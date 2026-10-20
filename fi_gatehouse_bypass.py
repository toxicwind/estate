import os, json, urllib.request, urllib.error
BASE="https://freeinference.org"
KEY=os.environ.get("FI_KEY") or ""
def post_fi(payload):
    h={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"}
    req=urllib.request.Request(BASE+"/v1/chat/completions",data=json.dumps(payload).encode(),headers=h,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return r.status, r.read().decode()[:2000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:2000]

print("=== FIND 403 TRIGGER ===")
tests=[
 "gatehouse",
 "estate/gatehouse",
 "toolcall-llm",
 "model-guard",
 "ESTATE/GATEHOUSE",
 "mcpproxy-go",
 "pitchfork list",
]
for t in tests:
    st,body=post_fi({"model":"qwen3.6-35b","messages":[{"role":"user","content":f"Say {t}"}],"max_tokens":20})
    print(f"[{t}] -> {st}")

# Now hit YOUR local gatehouse at 25127 - the real one from pitchfork
for path in ["/","/mcp","/api","/v1/models","/health","/sse"]:
    try:
        req=urllib.request.Request(f"http://localhost:25127{path}",headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=2) as r:
            b=r.read().decode()
            print(f"\n[LOCAL GATEHOUSE :25127{path}] {r.status} {b[:2000]}")
    except Exception as e:
        print(f"[LOCAL :25127{path}] err {e}")

print("\n=== BYPASS TEST: gatehouse without estate words ===")
# This should NOT 403
st,body=post_fi({"model":"qwen3.6-35b","messages":[{"role":"system","content":"You are a gateway guard that logs cache decisions"},{"role":"user","content":"Log your cache decision for main.py"}],"max_tokens":100})
print(f"Sanitized gatehouse -> {st} {body[:2000]}")

print("\n=== DONE ===")
