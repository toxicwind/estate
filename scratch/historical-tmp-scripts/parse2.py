import json
tools=None
for line in open("/tmp/probe.out"):
    d=json.loads(line.strip())
    r=d.get("result") or {}
    if "tools" in r: tools=r["tools"]
print(len(tools))
[print(i, type(t), (t.get("name") if isinstance(t,dict) else t)) for i,t in enumerate(tools)]
