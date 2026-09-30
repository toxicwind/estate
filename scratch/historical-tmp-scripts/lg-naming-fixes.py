#!/usr/bin/env python3
"""Apply config-naming maximal fixes to /tmp/lg-wt (idempotent).

Fixes (all evidence-backed, 2026-09-21):
 1. config/ports.env: drop dead EXEC_WS_PORT (unreferenced anywhere incl.
    live fallback copy); add daemon-local WS_EXEC_PORT / TUNNEL_LISTEN_PORT /
    TUNNEL_TARGET_PORT to the numeric SSOT with daemon-local comments.
 2. bridge/awrawr_ws_exec.py + tools/ws-exec-tunnel.py: stale "8379"
    defaults/docstrings -> 25204 (ground truth: ss + tailscale serve status;
    :8379 has no listener).
 3. pitchfork.toml: stale funnel comment :8379 -> :25204; explicit
    TUNNEL_LISTEN_PORT="25379" in ws-exec-tunnel env (was implicit default);
    SSOT comments on literal --port run lines (tau-code, kimi-code, redis).
"""
import io
import re
import sys

WT = "/tmp/lg-wt"
changed = []


def patch(path, old, new, count=1):
    p = WT + "/" + path
    s = io.open(p, encoding="utf-8").read()
    if new in s and old not in s:
        return  # already applied
    assert old in s, "MISSING in %s: %r" % (path, old[:60])
    s = s.replace(old, new, count)
    io.open(p, "w", encoding="utf-8").write(s)
    changed.append("%s: %r -> ..." % (path, old[:50]))


# --- 1. ports.env -----------------------------------------------------------
p = WT + "/config/ports.env"
s = io.open(p, encoding="utf-8").read()
dead = "EXEC_WS_PORT=25204  # owner: awrawr_ws_exec.py (pitchfork daemons.awrawr-ws-exec; NEVER claim/kill)\n"
assert dead in s, "EXEC_WS_PORT line not found"
s = s.replace(dead, "", 1)
addition = (
    "\n# --- daemon-local port names (set in pitchfork.toml [daemons.*] env tables) ---\n"
    "# These bypass ${} expansion in run lines (proved unreliable 2026-09-20:\n"
    "# toolcall-llm ${TOOLCALL_PORT} expanded empty -> llama-server stoi crash).\n"
    "# They are listed here so the numeric SSOT still sees every port in use.\n"
    "WS_EXEC_PORT=25204  # daemon-local; [daemons.awrawr-ws-exec] env; consumed by bridge/awrawr_ws_exec.py\n"
    "TUNNEL_LISTEN_PORT=25379  # daemon-local; [daemons.ws-exec-tunnel] env; consumed by tools/ws-exec-tunnel.py\n"
    "TUNNEL_TARGET_PORT=25204  # daemon-local; [daemons.ws-exec-tunnel] env; target = the ws-exec listener\n"
)
if "WS_EXEC_PORT=25204" not in s:
    s = s.rstrip("\n") + "\n" + addition
io.open(p, "w", encoding="utf-8").write(s)
changed.append("config/ports.env: dropped dead EXEC_WS_PORT, added 3 daemon-local vars")

# --- 2. stale 8379 defaults ---------------------------------------------------
patch("bridge/awrawr_ws_exec.py",
      'PORT = int(os.environ.get("WS_EXEC_PORT", "8379"))',
      'PORT = int(os.environ.get("WS_EXEC_PORT", "25204"))')
patch("bridge/awrawr_ws_exec.py",
      "1. Tailscale funnel: TLS, outbound-only (route /exec-ws -> 127.0.0.1:8379).",
      "1. Tailscale funnel: TLS, outbound-only (route /exec-ws -> 127.0.0.1:25204).")
patch("tools/ws-exec-tunnel.py",
      'TARGET_PORT = int(os.environ.get("TUNNEL_TARGET_PORT", "8379"))',
      'TARGET_PORT = int(os.environ.get("TUNNEL_TARGET_PORT", "25204"))')
patch("tools/ws-exec-tunnel.py",
      "Listens on 127.0.0.1:25379, forwards every byte both ways to 127.0.0.1:8379.",
      "Listens on 127.0.0.1:25379, forwards every byte both ways to 127.0.0.1:25204.")

# --- 3. pitchfork.toml ---------------------------------------------------------
patch("pitchfork.toml",
      "policy and audit as the HTTPS bridge (awrawr_mcp.py). Funnel: /exec-ws -> :8379.",
      "policy and audit as the HTTPS bridge (awrawr_mcp.py). Funnel: /exec-ws -> :25204.")
patch("pitchfork.toml",
      'env = { TUNNEL_TARGET_PORT = "25204" }',
      'env = { TUNNEL_LISTEN_PORT = "25379", TUNNEL_TARGET_PORT = "25204" }')
# SSOT comments on literal run-line ports (literals stay: ${} unreliable)
patch("pitchfork.toml",
      'run = "exec bun run src/server.ts --port 25145"',
      'run = "exec bun run src/server.ts --port 25145" # 25145 == $TAU_CODE_PORT (SSOT); literal: ${} not expanded in run lines')
patch("pitchfork.toml",
      'claim-port 25126 /home/toxic/projects/sovereign-projects/tau/vendors/kimi-code/apps/kimi-code/dist/main.mjs web --no-open --port 25126 --no-port-walk"',
      'claim-port 25126 /home/toxic/projects/sovereign-projects/tau/vendors/kimi-code/apps/kimi-code/dist/main.mjs web --no-open --port 25126 --no-port-walk" # 25126 == $KIMI_CODE_PORT (SSOT); literal: ${} not expanded in run lines')
patch("pitchfork.toml",
      'run = "exec valkey-server --port 25199 --bind 0.0.0.0 --protected-mode no --save \'\' --appendonly no"',
      'run = "exec valkey-server --port 25199 --bind 0.0.0.0 --protected-mode no --save \'\' --appendonly no" # 25199 == $REDIS_PORT (SSOT); literal: ${} not expanded in run lines')

print("applied %d fixes:" % len(changed))
for c in changed:
    print(" -", c)
