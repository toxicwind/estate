import os, urllib.request, json
key = os.environ.get("FLOCK_API_KEY", "")
for model in ["free", "nex-n2.5-mini:free"]:
    req = urllib.request.Request("http://127.0.0.1:25193/v1/chat/completions",
        data=json.dumps({"model": model, "messages": [{"role": "user", "content": "say ALIVE"}], "max_tokens": 8}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        print(model, "->", r.status, r.read()[:150])
    except urllib.error.HTTPError as e:
        print(model, "-> HTTP", e.code, e.read()[:300])
    except Exception as e:
        print(model, "-> ERR", type(e).__name__, str(e)[:120])
