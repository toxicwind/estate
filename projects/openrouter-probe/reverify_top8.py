#!/usr/bin/env python3
"""reverify_top8.py -- direct re-verification of the abstract-probe top 8."""
import json, re, time, urllib.request, urllib.error

SECRETS = "/home/toxic/.secrets"
OUT = "/home/toxic/sovereign/projects/openrouter-probe/reverify-20260920.jsonl"
TOKEN = "ABSTRACT-7X3Q"


def load_key(n):
    pat = re.compile(r"^\s*(?:export\s+)?%s\s*=\s*(.+?)\s*$" % re.escape(n))
    for line in open(SECRETS):
        m = pat.match(line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    raise SystemExit("no key")


KEY = load_key("OPENROUTER_API_KEY_1")
MODELS = [
    "nex-agi/nex-n2.5-mini:free",
    "poolside/laguna-s-2.1:free",
    "cohere/north-mini-code:free",
    "inclusionai/ling-3.0-flash-sante:free",
    "nex-agi/nex-n2.5-pro:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3.5-lightning:free",
]

out = open(OUT, "w")
for m in MODELS:
    body = json.dumps({
        "model": m,
        "messages": [{"role": "user",
                      "content": "Output exactly: %s. No other text." % TOKEN}],
        "max_tokens": 30, "temperature": 0}).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body, method="POST",
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=45)
        d = json.loads(r.read().decode())
        c = (d["choices"][0]["message"]["content"] or "").strip()
        row = {"model": m, "http": 200, "lat_ms": round((time.time() - t0) * 1000, 1),
               "content": c[:60].replace(KEY, "***")}
    except urllib.error.HTTPError as e:
        row = {"model": m, "http": e.code, "lat_ms": round((time.time() - t0) * 1000, 1),
               "content": ""}
    except Exception as e:
        row = {"model": m, "http": -1, "lat_ms": round((time.time() - t0) * 1000, 1),
               "content": str(e)[:60].replace(KEY, "***")}
    out.write(json.dumps(row) + "\n")
    out.flush()
    print("%s http=%s lat=%sms %r" % (m, row["http"], row["lat_ms"], row["content"][:40]), flush=True)
    time.sleep(2)
out.close()
print("wrote", OUT)
