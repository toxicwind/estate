import json, subprocess, select, time, os
tok = os.environ.get("BTOKEN", "")
lines = [
  json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"b","version":"1"}}}),
  json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}),
  json.dumps({"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"initialize_browserless","arguments":{"token":tok}}}),
  json.dumps({"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"get_config","arguments":{}}}),
  json.dumps({"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"get_health","arguments":{}}}),
  json.dumps({"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"get_metrics","arguments":{}}}),
  json.dumps({"jsonrpc":"2.0","id":14,"method":"tools/call","params":{"name":"get_sessions","arguments":{}}}),
]
p = subprocess.Popen(["node","dist/index.js"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd="/home/toxic/sovereign/projects/mesh/browserless")
p.stdin.write("\n".join(lines)+"\n"); p.stdin.flush()
got={}; deadline=time.time()+40
while time.time()<deadline and len(got)<5:
    r,_,_ = select.select([p.stdout],[],[],1.0)
    if r:
        line=p.stdout.readline()
        if not line: break
        try: d=json.loads(line)
        except: continue
        if d.get("id",0)>=10: got[d["id"]]=d
    elif p.poll() is not None: break
for i in [10,11,12,13,14]:
    d=got.get(i,{})
    status = "PASS" if "result" in d else "FAIL"
    detail = json.dumps(d.get("result", d.get("error",{})))[:90]
    print(f"ID {i} {status}: {detail}")
p.kill()
