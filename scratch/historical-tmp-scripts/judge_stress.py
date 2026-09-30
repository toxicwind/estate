#!/usr/bin/env python3
"""Stress oracle-judge-local: N consecutive completions, assert 200 + visible content.
Run on yote. Usage: python3 judge_stress.py [N]"""
import json, sys, time, urllib.request

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
BASE = "http://127.0.0.1:25100"
ok = 0
for i in range(N):
    body = json.dumps({
        "model": "oracle-judge-local",
        "messages": [{"role": "user",
                      "content": "Reply with exactly this word and nothing else: JUDGE%d" % i}],
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
        tag = "JUDGE%d" % i
        good = tag in content or ("JUDGE" in content and str(i) in content)
        print("try %2d: 200 in %6.1fs model=%s content=%r %s"
              % (i, dt, model.split("/")[-1], content[:40], "OK" if good else "CONTENT-MISMATCH"))
        if good:
            ok += 1
    except Exception as e:
        print("try %2d: FAILED %s" % (i, e))
print("RESULT: %d/%d ok" % (ok, N))
sys.exit(0 if ok == N else 1)
