import json
tools=None;status=None
for line in open("/tmp/probe2.out"):
    d=json.loads(line.strip())
    r=d.get("result") or {}
    if "tools" in r: tools=r["tools"]
    if d.get("id")==3: status=r
names=[t["name"] for t in tools]
print("count:",len(names))
print("first11_all_persistent:",all(n.startswith("persistent_" ) for n in names[:11]))
print("status_cdpAlive:",json.loads(status["content"][0]["text"])["cdpAlive"])
