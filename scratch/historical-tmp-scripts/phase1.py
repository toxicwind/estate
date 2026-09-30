import json, subprocess, select, time
MCP_SH = "/home/toxic/sovereign/projects/mesh/browserless/mcp.sh"
def run_calls(calls, timeout=60):
    lines = [json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"b","version":"1"}}}),
             json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"})]
    ids = {}
    for i,(n,a) in enumerate(calls, start=10):
        ids[i]=n; lines.append(json.dumps({"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":n,"arguments":a}}))
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
    try: p.kill()
    except: pass
    out=[]
    for i,(n,a) in enumerate(calls, start=10):
        d=got.get(i)
        if d is None: out.append((n,False,"NO_RESPONSE"))
        elif "error" in d: out.append((n,False,"RPC_ERROR:"+json.dumps(d["error"])[:120]))
        else:
            r=d.get("result",{}); c=r.get("content",[])
            txt=c[0].get("text","") if c else json.dumps(r)[:150]
            out.append((n,not r.get("isError",False),txt[:150].replace("\n"," ")))
    return out
TP="data:text/html,<html><body><h1 id=h>hello</h1><input id=i><button id=b>go</button></body></html>"
for phase,calls in [
  ("P1",[("persistent_status",{}),("persistent_tabs",{})]),
  ("P2",[("persistent_new_tab",{"url":TP})]),
]:
    t0=time.time()
    res=run_calls(calls)
    print(f"== {phase} ({time.time()-t0:.1f}s) ==")
    for (n,ok,txt) in res: print(("PASS " if ok else "FAIL ")+n+" - "+txt[:100])
