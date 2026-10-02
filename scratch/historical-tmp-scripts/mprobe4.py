import os, urllib.request, json, time
key = os.environ.get("FLOCK_API_KEY", "")
req = urllib.request.Request("http://127.0.0.1:25193/v1/chat/completions",
    data=json.dumps({"model": "moonshotai/kimi-k3", "messages": [{"role": "user", "content": "say ALIVE"}], "max_tokens": 5}).encode(),
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
t0 = time.time()
try:
    r = urllib.request.urlopen(req, timeout=150)
    print("status:", r.status, "in %.1fs" % (time.time()-t0))
    print(r.read()[:200])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, "in %.1fs" % (time.time()-t0), e.read()[:120])
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:100])
