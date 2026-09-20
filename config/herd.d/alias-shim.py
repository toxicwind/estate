#!/usr/bin/env python3
"""alias-shim: fixed-target alias forwarder for herd.

Started by herd (llama-swap) as a models.<alias> cmd entry:
    python3 alias-shim.py --port ${PORT} --target <peer-model-id>

Rewrites incoming `model: "<alias>"` to the fixed target and forwards to
herd, streaming the response back. The target is fixed at config time --
there is no fallback and no substitution, ever. If the target is down the
caller gets the upstream error verbatim.

Usage (herd invokes it; never run by hand with a different target).
"""
import argparse
import http.client
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--target", required=True)
ap.add_argument("--herd", default="http://127.0.0.1:25100")
args = ap.parse_args()
ALIAS = args.target  # placeholder, replaced below
HERD = urlparse(args.herd)


class Handler(BaseHTTPRequestHandler):
    server_version = "alias-shim/1.0"

    def log_message(self, fmt, *a):
        sys.stderr.write("[alias-shim:%s] " % args.target + fmt % a + "\n")

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health" or self.path.startswith("/health?"):
            self._send_json(200, {"status": "ok", "target": args.target})
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
        if payload.get("model") in (None, ""):
            self._send_json(400, {"error": "missing model"})
            return
        if payload["model"] == args.target:
            self._send_json(508, {"error": "alias loop: target is the alias itself"})
            return
        payload["model"] = args.target
        body = json.dumps(payload).encode("utf-8")
        auth = self.headers.get("Authorization")
        try:
            conn = http.client.HTTPConnection(HERD.hostname, HERD.port or 80, timeout=8)
            conn.putrequest("POST", "/v1/chat/completions")
            conn.putheader("Accept", "*/*")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36")
            if auth:
                conn.putheader("Authorization", auth)
            conn.putheader("Content-Length", str(len(body)))
            conn.endheaders()
            conn.send(body)
            resp = conn.getresponse()
        except Exception as exc:
            self._send_json(502, {"error": "herd unreachable: %s" % exc})
            return
        self.send_response(resp.status)
        ctype = resp.getheader("Content-Type", "application/json")
        self.send_header("Content-Type", ctype)
        if ctype.startswith("text/event-stream"):
            self.end_headers()
            try:
                while True:
                    chunk = resp.read(65536)
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


ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
