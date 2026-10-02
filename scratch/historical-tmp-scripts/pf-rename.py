import subprocess

# Start from HEAD's pitchfork.toml, apply ONLY approved hunks.
src = subprocess.run(
    ["git", "show", "HEAD:pitchfork.toml"],
    capture_output=True, text=True, cwd="/home/toxic/sovereign",
).stdout
lines = src.split("\n")
out = []
i = 0
changes = []

while i < len(lines):
    line = lines[i]

    # 1. openfang-front rename: [daemons.axiom] -> [daemons.openfang-front] + comment
    if line == "[daemons.axiom]":
        out.append("# (Renamed from \"axiom\" 2026-09-21: the old service spawned a DUPLICATE kernel")
        out.append("# on :25203 sharing the kernel SQLite DB. Now proxy-only; the kernel is")
        out.append("# daemons.openfang on :25196. See src/services/openfang.ts.)")
        out.append("[daemons.openfang-front]")
        changes.append("axiom->openfang-front")
        i += 1
        continue

    # 2. health_http for openfang-front (after depends=["shep"] in that block)
    if line == 'ready_http = "http://127.0.0.1:25103/api/health"' and i > 0 and 'depends = ["shep"]' in lines[i+1]:
        out.append(line)
        out.append(lines[i+1])  # depends
        out.append('health_http = { url = "http://127.0.0.1:25103/api/health", interval = "30s", timeout = "5s", retries = 3 }')
        changes.append("openfang-front health_http")
        i += 2
        continue

    # 3. health_http for openfang :25196 (after retry=true in openfang-run.sh block)
    if line == 'run = "exec /home/toxic/sovereign/ops/openfang-run.sh"':
        # copy until retry=true, then add health_http
        out.append(line)
        i += 1
        while i < len(lines) and lines[i].strip() != "retry = true":
            out.append(lines[i])
            i += 1
        if i < len(lines):
            out.append(lines[i])  # retry = true
            out.append('health_http = { url = "http://127.0.0.1:25196/api/health", interval = "30s", timeout = "5s", retries = 3 }')
            changes.append("openfang :25196 health_http")
            i += 1
        continue

    # 4 & 5. groups: axiom -> openfang-front (NOT adding mcp-gateway)
    if '"axiom"' in line and 'daemons = [' in line:
        out.append(line.replace('"axiom"', '"openfang-front"'))
        changes.append("group axiom->openfang-front")
        i += 1
        continue

    # 6. browserless rename
    if line == "[daemons.itvx-browserless]":
        out.append("[daemons.browserless]")
        changes.append("itvx-browserless->browserless")
        i += 1
        continue
    if line == 'run = "exec /home/toxic/.browserless/run.sh"':
        out.append('run = "exec /home/toxic/sovereign/projects/mesh/browserless/server/run.sh"')
        changes.append("browserless run path")
        i += 1
        continue
    if line == 'env = { BROWSERLESS_PORT = "25130" }':
        out.append('env = { BROWSERLESS_PORT = "25130", WAYLAND_DISPLAY = "wayland-1", XDG_RUNTIME_DIR = "/run/user/1000", BROWSERLESS_CONNECTION_TIMEOUT = "900000" }')
        changes.append("browserless env")
        i += 1
        continue

    out.append(line)
    i += 1

open("/home/toxic/sovereign/pitchfork.toml", "w").write("\n".join(out))
print("changes:", changes)
print("total:", len(changes))
