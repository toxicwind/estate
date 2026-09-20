#!/usr/bin/env python3
"""Add /squawk-feed/seq to the Tailscale funnel serve config (idempotent)."""
import http.client
import json
import sys

SOCK = "/var/run/tailscale/tailscaled.sock"
PATH = "/localapi/v0/serve-config"
HOST_KEY = "github-mcp-host.tailc9ac71.ts.net:443"
NEW_PATH = "/squawk-feed/seq"
BACKEND = "http://127.0.0.1:25135/squawk-feed/seq"


def api(method, body=None):
    conn = http.client.HTTPConnection("local-tailscaled.sock", timeout=15)
    conn.sock = None
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect(SOCK)
    conn.sock = s
    headers = {}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    conn.request(method, PATH, body=data, headers=headers)
    resp = conn.getresponse()
    out = resp.read().decode()
    conn.close()
    return resp.status, out


status, current = api("GET")
if status != 200:
    sys.exit("GET failed: %s %s" % (status, current))
cfg = json.loads(current)
handlers = cfg["Web"][HOST_KEY]["Handlers"]
if handlers.get(NEW_PATH, {}).get("Proxy") == BACKEND:
    print("already configured")
else:
    handlers[NEW_PATH] = {"Proxy": BACKEND}
    for method in ("POST", "PUT", "PATCH"):
        status, out = api(method, cfg)
        print("%s -> %s" % (method, status))
        if status == 200:
            break
    else:
        sys.exit("all methods failed: %s" % out[:200])
    print("serve config updated via %s" % method)

# verify
status, verify = api("GET")
vcfg = json.loads(verify)
print(json.dumps(vcfg["Web"][HOST_KEY]["Handlers"], indent=1))
