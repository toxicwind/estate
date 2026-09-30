#!/usr/bin/env python3
"""envhunt fixes: apply to a sovereign checkout root given as argv[1]."""
import re, sys

root = sys.argv[1].rstrip("/")
changed = []

def edit(path, old, new, count=1):
    with open(path) as f:
        t = f.read()
    n = t.count(old)
    assert n == count, f"{path}: pattern found {n}x (expected {count}): {old[:70]!r}"
    t = t.replace(old, new)
    with open(path, "w") as f:
        f.write(t)
    changed.append((path, old[:60]))

toml = root + "/pitchfork.toml"
t = open(toml).read()

# --- 1. keypool: ready probe was checking yote's :25102, not keypool's :25109 ---
# section-scoped: the same URL is legitimately used by [daemons.yote]
sec = re.search(r"\[daemons\.keypool\](.*?)(?=^\[daemons\.|\Z)", t, re.S | re.M)
assert sec, "keypool section not found"
span = sec.group(1)
old_probe = 'ready_http = "http://127.0.0.1:25102/health"'
assert span.count(old_probe) == 1, "keypool probe pattern not unique in section"
new_span = span.replace(old_probe, 'ready_http = "http://127.0.0.1:25109/health"')
t = t[:sec.start(1)] + new_span + t[sec.end(1):]
with open(toml, "w") as f:
    f.write(t)
changed.append((toml, old_probe[:60]))

# --- 2. tau-code: drop dead TAU_CODE_PORT env (code never reads it) ---
edit(toml, 'env = { TAU_CODE_PORT = "25145" }\n', '')

# --- 3. squawk-ws-client: drop token env (code default now correct) ---
edit(toml, 'env = { SQUAWK_WS_TOKEN_FILE = "/home/toxic/.squawk-ws-token" }\n', '')

# --- 4. forensics-srv: remove double-supervised section (systemd owns it) ---
old_forensics = '''[daemons.forensics-srv]
run = "exec /home/toxic/sovereign/forensics-srv/venv/bin/python /home/toxic/sovereign/forensics-srv/server.py"
dir = "/home/toxic/sovereign/forensics-srv"
mise = false
retry = true
boot_start = true
ready_cmd = "curl -sf http://127.0.0.1:25160/health >/dev/null"
auto = ["start"]
'''
new_forensics = '''# forensics-srv REMOVED 2026-09-21 (envhunt): double-supervised. The live
# process on :25160 is owned by the systemd user unit
# sovereign-forensics-srv.service (enabled, active, Restart=always; ppid chain
# verified -> systemd --user). Pitchfork's copy sat "stopped" but carried
# auto=["start"], so the next supervisor restart would wedge it on EADDRINUSE.
# Single owner = systemd. To migrate to pitchfork: stop+disable the unit,
# re-add this section, then `pitchfork start forensics-srv`.
'''
edit(toml, old_forensics, new_forensics)

# --- 5. ws-exec-tunnel: retire the stale 8379 narrative ---
old_tunnel = '''# ws-exec-tunnel (2026-09-14): TCP forwarder 127.0.0.1:25379 -> 127.0.0.1:8379.
# Chris's rule: 8379 is the ws-exec default - leave it in place, tunnel to it
# instead of moving it. Transparent to the WS protocol (handshake+frames pass
# through untouched). NOTE: running supervisor (2.16.0) has no reload mechanism
# and was not restarted (forbidden) - this section takes effect on the next
# supervisor start; the tunnel is currently supervised via `pitchfork run`.
'''
new_tunnel = '''# ws-exec-tunnel (2026-09-14): TCP forwarder 127.0.0.1:25379 -> 127.0.0.1:25204.
# Forwards to the WS lane's live port (code default 25204, 25xxx range per
# Chris 2026-09-21; the old "8379 is the default, tunnel to it" rule is
# retired). Transparent to the WS protocol (handshake+frames pass through
# untouched). NOTE: the supervisor snapshots daemon definitions at
# registration - after editing, re-register via bin/pitchfork-restart.
'''
edit(toml, old_tunnel, new_tunnel)

# --- 6. ports.env: AWR_MCP_PORT comment references retired systemd unit ---
penv = root + "/config/ports.env"
old_c = "AWR_MCP_PORT=25198  # owner: awrawr_mcp.py (systemd user unit awrawr-mcp.service; canonical: projects/bridge/yote/awrawr_mcp.py)"
new_c = "AWR_MCP_PORT=25198  # owner: awrawr_mcp.py (pitchfork daemons.awrawr-mcp; canonical: /home/toxic/awrawr_mcp.py)"
edit(penv, old_c, new_c)

# --- 7. squawk-ws-client: token default -> the live token file ---
client = root + "/projects/mesh/squawk-ws/squawk_ws_client_local.py"
edit(client,
     'TOKEN_FILE = os.environ.get("SQUAWK_WS_TOKEN_FILE", "/home/toxic/squawk-ws/token")',
     'TOKEN_FILE = os.environ.get("SQUAWK_WS_TOKEN_FILE", "/home/toxic/.squawk-ws-token")')

# --- 8. tau-code: honest code default 25145 (was stale 4700) ---
srv = root + "/tau/engine/packages/metaharness/src/server.ts"
edit(srv, "\tlet port = 4700;", "\tlet port = 25145;")

print(f"OK: {len(changed)} edits applied to {root}")
for p, s in changed:
    print(" -", p.split(root)[1], "::", s)
