#!/usr/bin/env python3
"""files-medic: tailnet-only static file server behind the /files serve path.

tailscale serve maps /files -> http://127.0.0.1:34567 (tailnet only, no funnel).
This daemon is that backend. Supervised by pitchfork as daemons.files.
Serves FILES_ROOT (default /home/toxic/files). stdlib only.
"""
import http.server
import json
import os

ROOT = os.environ.get("FILES_ROOT", "/home/toxic/files")
PORT = int(os.environ.get("FILES_PORT", "34567"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path == "/health" or self.path.startswith("/health?"):
            body = json.dumps(
                {"ok": True, "service": "files", "root": ROOT, "port": PORT}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def log_message(self, *args):
        pass


def main():
    os.makedirs(ROOT, exist_ok=True)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.serve_forever()


if __name__ == "__main__":
    main()
