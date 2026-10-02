#!/usr/bin/env python3
"""probe_reliability.py -- hardened abstract probe over every OpenRouter /v1/models entry.

Method (v3 -- supersedes the 14:25/14:29 single-pass sweeps of 2026-09-20):
  * abstract prompt: "Output exactly: ABSTRACT-7X3Q. No other text."
  * TRIALS sequential full passes. The passes themselves provide natural
    temporal spacing between trials of the same model -- ZERO artificial
    sleeps, pacing, or rate limits (doctrine).
  * bounded concurrency via ThreadPoolExecutor (not a rate limit: a resource bound).
  * per-model: reliability (exact-match rate over trials), latency
    distribution (mean/p50/p99/min/max over exact hits), structured error
    classes (402-not-entitled vs 404-dead-id vs 429-throttled vs 200-empty...).
  * HTTP 200 with an empty body is recorded as 200-empty and is NEVER
    ranked as usable.
  * ranking is explicitly SPECULATIVE: it measures instruction-following on
    a trivial abstract task, not model quality.

Key: OPENROUTER_API_KEY_FREE (the free-models-only credential) is read
IN-PROCESS from /home/toxic/.secrets. The value never leaves this box,
never printed, never logged (sanitize() defense on every string that
could carry it).
"""
import json
import re
import statistics
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

SECRETS = "/home/toxic/.secrets"
OUTDIR = "/home/toxic/sovereign/projects/openrouter-probe"
BASE = "https://openrouter.ai/api/v1"
KEY_NAME = "OPENROUTER_API_KEY_FREE"  # free-models-only credential (Chris 2026-09-20)
WORKERS = 10
TIMEOUT = 30
TRIALS = 3
TOKEN = "ABSTRACT-7X3Q"
PROMPT = "Output exactly: %s. No other text." % TOKEN
TS = time.strftime("%Y%m%d-%H%M%S")


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
    return s.replace(KEY, "***") if s else s


def api(path, data=None, timeout=TIMEOUT):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        BASE + path, data=body, method="POST" if body else "GET",
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://sovereign.local",
                 "X-Title": "sovereign-probe"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode()), (time.monotonic() - t0) * 1000, None
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()[:200]
        except Exception:
            detail = ""
        return e.code, None, (time.monotonic() - t0) * 1000, sanitize(detail)
    except Exception as e:
        return -1, None, (time.monotonic() - t0) * 1000, sanitize(str(e)[:200])


def score_of(text):
    t = (text or "").strip()
    if t == TOKEN:
        return 2
    if TOKEN in t:
        return 1
    return 0


def classify(status, content):
    """Structured error class. 200-empty is an outcome, not a success."""
    if status == 200:
        return None if content else "200-empty"
    return {
        402: "402-not-entitled",  # key not entitled to this model (free key vs paid ID)
        404: "404-dead-id",
        429: "429-throttled",
        403: "403-refused",
        401: "401-bad-key",
        -1: "transport-error",
    }.get(status, "http-%d" % status)


def attempt(model):
    st, data, ms, err = api("/chat/completions", {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 100, "temperature": 0})
    content = ""
    if data:
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except Exception:
            pass
    content = content.strip()
    return {"model": model, "http": st, "lat_ms": round(ms, 1),
            "score": score_of(content), "has_content": bool(content),
            "err": classify(st, content), "detail": err,
            "preview": sanitize(content[:80])}


def pct(sorted_vals, p):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def main():
    st, models, _, err = api("/models", timeout=30)
    assert st == 200, "model list failed: %s %s" % (st, err)
    ids = [m["id"] for m in models["data"]]
    print("key=%s trials=%d workers=%d models=%d prompt=%r"
          % (KEY_NAME, TRIALS, WORKERS, len(ids), PROMPT), flush=True)

    jl_path = "%s/reliability-%s.jsonl" % (OUTDIR, TS)
    out = open(jl_path, "w")
    rows = []
    # Sequential full passes: pass N+1 starts only when pass N completes.
    # Same-model trials end up minutes apart with no sleep/pacing anywhere.
    for trial in range(1, TRIALS + 1):
        print("pass %d/%d" % (trial, TRIALS), flush=True)
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(attempt, m): m for m in ids}
            done = 0
            for f in as_completed(futs):
                r = f.result()
                r["trial"] = trial
                rows.append(r)
                out.write(json.dumps(r) + "\n")
                out.flush()
                done += 1
                if done % 100 == 0:
                    print("  pass %d: %d/%d" % (trial, done, len(ids)), flush=True)
    out.close()

    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)

    aggs = []
    for m, rs in by_model.items():
        n = len(rs)
        exact = sum(1 for r in rs if r["score"] == 2)
        contains = sum(1 for r in rs if r["score"] == 1)
        empty200 = sum(1 for r in rs if r["err"] == "200-empty")
        lats = sorted(r["lat_ms"] for r in rs if r["score"] == 2)
        errs = Counter(r["err"] for r in rs if r["err"])
        aggs.append({
            "model": m, "trials": n,
            "exact": exact, "contains": contains, "empty200": empty200,
            "exact_rate": round(exact / n, 3),
            "best_score": max(r["score"] for r in rs),
            "lat_exact_ms": ({
                "mean": round(statistics.mean(lats), 1),
                "p50": round(pct(lats, 50), 1),
                "p99": round(pct(lats, 99), 1),
                "min": round(lats[0], 1), "max": round(lats[-1], 1),
                "n": len(lats)} if lats else None),
            "errs": dict(errs.most_common()),
        })

    def rank_key(a):
        p50 = a["lat_exact_ms"]["p50"] if a["lat_exact_ms"] else 1e12
        return (-a["exact_rate"], -a["best_score"], p50, a["model"])

    ranked = sorted(aggs, key=rank_key)
    result = {"ts": TS, "key_name": KEY_NAME, "prompt": PROMPT, "trials": TRIALS,
              "workers": WORKERS, "model_count": len(ids),
              "note": "SPECULATIVE ranking: instruction-following on a trivial "
                      "abstract task, not quality. exact_rate = fraction of "
                      "trials returning exactly the token.",
              "ranking": [a["model"] for a in ranked],
              "models": {a["model"]: a for a in ranked}}
    js_path = "%s/reliability-%s.json" % (OUTDIR, TS)
    json.dump(result, open(js_path, "w"), indent=1)

    print("http:", Counter(r["http"] for r in rows).most_common(8))
    print("err:", Counter(r["err"] for r in rows if r["err"]).most_common(8))
    print("--- speculative ranking top 25 (exact_rate desc, p50 asc) ---")
    for a in ranked[:25]:
        lat = a["lat_exact_ms"]
        ls = ("p50=%7.0fms" % lat["p50"]) if lat else "p50=     --"
        print("rate=%.2f best=%d %-8s %-55s %s"
              % (a["exact_rate"], a["best_score"], ls, a["model"],
                 str(a["errs"])[:44]))
    print("wrote %s %s" % (jl_path, js_path))


if __name__ == "__main__":
    main()
