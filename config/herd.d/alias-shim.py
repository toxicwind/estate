#!/usr/bin/env python3
"""alias-shim: fixed-target alias forwarder for herd.

Started by herd (llama-swap) as a models.<alias> cmd entry:
    python3 alias-shim.py --port ${PORT} --target <peer-model-id> [--standby <peer-model-id>] [--name <alias>]

Rewrites incoming `model: "<alias>"` to the fixed target and forwards to
herd, streaming the response back. The target (and optional standby) are
fixed at config time -- the ROUTER CONFIG owns model selection; this shim
never selects, ranks, probes, or prefers any model family. If the target is
down the caller gets the upstream error verbatim (fail loudly, never
silently substitute).

Optional one-shot standby failover (HFT telecom pattern): when the primary
target errors (connection failure or HTTP 5xx) the shim tries the
config-provided --standby exactly once, then surfaces whatever comes back.
Never a retry spin. 4xx (auth/billing/not-found) is NOT a failover trigger:
a 402/401/404 surfaces verbatim so misconfiguration stays visible.

Transport behavior preserved from the kimi-auto shim it replaces:
curl-like header layout (Pollinations bot-filter workaround), browser
User-Agent, Authorization passthrough, verbatim SSE streaming, fail-fast
8s herd connect ceiling, self-loop rejection (508).

Health is honest: /health reports the configured target/standby; request
failures surface as the upstream status, never a masked 200.

Router-config ownership: to change what an alias serves, edit the --target
/ --standby flags in the herd config (config/herd.yaml or the --config-dir
fragment). No code changes, no timers, no probes.

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
ap.add_argument("--target", required=True,
                help="primary model id -- set in ROUTER CONFIG (herd.yaml / config-dir fragment)")
ap.add_argument("--standby", default=None,
                help="optional one-shot failover model id -- set in ROUTER CONFIG")
ap.add_argument("--name", default=None,
                help="alias name advertised on /v1/models (optional)")
ap.add_argument("--herd", default="http://127.0.0.1:25100")
args = ap.parse_args()
HERD = urlparse(args.herd)

# Browser UA for all herd traffic (Pollinations bot-filter workaround,
# verified 2026-09-14). Transport detail, not model selection.
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "Chrome/126.0 Safari/537.36")

LOOP_MSG = "alias loop: requested model is the alias target itself"


class Handler(BaseHTTPRequestHandler):
    server_version = "alias-shim/2.0"

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
            self._send_json(200, {
                "status": "ok",
                "target": args.target,
                "standby": args.standby,
                "alias": args.name,
                "selection": "router-config",
            })
        elif self.path == "/v1/models" or self.path.startswith("/v1/models?"):
            data = []
            if args.name:
                data.append({
                    "id": args.name, "object": "model", "owned_by": "alias-shim",
                    "metadata": {"alias_of": args.target,
                                 "standby_of": args.standby,
                                 "selection": "router-config"},
                })
            self._send_json(200, {"object": "list", "data": data})
        else:
            self._send_json(404, {"error": "not found"})

    def _forward(self, model_id, payload, auth):
        """Forward one attempt to herd with model_id. Returns (conn, resp) or (None, None, err)."""
        body = json.dumps(payload).encode("utf-8")
        try:
            # Fail fast (HFT): herd is localhost -- a connect that takes
            # >8s means herd is dead; surface 502 immediately.
            conn = http.client.HTTPConnection(HERD.hostname, HERD.port or 80, timeout=8)
            conn.putrequest("POST", "/v1/chat/completions")
            conn.putheader("Accept", "*/*")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("User-Agent", BROWSER_UA)
            if auth:
                conn.putheader("Authorization", auth)
            conn.putheader("Content-Length", str(len(body)))
            conn.endheaders()
            conn.send(body)
            return conn, conn.getresponse(), None
        except Exception as exc:
            return None, None, "herd unreachable: %s" % exc

    def _stream_back(self, resp, conn):
        self.send_response(resp.status)
        ctype = resp.getheader("Content-Type", "application/json")
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
        requested = payload.get("model")
        if requested in (None, ""):
            self._send_json(400, {"error": "missing model"})
            return
        if requested == args.target or (args.standby and requested == args.standby):
            # Self-reference guard: the alias must never route into itself.
            self._send_json(508, {"error": LOOP_MSG})
            return
        # Fixed-target rewrite: the alias IS its target. No selection here.
        payload["model"] = args.target
        auth = self.headers.get("Authorization")

        conn, resp, err = self._forward(args.target, payload, auth)
        served = args.target

        # One-shot standby failover (config-driven): primary transport
        # failure or 5xx -> try --standby once. Never a retry spin; 4xx
        # surfaces verbatim.
        if (resp is None or resp.status >= 500) and args.standby and args.standby != args.target:
            why = err or ("herd HTTP %d" % resp.status)
            if resp is not None:
                try:
                    resp.read()
                except Exception:
                    pass
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            sys.stderr.write("[alias-shim:%s] primary failed (%s); one-shot failover to standby %s\n"
                             % (args.target, why, args.standby))
            payload["model"] = args.standby
            conn, resp, err = self._forward(args.standby, payload, auth)
            served = "%s -> standby %s" % (args.target, args.standby)

        if resp is None:
            self._send_json(502, {"error": err or "herd unreachable"})
            return
        self._stream_back(resp, conn)
        sys.stderr.write("[alias-shim:%s] %s -> %s (%s)\n"
                         % (args.target, requested, served, resp.status))


if __name__ == "__main__":
    sys.stderr.write("[alias-shim] target=%s standby=%s alias=%s -> herd %s (selection: router-config)\n"
                     % (args.target, args.standby, args.name, args.herd))
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
