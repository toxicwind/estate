import json
tools=None
for line in open("/tmp/probe.out"):
    line=line.strip()
    if not line.startswith("{"): continue
    d=json.loads(line)
    r=d.get("result") or {}
    if "tools" in r: tools=r["tools"]
print(type(tools), len(tools) if tools else 0)
names=[t["name"] for t in tools]
print("count:",len(names))
print("first11:",names[:11])
