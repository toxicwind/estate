import os, urllib.request, json, time
key = os.environ.get("FLOCK_API_KEY", "")
print("key_present:", bool(key))
req = urllib.request.Request("http://127.0.0.1:25193/v1/chat/completions",
    data=json.dumps({"model": "free", "messages": [{"role": "user", "content": "reply with exactly the word ALIVE"}], "max_tokens": 8}).encode(),
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
t0 = time.time()
try:
    r = urllib.request.urlopen(req, timeout=90)
    body = r.read()[:200]
    print("status:", r.status, "latency_s:", round(time.time() - t0, 1))
    print("body:", body)
except Exception as e:
    print("ERR after %.1fs: %s: %s" % (time.time() - t0, type(e).__name__, str(e)[:160]))
