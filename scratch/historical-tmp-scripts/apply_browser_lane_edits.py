#!/usr/bin/env python3
# apply_browser_lane_edits.py — idempotent edits for the noVNC interactive lane.
# Forge 2026-09-21. Run on yote as toxic.
import sys

TOML = "/home/toxic/sovereign/pitchfork.toml"
FUNNEL = "/home/toxic/sovereign/projects/yote/ops/funnel-map.sh"
ROUTER = "/home/toxic/sovereign/projects/mesh/browserless/browser-router.sh"

changed = []


def edit(path, fn):
    with open(path) as f:
        content = f.read()
    new = fn(content)
    if new != content:
        with open(path, "w") as f:
            f.write(new)
        changed.append(path)
    return new != content


# 1. websockify -> loopback-only :6080
old_run = 'run = "exec /home/toxic/.local/bin/websockify --web /home/toxic/.browserless/novnc 6080 127.0.0.1:5900"'
new_run = 'run = "exec /home/toxic/.local/bin/websockify --web /home/toxic/.browserless/novnc 127.0.0.1:6080 127.0.0.1:5900"'


def toml_edit(c):
    if old_run in c:
        c = c.replace(old_run, new_run)
    gate_block = '''[daemons.agent-viewer-gate]
# Forge 2026-09-21: token-gated front door for the noVNC agent viewer.
# Requires ?token=<viewer-token> (or the aview cookie it issues), then
# proxies to websockify :6080. Funnel mounts this at /agent-browser.
# The viewer is INTERACTIVE (Chris 2026-09-21: "user should be able to
# interact or help"); :6080 itself stays loopback-only.
port = 6081
run = "exec python3 /home/toxic/sovereign/projects/mesh/browserless/viewer/agent-viewer-gate.py"
dir = "."
mise = false
retry = true
ready_cmd = "curl -sf http://127.0.0.1:6081/healthz > /dev/null"
boot_start = true
auto = ["start"]

'''
    if "[daemons.agent-viewer-gate]" not in c:
        anchor = "[daemons.browser-keeper]"
        assert anchor in c, "browser-keeper anchor missing"
        c = c.replace(anchor, gate_block + anchor)
    return c


edit(TOML, toml_edit)


# 2. funnel map: /agent-browser -> gate
def funnel_edit(c):
    if "/agent-browser" in c:
        return c
    lines = c.split("\n")
    map_start = next(i for i, l in enumerate(lines) if l.strip() == "MAP=(")
    close = next(i for i in range(map_start, len(lines)) if lines[i].strip() == ")")
    lines.insert(close, '"/agent-browser\t\thttp://127.0.0.1:6081"')
    return "\n".join(lines)


edit(FUNNEL, funnel_edit)


# 3. router comment: view-only -> interactive
def router_edit(c):
    c = c.replace(
        "#             :6080 view-only), CDP 127.0.0.1:9223, profile nv-audit.",
        "#             :6080 INTERACTIVE on loopback (external: token-gated\n"
        "#             funnel /agent-browser -> gate :6081), CDP 127.0.0.1:9223,\n"
        "#             profile nv-audit.",
    )
    return c


edit(ROUTER, router_edit)

print("changed:", changed if changed else "none (already applied)")
