#!/usr/bin/env python3
# apply_readme.py — doc hygiene for the interactive-viewer lane. Idempotent.
import os

KEEPER = "/home/toxic/sovereign/projects/mesh/browserless/keeper"
README = os.path.join(KEEPER, "README.md")
FRAG = os.path.join(KEEPER, "pitchfork.fragment.toml")
VIEWER = "/home/toxic/sovereign/projects/mesh/browserless/viewer"

# 1. Remove superseded .bak files (untracked; pre-isolation versions live in git history).
for bak in ("keeper.sh.bak-20260921", "keeper.js.bak-20260921"):
    p = os.path.join(KEEPER, bak)
    if os.path.exists(p):
        os.remove(p)
        print("removed", bak)
    else:
        print("already gone:", bak)

# 2. README: fix stale lines.
c = open(README).read()

old_sh = "`keeper.sh` - pitchfork launcher (sets Wayland env, execs keeper.js)."
new_sh = ("`keeper.sh` - pitchfork launcher for the isolated display: unsets "
          "`WAYLAND_DISPLAY`, sets `DISPLAY=:99`, execs keeper.js "
          "(Forge 2026-09-21 — the keeper never renders in Chris's Hyprland session).")
assert old_sh in c
c = c.replace(old_sh, new_sh)

old_toggle = """- `browser-toggle.sh` - show/hide the keeper window via the Hyprland
  scratchpad (`special:browser`). Wired to the Quickshell bar button; also
  runnable by hand."""
new_toggle = """- `browser-toggle.sh` - LEGACY: showed/hid the keeper window via the Hyprland
  scratchpad. Dead since the keeper moved to the isolated Xvnc :99 display
  (no Hyprland window exists any more); kept for reference."""
assert old_toggle in c
c = c.replace(old_toggle, new_toggle)

viewer_section = """
## Agent display + interactive viewer (Forge 2026-09-21)

The keeper Chromium renders on an **isolated virtual display** — never in
Chris's Hyprland session. (Root cause of the 2026-09-21 takeover: keeper.sh
exported `WAYLAND_DISPLAY=wayland-1`, so agent windows stole his mouse and
focus.)

- `agent-display` — `Xvnc :99`, RFB on `127.0.0.1:5900` only (`-localhost`),
  VNC password auth via `/home/toxic/.browserless/vncpasswd` (0600, Chris's —
  never rotated, never stored anywhere else).
- `agent-viewer` — websockify serving stock noVNC on **`127.0.0.1:6080`
  (loopback-only)**. The viewer is **INTERACTIVE**: noVNC defaults
  `view_only=false` (verified in vendored `app/ui.js`; `mandatory.json` and
  `defaults.json` are empty), so Chris can click, type, and take over the
  agent browser. View-only was explicitly rejected (Chris 2026-09-21:
  "view only is no point, user should be able to interact or help lol").
- `agent-viewer-gate` (`../viewer/agent-viewer-gate.py`) — token-gated front
  door on `127.0.0.1:6081`. Requires `?token=<viewer-token>` (or the `aview`
  cookie a successful check issues), then transparently proxies HTTP and
  websocket upgrades to `:6080`. Token: `/home/toxic/.browserless/viewer-token`
  (0600, generated once). `/healthz` answers 200 with no token for the
  pitchfork readiness probe.
- External route: tailscale funnel `/agent-browser` -> `127.0.0.1:6081`
  (declared in `projects/yote/ops/funnel-map.sh`). The public URL is useless
  without the token — 403 on the page and on the websocket handshake alike.
  noVNC resolves its `./websockify` WS path relative to the page URL, so the
  subpath mount just works.
- VNC auth is untouched: past the gate, noVNC still prompts for the Xvnc
  password.

Viewer URL: `https://github-mcp-host.tailc9ac71.ts.net/agent-browser/vnc.html?token=<viewer-token>`

Restart/rollback: `pitchfork-restart agent-viewer --reregister` (picks up
`pitchfork.toml` run-line changes), `pitchfork start agent-viewer-gate`.
To close the external route without touching the daemons:
`tailscale funnel --bg --set-path /agent-browser` off — i.e. remove the
`/agent-browser` line from `funnel-map.sh` and run
`tailscale serve --bg --remove /agent-browser` as root.
"""
if "## Agent display + interactive viewer" not in c:
    c = c.rstrip("\n") + "\n" + viewer_section
    print("README: viewer section added")
else:
    print("README: viewer section already present")
open(README, "w").write(c)

# 3. Fragment: rewrite as an accurate record of the live toml entries.
frag = """# Pitchfork daemon record — browser lane (Forge 2026-09-21).
# Already merged into /home/toxic/sovereign/pitchfork.toml; this file is the
# committed record, not a merge source. Owned restart from /home/toxic/sovereign:
#   ./bin/pitchfork-restart <agent-display|agent-viewer> --reregister
#   pitchfork start agent-viewer-gate   (new daemons)

[daemons.agent-display]
# Isolated virtual display for the agent browser.
port = 5900
run = "exec Xvnc :99 -geometry 1600x900 -depth 24 -rfbport 5900 -localhost -SecurityTypes VncAuth -rfbauth /home/toxic/.browserless/vncpasswd"
dir = "."
mise = false
retry = true
ready_cmd = "ss -tln | grep -q 127.0.0.1:5900"
boot_start = true
auto = ["start"]

[daemons.agent-viewer]
# noVNC web viewer. INTERACTIVE (Chris 2026-09-21); loopback-only.
# External access goes through agent-viewer-gate below.
port = 6080
run = "exec /home/toxic/.local/bin/websockify --web /home/toxic/.browserless/novnc 127.0.0.1:6080 127.0.0.1:5900"
dir = "."
mise = false
retry = true
ready_cmd = "curl -sf http://127.0.0.1:6080/vnc.html > /dev/null"
boot_start = true
auto = ["start"]

[daemons.agent-viewer-gate]
# Token-gated front door for the viewer; funnel mounts :6081 at /agent-browser.
port = 6081
run = "exec python3 /home/toxic/sovereign/projects/mesh/browserless/viewer/agent-viewer-gate.py"
dir = "."
mise = false
retry = true
ready_cmd = "curl -sf http://127.0.0.1:6081/healthz > /dev/null"
boot_start = true
auto = ["start"]

[daemons.browser-keeper]
port = 9223
run = "exec /home/toxic/sovereign/projects/mesh/browserless/keeper/keeper.sh"
dir = "."
mise = false
retry = true
ready_cmd = "curl -sf http://127.0.0.1:9223/json/version > /dev/null"
boot_start = true
env = { DISPLAY = ":99", XDG_RUNTIME_DIR = "/run/user/1000" }
auto = ["start"]
"""
open(FRAG, "w").write(frag)
print("fragment rewritten")

# 4. Tiny viewer README.
vr = os.path.join(VIEWER, "README.md")
if not os.path.exists(vr):
    open(vr, "w").write(
        "# agent-viewer-gate\n\nToken-gated front door for the noVNC agent viewer "
        "(`:6080`, loopback-only, interactive).\n\n"
        "- Listens `127.0.0.1:6081`, requires `?token=` "
        "(`/home/toxic/.browserless/viewer-token`, 0600) or the `aview` cookie,\n"
        "  then proxies HTTP + websocket upgrades to websockify on `:6080`.\n"
        "- Funnel mounts this at `/agent-browser` "
        "(see `projects/yote/ops/funnel-map.sh`).\n"
        "- `/healthz` → 200, no token (pitchfork `ready_cmd`).\n"
        "- The VNC password itself is never handled here — noVNC still prompts for it.\n\n"
        "Full lane docs: `../keeper/README.md` → "
        "\"Agent display + interactive viewer\".\n"
    )
    print("viewer README written")
print("done")
