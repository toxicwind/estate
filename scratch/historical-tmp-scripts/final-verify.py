#!/usr/bin/env python3
"""Final post-restart verification: all three modelmap issues. Run on yote."""
import json, sys, time, urllib.request, urllib.error

BASE = "http://127.0.0.1:25100"

def probe(model, content="Reply with exactly: VERIFY_OK", max_tokens=128, timeout=300):
    body = json.dumps({"model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens, "temperature": 0}).encode()
    req = urllib.request.Request(BASE + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        dt = time.time() - t
        msg = d.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        return ("200", dt, msg.strip()[:60], d.get("model", "").split("/")[-1][:40], None)
    except urllib.error.HTTPError as e:
        try: err = e.read().decode()[:100]
        except Exception: err = ""
        return (str(e.code), time.time() - t, "", "", err)
    except Exception as e:
        return ("ERR", time.time() - t, "", "", str(e)[:100])

print("=== ISSUE 1: oracle-judge-local (3x, must be 200 + content) ===")
ok1 = 0
for i in range(3):
    code, dt, content, model, err = probe("oracle-judge-local", "Reply with exactly: JUDGE%d" % i, 256)
    good = code == "200" and ("JUDGE%d" % i) in content
    ok1 += good
    print(" try %d: %s in %.1fs model=%s content=%r %s" % (i, code, dt, model, content, "OK" if good else ("ERR " + str(err))))

print("=== ISSUE 2: small/medium/code/long (must be 200 + visible content) ===")
ok2 = 0
for m in ["small", "medium", "code", "long"]:
    code, dt, content, model, err = probe(m, "Reply with exactly: The %s route is alive." % m, 256)
    good = code == "200" and "alive" in content.lower()
    ok2 += good
    print(" %-6s: %s in %.1fs model=%s content=%r %s" % (m, code, dt, model, content, "OK" if good else ("ERR " + str(err))))

print("=== ISSUE 3: kimi aliases (must fail LOUD with genuine upstream status) ===")
ok3 = 0
for m in ["kimi", "kimi-k2", "kimi-code", "kimi-auto"]:
    code, dt, content, model, err = probe(m, "Reply: KIMI_OK", 32, 180)
    loud = code in ("402", "404", "429", "503") and err
    ok3 += loud
    print(" %-9s: %s in %.1fs loud=%s err=%r" % (m, code, dt, loud, (err or "")[:80]))

print("=== REGRESSION: oracle-judge-a (remote shim, must still work) ===")
code, dt, content, model, err = probe("oracle-judge-a", "Reply with exactly: JUDGE_A_OK", 64, 180)
print(" judge-a: %s in %.1fs content=%r %s" % (code, dt, content, "OK" if code == "200" and content else "CHECK " + str(err)))

print("\nSUMMARY: issue1 %d/3, issue2 %d/4, issue3 %d/4 loud" % (ok1, ok2, ok3))
sys.exit(0 if (ok1 == 3 and ok2 == 4 and ok3 == 4) else 1)
