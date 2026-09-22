import json, subprocess, select, time
MCP_SH = "/home/toxic/sovereign/projects/mesh/browserless/mcp.sh"
lines = [json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"b","version":"1"}}}),
         json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}),
         json.dumps({"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"persistent_tabs","arguments":{}}}),
         json.dumps({"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"persistent_activate_tab","arguments":{"tab":0}}}),
         json.dumps({"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"persistent_tabs","arguments":{}}})]
p = subprocess.Popen([MCP_SH], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
p.stdin.write("\n".join(lines)+"\n"); p.stdin.flush()
deadline=time.time()+30
while time.time()<deadline:
    r,_,_ = select.select([p.stdout],[],[],1.0)
    if r:
        line=p.stdout.readline()
        if not line: break
        try: d=json.loads(line)
        except: continue
        if d.get("id",0)>=10: print("ID",d["id"],":",json.dumps(d)[:400]); print()
    elif p.poll() is not None: break
p.kill()
