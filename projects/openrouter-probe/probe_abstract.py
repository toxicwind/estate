#!/usr/bin/env python3
"""probe_abstract.py -- probe EVERY OpenRouter model with an abstract prompt.

Abstract prompt tests instruction-following with zero domain content:
    "Output exactly: ABSTRACT-7X3Q. No other text."

Scoring (speculative ranking signal):
    2 = exact match (after strip)
    1 = contains the token
    0 = anything else / error

Sort: score desc, latency asc. Cost is NOT a factor (402s fail fast, free).

Reads OPENROUTER_API_KEY_FREE from /home/toxic/.secrets IN-PROCESS.
Key NEVER leaves this box, NEVER printed or logged (sanitize defense).
"""
import json, re, time, urllib.request, urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

SECRETS = "/home/toxic/.secrets"
OUTDIR = "/home/toxic/sovereign/projects/openrouter-probe"
BASE = "https://openrouter.ai/api/v1"
KEY_NAME = "OPENROUTER_API_KEY_FREE"
WORKERS = 8
TIMEOUT = 30
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
    raise SystemExit("key %s not found" % name)


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
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode()), (time.time() - t0) * 1000, None
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()[:200]
        except Exception:
            detail = ""
        return e.code, None, (time.time() - t0) * 1000, sanitize(detail)
    except Exception as e:
        return -1, None, (time.time() - t0) * 1000, sanitize(str(e)[:200])


def score_of(text):
    t = (text or "").strip()
    if t == TOKEN:
        return 2
    if TOKEN in t:
        return 1
    return 0


def probe(model):
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
    return {"model": model, "http": st, "lat_ms": round(ms, 1),
            "score": score_of(content), "has_content": bool(content.strip()),
            "preview": sanitize(content.strip()[:80]), "error": err}


st, models, _, err = api("/models", timeout=30)
assert st == 200, "model list failed: %s %s" % (st, err)
ids = [m["id"] for m in models["data"]]
print("probing %d models, prompt=%r" % (len(ids), PROMPT), flush=True)

out = open("%s/abstract-%s.jsonl" % (OUTDIR, TS), "w")
rows = []
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(probe, m): m for m in ids}
    done = 0
    for f in as_completed(futs):
        r = f.result()
        rows.append(r)
        out.write(json.dumps(r) + "\n")
        out.flush()
        done += 1
        if done % 50 == 0:
            print("  %d/%d" % (done, len(ids)), flush=True)
out.close()

print("http:", Counter(r["http"] for r in rows).most_common(6))
print("score:", Counter(r["score"] for r in rows).most_common(4))
ranked = sorted(rows, key=lambda r: (-r["score"], r["lat_ms"]))
print("--- speculative ranking top 30 ---")
for r in ranked[:30]:
    print("score=%d lat=%7.0fms %-55s %r" % (r["score"], r["lat_ms"], r["model"], r["preview"][:40]))
json.dump(ranked, open("%s/ranking-%s.json" % (OUTDIR, TS), "w"), indent=1)
print("wrote abstract-%s.jsonl ranking-%s.json" % (TS, TS))
