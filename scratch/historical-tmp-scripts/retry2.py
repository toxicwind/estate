#!/usr/bin/env python3
import json, urllib.request
for base, model in [("http://127.0.0.1:25196", "openfang:coyote"),
                    ("http://127.0.0.1:25103", "openfang:assistant")]:
    body = json.dumps({"model": model,
                       "messages": [{"role": "user", "content": "Reply with exactly: ROUTE_OK"}],
                       "max_tokens": 20}).encode()
    try:
        req = urllib.request.Request(f"{base}/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.load(r)
        print(base, model, "->", d["choices"][0]["message"]["content"][:40])
    except Exception as e:
        print(base, model, "-> FAIL:", str(e)[:100])
