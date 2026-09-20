#!/usr/bin/env python3
"""deep_pass.py -- deeper latency/throughput pass on working OpenRouter models.

Streaming completions: measures TTFT, total latency, tokens, TPS.
Reads OPENROUTER_API_KEY_1 from /home/toxic/.secrets IN-PROCESS.
Key NEVER leaves this box, NEVER printed.
Rank on quality/latency/availability only -- cost is NOT a factor.
"""
import json
import os
import re
import time
import urllib.request
import urllib.error

SECRETS = "/home/toxic/.secrets"
OUTDIR = "/home/toxic/sovereign/projects/openrouter-probe"
BASE = "https://openrouter.ai/api/v1"
KEY_NAME = "OPENROUTER_API_KEY_1"
REQS_PER_MODEL = 5
MAX_TOKENS = 50
TIMEOUT = 120


def load_key(name):
    pat = re.compile(r"^\s*(?:export\s+)?%s\s*=\s*(.+?)\s*$" % re.escape(name))
    with open(SECRETS) as f:
        for line in f:
            m = pat.match(line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    raise SystemExit("key not found")


KEY = load_key(KEY_NAME)

MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nex-agi/nex-n2.5-mini:free",
    "nex-agi/nex-n2.5-pro:free",
    "nvidia/nemotron-3.5-lightning:free",
]

PROMPT = "Write a 3-sentence story about a robot learning to paint."


def one_run(model_id):
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.7,
        "stream": True,
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=body, method="POST",
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://yote.local",
                 "X-Title": "openrouter-deep-pass"},
    )
    t0 = time.time()
    ttft = None
    chunks = 0
    text_parts = []
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            for line in r:
                line = line.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    d = json.loads(payload)
                    delta = d["choices"][0]["delta"].get("content", "")
                    if delta:
                        if ttft is None:
                            ttft = (time.time() - t0) * 1000
                        text_parts.append(delta)
                        chunks += 1
                except Exception:
                    pass
        total = (time.time() - t0) * 1000
        text = "".join(text_parts)
        # rough token estimate: ~4 chars/token
        est_tokens = max(1, len(text) // 4)
        gen_time = max(1, total - (ttft or 0))
        tps = est_tokens / (gen_time / 1000)
        return {"model": model_id, "ok": True,
                "ttft_ms": round(ttft or -1, 1),
                "total_ms": round(total, 1),
                "chars": len(text),
                "est_tokens": est_tokens,
                "tps": round(tps, 1),
                "sample": text[:100].replace("\n", " ")}
    except Exception as e:
        total = (time.time() - t0) * 1000
        return {"model": model_id, "ok": False,
                "total_ms": round(total, 1),
                "error": type(e).__name__ + ": " + str(e)[:100]}


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = os.path.join(OUTDIR, "deep-%s.jsonl" % ts)
    print("deep pass: %d models x %d reqs" % (len(MODELS), REQS_PER_MODEL),
          flush=True)
    with open(out, "w") as f:
        for mid in MODELS:
            print("=== %s ===" % mid, flush=True)
            for i in range(REQS_PER_MODEL):
                r = one_run(mid)
                r["iter"] = i
                f.write(json.dumps(r) + "\n")
                f.flush()
                if r["ok"]:
                    print("  iter %d: ttft=%.0fms total=%.0fs tps=%.1f" % (
                        i, r["ttft_ms"], r["total_ms"] / 1000, r["tps"]),
                        flush=True)
                else:
                    print("  iter %d: FAIL %s" % (i, r["error"]), flush=True)

    # aggregate
    print("\n=== DEEP PASS SUMMARY (quality/latency/availability; NO cost) ===")
    print("%-42s %6s %9s %9s %7s" % ("model", "ok", "ttft_ms", "total_ms", "tps"))
    agg = {}
    with open(out) as f:
        for line in f:
            r = json.loads(line)
            agg.setdefault(r["model"], []).append(r)
    rows = []
    for mid, rs in agg.items():
        oks = [r for r in rs if r["ok"]]
        if not oks:
            print("%-42s %6s  all failed" % (mid[:42], "0/%d" % len(rs)))
            continue
        ttft = sum(r["ttft_ms"] for r in oks) / len(oks)
        tot = sum(r["total_ms"] for r in oks) / len(oks)
        tps = sum(r["tps"] for r in oks) / len(oks)
        rows.append((mid, len(oks), len(rs), ttft, tot, tps))
    rows.sort(key=lambda x: (x[3], x[4]))  # rank by ttft then total
    for mid, ok, n, ttft, tot, tps in rows:
        print("%-42s %3d/%-3d %9.0f %9.0f %7.1f" % (
            mid[:42], ok, n, ttft, tot, tps))
    print("\nresults: %s" % out)


if __name__ == "__main__":
    main()
