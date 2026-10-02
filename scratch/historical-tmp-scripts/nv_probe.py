import json, os, sys, time, urllib.request

def load_env(path):
    for line in open(path):
        s = line.strip()
        if s.startswith("export "):
            s = s[7:]
        if "=" in s and not s.startswith("#"):
            k, v = s.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env("/home/toxic/.config/claude/env")
key = os.environ.get("NVIDIA_NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY")
if not key:
    print("NO_KEY")
    sys.exit(1)

def call(url, payload=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, json.load(r), int((time.time() - t) * 1000)
    except Exception as e:
        return "ERR", str(e)[:150], int((time.time() - t) * 1000)

st, models, ms = call("https://integrate.api.nvidia.com/v1/models")
print("MODELS_STATUS", st, "ms=", ms)
data = models.get("data", []) if st == 200 else []
emb_models = sorted(m["id"] for m in data if "embed" in m.get("id", "").lower())
print("EMBEDDING_MODELS", json.dumps(emb_models))

for m in emb_models[:4]:
    st, d, ms = call(
        "https://integrate.api.nvidia.com/v1/embeddings",
        {"model": m, "input": ["The quick brown fox jumps over the lazy dog"],
         "input_type": "query", "encoding_format": "float"},
    )
    if st == 200:
        print(m, "OK dims=", len(d["data"][0]["embedding"]), "ms=", ms,
              "usage=", d.get("usage"))
    else:
        print(m, "FAIL", d, "ms=", ms)
