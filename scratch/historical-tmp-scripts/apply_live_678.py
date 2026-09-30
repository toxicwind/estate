#!/usr/bin/env python3
"""envhunt live-tree remaining fixes (6,7,8): ports.env comment, squawk client, tau-code."""
import sys

root = sys.argv[1].rstrip("/")
changed = []

def edit(path, old, new, count=1):
    with open(path) as f:
        t = f.read()
    n = t.count(old)
    assert n == count, f"{path}: found {n}x (expected {count}): {old[:70]!r}"
    open(path, "w").write(t.replace(old, new))
    changed.append(path)

# 6. ports.env: AWR_MCP_PORT comment references retired systemd unit
penv = root + "/config/ports.env"
edit(penv,
     "AWR_MCP_PORT=25198  # owner: awrawr_mcp.py (systemd user unit awrawr-mcp.service; canonical: projects/bridge/yote/awrawr_mcp.py)",
     "AWR_MCP_PORT=25198  # owner: awrawr_mcp.py (pitchfork daemons.awrawr-mcp; canonical: /home/toxic/awrawr_mcp.py)")

# 7. squawk-ws-client: token default -> the live token file
client = root + "/projects/mesh/squawk-ws/squawk_ws_client_local.py"
edit(client,
     'TOKEN_FILE = os.environ.get("SQUAWK_WS_TOKEN_FILE", "/home/toxic/squawk-ws/token")',
     'TOKEN_FILE = os.environ.get("SQUAWK_WS_TOKEN_FILE", "/home/toxic/.squawk-ws-token")')

# 8. tau-code: honest code default 25145 (was stale 4700)
srv = root + "/tau/engine/packages/metaharness/src/server.ts"
edit(srv, "\tlet port = 4700;", "\tlet port = 25145;")

print(f"OK: {len(changed)} edits applied to {root}")
for p in changed:
    print(" -", p)
