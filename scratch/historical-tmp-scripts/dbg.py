import json, subprocess, select, time
MCP_SH = "/home/toxic/sovereign/projects/mesh/browserless/mcp.sh"
TOK = ""
lines = [json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"b","version":"1"}}}),
         json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}),
         json.dumps({"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"initialize_browserless","arguments":{"token":TOK}}}),
         json.dumps({"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"get_config","arguments":{}}})]
p = subprocess.Popen([MCP_SH], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
p.stdin.write("\n".join(lines)+"\n"); p.stdin.flush()
got={}; deadline=time.time()+40
while time.time()<deadline and len(got)<2:
    r,_,_ = select.select([p.stdout],[],[],1.0)
    if r:
        line=p.stdout.readline()
        if not line: break
        try: d=json.loads(line)
        except: continue
        if d.get("id",0)>=10: got[d["id"]]=d; print("ID",d["id"],json.dumps(d)[:300])
    elif p.poll() is not None: break
p.kill()
err=p.stderr.read()
print("STDERR:",err[:1500])
