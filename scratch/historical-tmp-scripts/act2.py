import json, subprocess, select, time, re
MCP_SH = "/home/toxic/sovereign/projects/mesh/browserless/mcp.sh"
def call(calls, timeout=30):
    lines = [json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"b","version":"1"}}}),
             json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"})]
    for i,(n,a) in enumerate(calls, start=10):
        lines.append(json.dumps({"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":n,"arguments":a}}))
    p = subprocess.Popen([MCP_SH], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    p.stdin.write("\n".join(lines)+"\n"); p.stdin.flush()
    got={}; deadline=time.time()+timeout
    while time.time()<deadline and len(got)<len(calls):
        r,_,_ = select.select([p.stdout],[],[],1.0)
        if r:
            line=p.stdout.readline()
            if not line: break
            try: d=json.loads(line)
            except: continue
            if d.get("id",0)>=10: got[d["id"]]=d
        elif p.poll() is not None: break
    p.kill(); return got
# create tab, then activate it in a NEW process (like the failing test)
g=call([("persistent_new_tab",{"url":"data:text/html,<h1>y</h1>"})])
txt=g[10]["result"]["content"][0]["text"]; print("NEWTAB:",txt[:60])
m=re.search(r"New tab (\d+)",txt); tab=int(m.group(1))
g2=call([("persistent_tabs",{}),("persistent_activate_tab",{"tab":tab})])
for i in (10,11):
    d=g2.get(i,{})
    if "error" in d: print("ID",i,"ERROR:",json.dumps(d["error"])[:500])
    else: print("ID",i,"OK:",d["result"]["content"][0]["text"][:120])
