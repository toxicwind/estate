import re
p = "/home/toxic/sovereign/pitchfork.toml"
t = open(p).read()

# 1. Update browser-keeper env: Wayland -> Xvnc :99
old_env = 'env = { WAYLAND_DISPLAY = "wayland-1", XDG_RUNTIME_DIR = "/run/user/1000" }'
new_env = 'env = { DISPLAY = ":99", XDG_RUNTIME_DIR = "/run/user/1000" }'
assert old_env in t, "browser-keeper env not found"
t = t.replace(old_env, new_env)

# 2. Insert agent-display + agent-viewer daemons before browser-keeper section
anchor = "[daemons.browser-keeper]"
new_daemons = """[daemons.agent-display]
# Forge 2026-09-21: isolated virtual display for the agent browser.
# Xvnc :99, RFB localhost-only with VncAuth. The keeper's Chromium renders
# here instead of Chris's Hyprland session (no more mouse takeovers).
port = 5900
run = "exec Xvnc :99 -geometry 1600x900 -depth 24 -rfbport 5900 -localhost -SecurityTypes VncAuth -rfbauth /home/toxic/.browserless/vncpasswd"
dir = "."
mise = false
retry = true
ready_cmd = "ss -tln | grep -q 127.0.0.1:5900"
boot_start = true
auto = ["start"]

[daemons.agent-viewer]
# Forge 2026-09-21: noVNC web viewer for the agent display.
# websockify bridges :6080 (HTTP) -> 127.0.0.1:5900 (RFB).
# View-only: Chris watches via ?view_only=1 so his mouse never fights the agent.
port = 6080
run = "exec /home/toxic/.local/bin/websockify --web /home/toxic/.browserless/novnc 6080 127.0.0.1:5900"
dir = "."
mise = false
retry = true
ready_cmd = "curl -sf http://127.0.0.1:6080/vnc.html > /dev/null"
boot_start = true
auto = ["start"]

"""
assert anchor in t
t = t.replace(anchor, new_daemons + anchor)
open(p, "w").write(t)
print("pitchfork.toml updated")
