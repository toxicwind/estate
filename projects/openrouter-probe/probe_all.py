#!/usr/bin/env python3
"""probe_all.py -- probe EVERY model on OpenRouter's /v1/models endpoint.

Reads OPENROUTER_API_KEY_1 from /home/toxic/.secrets IN-PROCESS.
The key NEVER leaves this box and is NEVER printed or logged.
Rank on quality/latency/availability only -- cost is NOT a factor (Chris directive).

Usage: python3 probe_all.py
Output: /home/toxic/sovereign/projects/openrouter-probe/results-<ts>.jsonl + stdout tables.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

SECRETS = "/home/toxic/.secrets"
OUTDIR = "/home/toxic/sovereign/projects/openrouter-probe"
BASE = "https://openrouter.ai/api/v1"
KEY_NAME = "OPENROUTER_API_KEY_1"
WORKERS = 8
PER_MODEL_TIMEOUT = 25


def load_key(name):
    pat = re.compile(r"^\s*(?:export\s+)?%s\s*=\s*(.+?)\s*$" % re.escape(name))
    with open(SECRETS) as f:
        for line in f:
            m = pat.match(line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    raise SystemExit("key %s not found in %s" % (name, SECRETS))


KEY = load_key(KEY_NAME)


def sanitize(s):
    # defense in depth: never let the key value into any recorded string
    if not s:
        return s
    return s.replace(KEY, "***")


def api_get(path):
    req = urllib.request.Request(
        BASE + path, headers={"Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def probe(model_id):
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": "say OK"}],
        "max_tokens": 5,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=body, method="POST",
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://yote.local",
                 "X-Title": "openrouter-probe"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=PER_MODEL_TIMEOUT) as r:
            d = json.load(r)
            lat = (time.time() - t0) * 1000
            content = ""
            try:
                content = d["choices"][0]["message"]["content"] or ""
            except Exception:
                pass
            return {"model": model_id, "http": 200, "lat_ms": round(lat, 1),
                    "has_content": bool(content.strip()),
                    "preview": sanitize(content.strip()[:80])}
    except urllib.error.HTTPError as e:
        lat = (time.time() - t0) * 1000
        try:
            eb = e.read()[:200].decode("utf-8", "replace")
        except Exception:
            eb = ""
        return {"model": model_id, "http": e.code, "lat_ms": round(lat, 1),
                "has_content": False, "preview": "",
                "error": sanitize(eb[:120])}
    except Exception as e:
        lat = (time.time() - t0) * 1000
        return {"model": model_id, "http": -1, "lat_ms": round(lat, 1),
                "has_content": False, "preview": "",
                "error": sanitize(type(e).__name__ + ": " + str(e)[:100])}


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    print("key: %s loaded (%d chars, NOT shown)" % (KEY_NAME, len(KEY)), flush=True)
    print("fetching model list...", flush=True)
    models_data = api_get("/models")
    ids = [m["id"] for m in models_data.get("data", []) if m.get("id")]
    print("%d models to probe (no :free filter)" % len(ids), flush=True)

    results = []
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(probe, mid): mid for mid in ids}
        done = 0
        for fut in as_completed(futs):
            results.append(fut.result())
            done += 1
            if done % 25 == 0:
                print("  %d/%d (%.0fs)" % (done, len(ids), time.time() - t_start),
                      flush=True)

    out = os.path.join(OUTDIR, "results-%s.jsonl" % ts)
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    ok = [r for r in results if r["http"] == 200 and r["has_content"]]
    ok.sort(key=lambda r: r["lat_ms"])
    print("\n=== WORKING MODELS (%d/%d) ===" % (len(ok), len(results)))
    print("%-62s %6s %9s  %s" % ("model", "http", "lat_ms", "preview"))
    for r in ok:
        print("%-62s %6d %9.1f  %s" % (
            r["model"][:62], r["http"], r["lat_ms"], r["preview"][:40]))

    print("\n=== NON-200 BREAKDOWN ===")
    for code, n in sorted(Counter(
            r["http"] for r in results if r["http"] != 200).items()):
        print("  http %s: %d models" % (code, n))
    no_content = [r for r in results
                  if r["http"] == 200 and not r["has_content"]]
    if no_content:
        print("  http 200 but EMPTY content: %d models" % len(no_content))
        for r in no_content[:10]:
            print("    %s" % r["model"][:70])

    kimi = [r for r in results
            if "kimi" in r["model"].lower() or "moonshot" in r["model"].lower()]
    print("\n=== KIMI/MOONSHOT (%d probed) ===" % len(kimi))
    for r in sorted(kimi, key=lambda r: r["model"]):
        detail = ("content=" + r["preview"][:40]) if r["preview"] else r.get("error", "")[:70]
        print("%-62s http=%s lat=%7.0fms %s" % (
            r["model"][:62], r["http"], r["lat_ms"], detail))

    print("\nresults: %s" % out)
    print("total wall: %.0fs" % (time.time() - t_start))


if __name__ == "__main__":
    main()
