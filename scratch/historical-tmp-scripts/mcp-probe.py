import json, subprocess, sys

proc = subprocess.Popen(
    ["node", "dist/index.js"],
    cwd="/home/toxic/sovereign/projects/mesh/browserless",
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, bufsize=1)

def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n"); proc.stdin.flush()

def read_msg():
    line = proc.stdout.readline()
    if not line:
        print("STDOUT_EOF; stderr:", proc.stderr.read()[:2000]); sys.exit(1)
    return json.loads(line)

rid = 1
def rpc(method, params=None):
    global rid
    send({"jsonrpc":"2.0","id":rid,"method":method,"params":params or {}})
    rid += 1
    return read_msg()

init = rpc("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1"}})
print("INIT server:", init["result"]["serverInfo"])
send({"jsonrpc":"2.0","method":"notifications/initialized"})
tools = rpc("tools/list")
names = [t["name"] for t in tools["result"]["tools"]]
persist = [n for n in names if n.startswith("persistent_")]
print("TOOL_COUNT:", len(names), "PERSISTENT:", persist)
assert len(persist) == 7, "expected 7 persistent_* tools, got %d" % len(persist)
st = rpc("tools/call", {"name":"persistent_status","arguments":{}})
txt = st["result"]["content"][0]["text"]
print("STATUS:", txt[:600])
s = json.loads(txt)
assert s["cdpAlive"] is True, "cdpAlive not true"
ev = rpc("tools/call", {"name":"persistent_evaluate","arguments":{"js":"navigator.userAgent"}})
print("EVAL_UA:", json.dumps(ev)[:300])
assert "Chrome" in json.dumps(ev), "userAgent missing Chrome"
proc.stdin.close()
proc.wait(timeout=15)
print("PROBE_OK")
