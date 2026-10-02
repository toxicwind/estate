#!/usr/bin/env python3
"""Verify small/medium/code/long return real visible completions. Run on yote."""
import json, sys, time, urllib.request

BASE = "http://127.0.0.1:25100"
MODELS = ["small", "medium", "code", "long"]
ok = 0
for m in MODELS:
    body = json.dumps({
        "model": m,
        "messages": [{"role": "user",
                      "content": "Reply with exactly this sentence and nothing else: The %s route is alive." % m}],
        "max_tokens": 256, "temperature": 0,
    }).encode()
    req = urllib.request.Request(BASE + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            d = json.load(r)
        dt = time.time() - t
        msg = d["choices"][0]["message"]
        content = (msg.get("content") or "").strip()
        model = d.get("model", "")
        good = ("alive" in content.lower()) and len(content) > 5
        print("%-6s 200 in %6.1fs model=%s content=%r %s"
              % (m, dt, model.split("/")[-1][:40], content[:60], "OK" if good else "CONTENT-CHECK"))
        if good:
            ok += 1
    except Exception as e:
        print("%-6s FAILED %s" % (m, str(e)[:120]))
print("RESULT: %d/%d ok" % (ok, len(MODELS)))
sys.exit(0 if ok == len(MODELS) else 1)
