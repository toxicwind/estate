"""Remove the stale [daemons.ws-exec-tunnel] section (port 25379).

Evidence (oracle tunnel-audit-25379, 2026-09-21):
- nothing listens on :25379
- daemon NOT in pitchfork's registry (toml added 2026-09-20, never registered)
- funnel /exec-ws routes directly to :25204; nothing dials :25379
- verdict: STALE, candidate for removal
The forwarder script tools/ws-exec-tunnel.py is kept (harmless fallback).
"""
import shutil, datetime

ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

p = "/home/toxic/sovereign/pitchfork.toml"
shutil.copy(p, "/tmp/pitchfork.toml.bak-" + ts)
s = open(p).read()
start = s.find("# ws-exec-tunnel (2026-09-14)")
end = s.find("# squawk-ws-client (2026-09-14")
assert start > 0 and end > start, "anchors"
removed = s[start:end]
assert "[daemons.ws-exec-tunnel]" in removed, "section not in span"
s = s[:start] + s[end:]
open(p, "w").write(s)
print("removed %d chars from pitchfork.toml" % len(removed))

p2 = "/home/toxic/sovereign/config/ports.env"
shutil.copy(p2, "/tmp/ports.env.bak-" + ts)
lines = open(p2).read().splitlines(keepends=True)
n0 = len(lines)
lines = [l for l in lines if not l.startswith("WS_EXEC_TUNNEL_PORT=")]
assert len(lines) == n0 - 1, "ports.env line"
open(p2, "w").write("".join(lines))
print("removed WS_EXEC_TUNNEL_PORT from ports.env")

# validate toml still parses
try:
    import tomllib
    tomllib.load(open("/home/toxic/sovereign/pitchfork.toml", "rb"))
    print("toml parses OK")
except ImportError:
    import subprocess
    r = subprocess.run(["python3", "-c", "import tomllib; tomllib.load(open('/home/toxic/sovereign/pitchfork.toml','rb')); print('toml parses OK')"], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[:200])
