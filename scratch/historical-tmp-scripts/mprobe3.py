import os, urllib.request, json, time
key = os.environ.get("FLOCK_API_KEY", "")
for model in ["kimi-k3-nim", "openai/gpt-oss-20b"]:
    req = urllib.request.Request("http://127.0.0.1:25193/v1/chat/completions",
        data=json.dumps({"model": model, "messages": [{"role": "user", "content": "say ALIVE"}], "max_tokens": 5}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=60)
        print(model, "->", r.status, "in %.1fs" % (time.time()-t0), r.read()[:120])
    except urllib.error.HTTPError as e:
        print(model, "-> HTTP", e.code, "in %.1fs" % (time.time()-t0), e.read()[:80])
    except Exception as e:
        print(model, "-> ERR", type(e).__name__, str(e)[:100])
