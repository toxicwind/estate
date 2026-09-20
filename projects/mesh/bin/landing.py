#!/usr/bin/env python3
"""Mesh landing page: public homepage for the sovereign funnel.

Serves on 127.0.0.1:8443 (funnel `/` -> here). Shows live status of every
funnel route by probing the localhost backends. stdlib only.
"""
import concurrent.futures
import html
import json
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8443

# (display name, probe url, public funnel path or None for tailnet-only)
BACKENDS = [
    ("awrawr MCP", "http://127.0.0.1:8377/mcp", "/mcp"),
    ("exec bridge (ws)", "http://127.0.0.1:8379/exec-ws", "/exec-ws"),
    ("gemini MCP", "http://127.0.0.1:8378/mcp", "/gemini-mcp"),
    ("squawk WS", "http://127.0.0.1:25147/squawk-ws", "/squawk-ws"),
    ("squawk feed", "http://127.0.0.1:25135/squawk-feed/seq", "/squawk-feed/seq"),
    ("whatsapp webhook", "http://127.0.0.1:25146/webhook", "/whatsapp-webhook"),
    ("shep MCP", "http://127.0.0.1:25127/mcp", "/mesh-mcp"),
    ("shep health", "http://127.0.0.1:25127/health", "/mesh-health"),
    ("shep metrics", "http://127.0.0.1:25127/metrics", "/mesh-metrics"),
    ("files", "http://127.0.0.1:34567/", None),
]

_status_cache = {"at": 0.0, "rows": []}
CACHE_TTL = 10.0


def probe(name, url):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            code = r.status
        ms = int((time.time() - t0) * 1000)
        # Any HTTP response (even 401/404/426) means the backend is alive.
        return (name, url, True, code, ms)
    except Exception as e:  # noqa: BLE001 - probe must never raise
        ms = int((time.time() - t0) * 1000)
        # HTTPError carries a status code -> backend IS alive.
        code = getattr(e, "code", None)
        if code is not None:
            return (name, url, True, code, ms)
        return (name, url, False, 0, ms)


def get_status():
    now = time.time()
    if now - _status_cache["at"] < CACHE_TTL and _status_cache["rows"]:
        return _status_cache["rows"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(BACKENDS)) as ex:
        rows = list(ex.map(lambda b: probe(b[0], b[1]), BACKENDS))
    _status_cache.update(at=now, rows=rows)
    return rows


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>sovereign mesh</title><meta http-equiv="refresh" content="30">
<style>
body{{background:#0d1117;color:#c9d1d9;font-family:system-ui,sans-serif;max-width:760px;margin:2em auto;padding:0 1em}}
h1{{font-size:1.4em}}table{{width:100%;border-collapse:collapse;margin-top:1em}}
td,th{{padding:.45em .6em;border-bottom:1px solid #21262d;text-align:left;font-size:.9em}}
.dot{{display:inline-block;width:.7em;height:.7em;border-radius:50%;margin-right:.5em}}
.up{{background:#3fb950}}.down{{background:#f85149}}
a{{color:#58a6ff}}.muted{{color:#8b949e;font-size:.8em}}
</style></head><body>
<h1>&#x1f432; sovereign mesh</h1>
<p class="muted">funnel gateway status &mdash; auto-refreshes every 30s</p>
<table><tr><th></th><th>service</th><th>backend</th><th>code</th><th>latency</th><th>public</th></tr>
{rows}
</table><p class="muted">tailnet-only routes are reachable inside the tailnet, not via funnel.</p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, json.dumps({"status": "ok"}), "application/json")
            return
        if self.path == "/api/status":
            rows = get_status()
            self._send(200, json.dumps([
                {"name": n, "alive": a, "code": c, "ms": m} for n, _, a, c, m in rows
            ]), "application/json")
            return
        if self.path != "/":
            self._send(404, "not found", "text/plain")
            return
        rows = get_status()
        pub = {b[0]: b[2] for b in BACKENDS}
        trs = []
        for name, _, alive, code, ms in rows:
            dot = "up" if alive else "down"
            path = pub.get(name)
            link = f'<a href="{html.escape(path)}">{html.escape(path)}</a>' if path else '<span class="muted">tailnet</span>'
            trs.append(
                f'<tr><td><span class="dot {dot}"></span></td>'
                f"<td>{html.escape(name)}</td><td>{'alive' if alive else 'DOWN'}</td>"
                f"<td>{code or '&mdash;'}</td><td>{ms} ms</td><td>{link}</td></tr>"
            )
        self._send(200, PAGE.format(rows="\n".join(trs)))


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"landing on 127.0.0.1:{PORT}", flush=True)
    srv.serve_forever()
