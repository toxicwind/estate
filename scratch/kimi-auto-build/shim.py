#!/usr/bin/env python3
"""kimi-auto sidecar shim.

Started by herd (llama-swap) as the `models.kimi-auto` cmd entry. It is a
minimal OpenAI-compatible server that:

  1. Reads the resolver's state file to find the current best Kimi model.
  2. Rewrites incoming `model: "kimi-auto"` requests to that model id.
  3. Forwards the request to herd and streams the response back.

This makes `kimi-auto` a real, resolvable model id on the herd surface.
Model selection lives in resolver.py; this shim only routes.

Usage (herd invokes it):
    python3 shim.py --port ${PORT} [--herd http://127.0.0.1:25100]
"""

import argparse
import http.client
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

DEFAULT_HERD = "http://127.0.0.1:25100"
DEFAULT_STATE = os.path.expanduser("~/.local/share/kimi-auto/state.json")
DEFAULT_FALLBACK = "kimi-k3"


def load_state(state_path, fallback):
    """Return (model_id, updated_at). Never raises; falls back cleanly."""
    try:
        with open(state_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        model = data.get("model")
        if isinstance(model, str) and model:
            return model, data.get("updated_at")
    except Exception as exc:  # missing/corrupt state -> fallback
        print(f"[kimi-auto] state load failed ({exc}); using fallback", flush=True)
    return fallback, None


class Handler(BaseHTTPRequestHandler):
    server_version = "kimi-auto-shim/1.0"

    def log_message(self, fmt, *args):  # quieter; herd captures stdout
        sys.stderr.write("[kimi-auto] " + fmt % args + "\n")

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health" or self.path.startswith("/health?"):
            model, updated = load_state(self.server.state_path, self.server.fallback)
            self._send_json(200, {"status": "ok", "model": model, "updated_at": updated})
        elif self.path == "/v1/models" or self.path.startswith("/v1/models?"):
            model, _ = load_state(self.server.state_path, self.server.fallback)
            self._send_json(200, {
                "object": "list",
                "data": [
                    {"id": "kimi-auto", "object": "model", "owned_by": "kimi-auto",
                     "metadata": {"resolves_to": model}},
                ],
            })
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._send_json(400, {"error": "invalid JSON body"})
            return

        target, updated = load_state(self.server.state_path, self.server.fallback)
        requested = payload.get("model")
        if requested in ("kimi-auto", None, ""):
            payload["model"] = target
        # else: pass through any explicit model id untouched

        body = json.dumps(payload).encode("utf-8")
        herd = urlparse(self.server.herd_url)

        try:
            conn = http.client.HTTPConnection(herd.hostname, herd.port or 80, timeout=120)
            fwd_headers = {"Content-Type": "application/json"}
            auth = self.headers.get("Authorization")
            if auth:
                fwd_headers["Authorization"] = auth
            conn.request("POST", "/v1/chat/completions", body=body, headers=fwd_headers)
            resp = conn.getresponse()
        except Exception as exc:
            self._send_json(503, {"error": f"herd unreachable: {exc}"})
            return

        # Stream the upstream response back verbatim (SSE-friendly).
        self.send_response(resp.status)
        ctype = resp.getheader("Content-Type") or "application/json"
        self.send_header("Content-Type", ctype)
        if "text/event-stream" in ctype:
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            try:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            data = resp.read()
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        conn.close()
        sys.stderr.write(
            f"[kimi-auto] {requested} -> {target} ({resp.status})\n"
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--herd", default=os.environ.get("KIMI_AUTO_HERD", DEFAULT_HERD))
    ap.add_argument("--state", default=os.environ.get("KIMI_AUTO_STATE", DEFAULT_STATE))
    ap.add_argument("--fallback-model", default=os.environ.get("KIMI_AUTO_FALLBACK", DEFAULT_FALLBACK))
    args = ap.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    server.herd_url = args.herd
    server.state_path = args.state
    server.fallback = args.fallback_model
    print(f"[kimi-auto] shim on 127.0.0.1:{args.port} -> herd {args.herd}", flush=True)
    print(f"[kimi-auto] state: {args.state} (fallback {args.fallback_model})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
