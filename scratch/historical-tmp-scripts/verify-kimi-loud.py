#!/usr/bin/env python3
"""Kimi aliases must fail LOUD with genuine upstream status. Run on yote."""
import json, sys, urllib.request, urllib.error

BASE = "http://127.0.0.1:25100"

def probe(model):
    body = json.dumps({"model": model,
        "messages": [{"role": "user", "content": "Reply: KIMI_OK"}],
        "max_tokens": 32}).encode()
    req = urllib.request.Request(BASE + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.load(r)
        return ("200", (d.get("choices", [{}])[0].get("message", {}).get("content", "") or "")[:40], "")
    except urllib.error.HTTPError as e:
        try: err = e.read().decode()[:120]
        except Exception: err = ""
        return (str(e.code), "", err)
    except Exception as e:
        return ("ERR", "", str(e)[:80])

ok = 0
for m in ["kimi", "kimi-k2", "kimi-code", "kimi-auto"]:
    code, content, err = probe(m)
    loud = code in ("402", "404", "429", "503") and bool(err)
    ok += 1 if loud else 0
    print("%-9s: HTTP %s loud=%s content=%r err=%r" % (m, code, loud, content, err[:90]))
print("LOUD-FAILURE: %d/4" % ok)
sys.exit(0 if ok == 4 else 1)
