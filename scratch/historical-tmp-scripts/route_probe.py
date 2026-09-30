#!/usr/bin/env python3
"""OpenFang chat-route acceptance probes (post-repair)."""
import json
import time
import urllib.request

ROUTES = [
    ("openfang:assistant", "http://127.0.0.1:25196"),
    ("openfang:squawk-relay", "http://127.0.0.1:25196"),
    ("openfang:oracle-market", "http://127.0.0.1:25196"),
    ("openfang:coyote", "http://127.0.0.1:25196"),
    ("openfang:assistant", "http://127.0.0.1:25103"),  # via mesh-front proxy
]

for model, base in ROUTES:
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly: ROUTE_OK"}],
            "max_tokens": 20,
        }
    ).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request(
            f"{base}/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            payload = json.load(r)
        dt = time.time() - t0
        text = ""
        try:
            text = payload["choices"][0]["message"]["content"]
        except Exception:
            text = json.dumps(payload)[:120]
        verdict = "EXACT_ROUTE_OK" if "ROUTE_OK" in text else "ALIVE_NONEXACT"
        print(f"{verdict} {model} via {base} {dt:.1f}s :: {text[:80]!r}")
    except Exception as e:
        print(f"FAIL {model} via {base} {time.time()-t0:.1f}s :: {e}")
