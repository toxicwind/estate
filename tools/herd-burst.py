#!/usr/bin/env python3
"""herd-burst: A/B burst-concurrency probe. N concurrent requests at one model,
measures per-request latency p50/p95 + aggregate throughput. Usage:
  herd-burst.py <model> <concurrency> [max_tokens]"""
import json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

model = sys.argv[1] if len(sys.argv) > 1 else "beellama/exaone-4-0-1-2b-iq4xs"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 8
MT = int(sys.argv[3]) if len(sys.argv) > 3 else 32
PROMPT = "Write a haiku about GPUs. Exactly 3 lines."

def one(i):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": PROMPT}],
                       "max_tokens": MT, "stream": False}).encode()
    req = urllib.request.Request("http://127.0.0.1:25100/v1/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    t0 = time.monotonic(); err, toks = None, 0
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            j = json.load(r)
            toks = j.get("usage", {}).get("completion_tokens", 0)
    except Exception as e:
        err = "%s: %s" % (type(e).__name__, str(e)[:80])
    return {"i": i, "dt": round(time.monotonic() - t0, 2), "toks": toks, "err": err}

t0 = time.monotonic()
with ThreadPoolExecutor(max_workers=N) as ex:
    res = list(ex.map(one, range(N)))
wall = time.monotonic() - t0
ok = [r for r in res if not r["err"]]
dts = sorted(r["dt"] for r in ok)
tot_toks = sum(r["toks"] for r in ok)
def pct(p): return dts[min(len(dts)-1, int(p*len(dts)))] if dts else None
print("model=%s N=%d ok=%d/%d wall=%.1fs" % (model, N, len(ok), N, wall))
print("p50=%.2fs p95=%.2fs max=%.2fs" % (pct(0.5), pct(0.95), max(dts) if dts else 0))
print("aggregate=%d toks / %.1fs = %.1f tok/s" % (tot_toks, wall, tot_toks/wall if wall else 0))
for r in res:
    if r["err"]: print("  req%d FAIL %s" % (r["i"], r["err"]))
