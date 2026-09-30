"""Probe what the NVIDIA key entitles us to. Reads key in-process, never prints it."""
import re, json, urllib.request

sec = open("/home/toxic/.secrets").read()
m = re.search(r'^export NVIDIA_API_KEY=(.+)$', sec, re.M)
key = m.group(1).strip().strip('"').strip("'")

def get(path, timeout=30, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com" + path,
        data=data,
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json"},
        method="POST" if payload else "GET",
    )
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200].decode(errors="replace")
    except Exception as e:
        return "ERR", str(e)[:150]

out = {}
s, models = get("/v1/models")
out["models_status"] = s
if s == 200:
    data = models.get("data", [])
    out["model_count"] = len(data)
    fam = {}
    for d in data:
        o = d.get("owned_by", "?")
        fam[o] = fam.get(o, 0) + 1
    out["owned_by"] = fam
    ids = sorted(str(d.get("id")) for d in data)
    out["kimi"] = [i for i in ids if "kimi" in i.lower()]
    out["nemotron"] = [i for i in ids if "nemotron" in i.lower()][:8]
    out["llama"] = [i for i in ids if "llama" in i.lower()][:8]
    out["embed"] = [i for i in ids if "embed" in i.lower()][:6]
    out["rerank"] = [i for i in ids if "rerank" in i.lower()][:6]
    out["first10"] = ids[:10]
print(json.dumps(out, indent=1))
