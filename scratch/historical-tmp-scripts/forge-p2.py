t = open('/home/toxic/sovereign/pitchfork.toml').read()
old_env = 'env = { WAYLAND_DISPLAY = "wayland-1", XDG_RUNTIME_DIR = "/run/user/1000" }'
new_env = 'env = { DISPLAY = ":99", XDG_RUNTIME_DIR = "/run/user/1000" }'
assert t.count(old_env) == 1
t = t.replace(old_env, new_env)
anchor = "\n[daemons.browser-keeper]\n"
assert t.count(anchor) == 1
new_daemons = """
[daemons.agent-display]
# Forge 2026-09-21: isolated virtual display for the agent browser.
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
port = 6080
run = "exec /home/toxic/.local/bin/websockify --web /home/toxic/.browserless/novnc 6080 127.0.0.1:5900"
dir = "."
mise = false
retry = true
ready_cmd = "curl -sf http://127.0.0.1:6080/vnc.html > /dev/null"
boot_start = true
auto = ["start"]
"""
t = t.replace(anchor, new_daemons + anchor)
open('/home/toxic/sovereign/pitchfork.toml','w').write(t)
print("pitchfork.toml updated cleanly")
