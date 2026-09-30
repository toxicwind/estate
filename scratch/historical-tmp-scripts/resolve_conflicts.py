#!/usr/bin/env python3
"""Resolve envhunt rebase conflicts: take HEAD's deletions, keep our fixes."""
import sys, tomllib

root = sys.argv[1].rstrip("/")

# pitchfork.toml: HEAD deleted the entire [daemons.ws-exec-tunnel] section
# (commit 6f797b4bb7, oracle tunnel-audit-25379 verdict STALE). Accept the
# deletion: drop everything between the conflict markers inclusive.
p = root + "/pitchfork.toml"
lines = open(p).read().split("\n")
start = next(i for i, l in enumerate(lines) if l == "<<<<<<< HEAD")
end = next(i for i, l in enumerate(lines) if l.startswith(">>>>>>> b3493bf856"))
assert start < end, "marker order wrong"
del lines[start:end + 1]
open(p, "w").write("\n".join(lines))

# ports.env: keep HEAD's restructure + EXEC_WS_PORT, apply our AWR comment fix.
p = root + "/config/ports.env"
t = open(p).read()
old_block = (
    "<<<<<<< HEAD\n"
    "# owner: server.py (.whatsapp-mcp-venv, pitchfork daemons.whatsapp-mcp)\n"
    "WHATSAPP_MCP_PORT=25146\n"
    "# owner: awrawr_mcp.py (systemd user unit awrawr-mcp.service; canonical: projects/bridge/yote/awrawr_mcp.py)\n"
    "AWR_MCP_PORT=25198\n"
    "# owner: awrawr_ws_exec.py (pitchfork daemons.awrawr-ws-exec; NEVER claim/kill)\n"
    "EXEC_WS_PORT=25204\n"
    "=======\n"
    "WHATSAPP_MCP_PORT=25146  # owner: server.py (.whatsapp-mcp-venv, pitchfork daemons.whatsapp-mcp)\n"
    "AWR_MCP_PORT=25198  # owner: awrawr_mcp.py (pitchfork daemons.awrawr-mcp; canonical: /home/toxic/awrawr_mcp.py)\n"
    ">>>>>>> b3493bf856 (envhunt: kill stupid env overrides before they make us flail)\n"
)
new_block = (
    "# owner: server.py (.whatsapp-mcp-venv, pitchfork daemons.whatsapp-mcp)\n"
    "WHATSAPP_MCP_PORT=25146\n"
    "# owner: awrawr_mcp.py (pitchfork daemons.awrawr-mcp; canonical: /home/toxic/awrawr_mcp.py)\n"
    "AWR_MCP_PORT=25198\n"
    "# owner: awrawr_ws_exec.py (pitchfork daemons.awrawr-ws-exec; NEVER claim/kill)\n"
    "EXEC_WS_PORT=25204\n"
)
assert t.count(old_block) == 1, "ports.env conflict block not found"
t = t.replace(old_block, new_block)
open(p, "w").write(t)

tomllib.load(open(root + "/pitchfork.toml", "rb"))
print("conflicts resolved, TOML OK")
