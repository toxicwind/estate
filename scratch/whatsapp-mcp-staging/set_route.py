#!/usr/bin/env python3
"""Add /whatsapp-webhook to the tailscale funnel serve config via LocalAPI.

Reads the live config, backs it up, adds ONLY our handler, writes it back,
then verifies. Existing handlers are never touched.
"""
import http.client
import json
import socket
import sys

SOCK = "/var/run/tailscale/tailscaled.sock"
HOST_KEY = "github-mcp-host.tailc9ac71.ts.net:443"
BACKUP = "/home/toxic/whatsapp-mcp/serve-config.backup.json"


class UnixHTTP(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("localhost")
        self._path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self._path)


def api(method, url, body=None):
    c = UnixHTTP(SOCK)
    headers = {"Host": "local-tailscaled.sock"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    c.request(method, url, body=data, headers=headers)
    r = c.getresponse()
    return r.status, r.read()


def main():
    st, raw = api("GET", "/localapi/v0/serve-config")
    print(f"GET -> {st}, {len(raw)} bytes", flush=True)
    if st != 200 or not raw:
        print("GET failed, aborting", flush=True)
        return 1
    cfg = json.loads(raw)
    with open(BACKUP, "w") as f:
        json.dump(cfg, f, indent=2)
    handlers = cfg["Web"][HOST_KEY]["Handlers"]
    print("current handlers: " + str(sorted(handlers)), flush=True)

    handlers["/whatsapp-webhook"] = {"Proxy": "http://127.0.0.1:25146/webhook"}

    for method in ("POST", "PUT"):
        st, out = api(method, "/localapi/v0/serve-config", cfg)
        print(f"{method} -> {st} {out[:200]!r}", flush=True)
        if st in (200, 204):
            break
    else:
        print("both methods failed, aborting", flush=True)
        return 1

    st, raw = api("GET", "/localapi/v0/serve-config")
    cfg2 = json.loads(raw)
    h2 = sorted(cfg2["Web"][HOST_KEY]["Handlers"])
    print("handlers now: " + str(h2), flush=True)
    if "/whatsapp-webhook" not in h2:
        print("ROUTE NOT PRESENT", flush=True)
        return 1
    print("webhook -> " + cfg2["Web"][HOST_KEY]["Handlers"]["/whatsapp-webhook"]["Proxy"], flush=True)
    print("OK", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
