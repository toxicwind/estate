"""First-class NVIDIA key scope verification. Key read in-process, never printed."""
import re, json, time, urllib.request, urllib.error

sec = open("/home/toxic/.secrets").read()
m = re.search(r'^export NVIDIA_API_KEY=(.+)$', sec, re.M)
KEY = m.group(1).strip().strip('"').strip("'")

def req(method, url, payload=None, timeout=30):
    data = json.dumps(payload).encode() if payload else None
    r = urllib.request.Request(url, data=data, method=method,
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        body = resp.read().decode(errors="replace")
        return {"status": resp.status, "ms": int((time.time()-t0)*1000), "body": body[:600]}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "ms": int((time.time()-t0)*1000),
                "body": e.read().decode(errors="replace")[:600]}
    except Exception as e:
        return {"status": "ERR", "ms": int((time.time()-t0)*1000), "body": str(e)[:200]}

out = {"phaseA_identity": {}, "phaseB_404class": {}}

# ---- Phase A: scope / identity ----
u = req("GET", "https://api.ngc.nvidia.com/v2/users/me")
# redact email-ish fields, keep roles/scopes
try:
    ub = json.loads(u["body"])
    u["user"] = {k: ub.get(k) for k in ("id", "name", "isVerified")}
    u["orgRoles"] = ub.get("orgRoles") or ub.get("roles")
    del u["body"]
except Exception:
    pass
out["phaseA_identity"]["users_me"] = u

o = req("GET", "https://api.ngc.nvidia.com/v2/orgs")
try:
    ob = json.loads(o["body"])
    orgs = ob if isinstance(ob, list) else ob.get("organizations", ob.get("orgs", []))
    o["orgs"] = [{"id": g.get("id"), "name": g.get("name"), "type": g.get("type"),
                  "roles": g.get("roles")} for g in (orgs or [])]
    del o["body"]
except Exception:
    pass
out["phaseA_identity"]["orgs"] = o

mo = req("GET", "https://integrate.api.nvidia.com/v1/models")
try:
    mob = json.loads(mo["body"])
    mo["count"] = len(mob.get("data", []))
    del mo["body"]
except Exception:
    pass
out["phaseA_identity"]["models_catalog"] = mo

# ---- Phase B: 404 classification, max_tokens=1 ----
def chat(model, timeout=30):
    return req("POST", "https://integrate.api.nvidia.com/v1/chat/completions",
        {"model": model, "messages": [{"role": "user", "content": "hi"}],
         "max_tokens": 1}, timeout=timeout)

targets = [
    ("retired_id", "moonshotai/kimi-k2-instruct"),
    ("catalog_kimi", "moonshotai/kimi-k2.6"),
    ("catalog_nemotron", "nvidia/llama-3.1-nemotron-70b-instruct"),
    ("catalog_llama31", "meta/llama-3.1-8b-instruct"),
    ("catalog_llama33", "meta/llama-3.3-70b-instruct"),
    ("catalog_nano", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"),
]
for label, mid in targets:
    r = chat(mid)
    # classify body shape
    b = r["body"]
    if "Not found for account" in b:
        r["class"] = "scope/entitlement-gate"
    elif r["status"] == 404 and "page not found" in b.lower():
        r["class"] = "dead/retired-id"
    elif r["status"] == 410:
        r["class"] = "retired-410"
    elif r["status"] == 200:
        r["class"] = "ENTITLED-working"
    else:
        r["class"] = "other"
    out["phaseB_404class"][label] = {"model": mid, **r}

print(json.dumps(out, indent=1))
