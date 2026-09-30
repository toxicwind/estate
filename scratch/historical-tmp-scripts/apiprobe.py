import os, urllib.request, json, time
key = os.environ.get("ANTHROPIC_API_KEY", "")
print("key_present:", bool(key))
for url, headers, body in [
    ("https://api.anthropic.com/v1/messages",
     {"Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
     {"model": "claude-opus-4-6", "max_tokens": 8, "messages": [{"role": "user", "content": "say ALIVE"}]}),
]:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=45)
        print(url, "->", r.status, "in %.1fs" % (time.time() - t0), r.read()[:120])
    except Exception as e:
        print(url, "-> ERR after %.1fs: %s: %s" % (time.time() - t0, type(e).__name__, str(e)[:160]))
