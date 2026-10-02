import json, subprocess, select, time, os, re
MCP_SH = "/home/toxic/sovereign/projects/mesh/browserless/mcp.sh"
tok = None
try:
    for line in open("/home/toxic/.browserless/.env"):
        m = re.match(r"BROWSERLESS_TOKEN=(.*)", line.strip())
        if m: tok = m.group(1).strip().strip("\"").strip(chr(39))
except: pass
print("TOKEN_FOUND:", bool(tok))
def call(calls, timeout=40):
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
def show(g, calls):
    for i,(n,a) in enumerate(calls, start=10):
        d=g.get(i)
        if d is None: print("FAIL",n,"- NO_RESPONSE"); continue
        if "error" in d: print("FAIL",n,"-",json.dumps(d["error"])[:140]); continue
        r=d.get("result",{}); c=r.get("content",[])
        txt=c[0].get("text","") if c else json.dumps(r)[:80]
        print(("PASS " if not r.get("isError") else "FAIL ")+n+" - "+txt[:110].replace("\n"," "))
TP="data:text/html,<h1>hi</h1>"
print("== INIT ==")
g=call([("initialize_browserless",{"token":tok})] if tok else [("initialize_browserless",{})],timeout=30)
show(g,[("initialize_browserless",{})])
if tok:
    print("== LEGACY (authenticated) ==")
    g=call([("get_health",{}),("get_config",{}),("get_metrics",{}),("get_sessions",{})],timeout=40); show(g,[("get_health",{}),("get_config",{}),("get_metrics",{}),("get_sessions",{})])
    g=call([("get_content",{"url":TP}),("take_screenshot",{"url":TP})],timeout=60); show(g,[("get_content",{"url":TP}),("take_screenshot",{"url":TP})])
