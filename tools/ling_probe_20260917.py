#!/usr/bin/env python3
"""Fresh Ling live probe (2026-09-17). Reads key NAME from /home/toxic/.secrets,
never prints key material. Streams 2 fixtures via OpenRouter, measures TTFT,
checks non-empty + expected substring. Prints JSON summary only."""
import json
import re
import time
import urllib.request

MODEL = "inclusionai/ling-3.0-flash-fin:free"
URL = "https://openrouter.ai/api/v1/chat/completions"


def load_key():
    vals = {}
    with open("/home/toxic/.secrets") as f:
        for line in f:
            m = re.match(r"\s*(?:export\s+)?(OPENROUTER[A-Za-z_]*)\s*=\s*(.+?)\s*$", line)
            if m:
                vals[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    for k in ("OPENROUTER_API_KEY", "OPENROUTER_API_KEY_2", "OPENROUTER_API_KEY_"):
        if vals.get(k):
            return k, vals[k]
    for k, v in vals.items():
        if v:
            return k, v
    raise SystemExit("no OPENROUTER* key name found in secrets file")


def probe(key, prompt, expect):
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 64,
            "stream": True,
        }
    ).encode()
    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://awrawr-pc/",
            "X-Title": "ling-probe",
        },
    )
    t0 = time.time()
    ttft = None
    text = ""
    prov = None
    err = None
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    o = json.loads(data)
                except Exception:
                    continue
                if prov is None:
                    prov = o.get("provider")
                d = o.get("choices", [{}])[0].get("delta", {})
                if d.get("content"):
                    if ttft is None:
                        ttft = (time.time() - t0) * 1000
                    text += d["content"]
    except Exception as e:  # noqa: BLE001 - report, don't crash
        err = f"{type(e).__name__}: {e}"
    total = (time.time() - t0) * 1000
    head = text.strip()
    return {
        "prompt": prompt,
        "nonempty": bool(head),
        "correct": expect in head,
        "ttft_ms": round(ttft, 1) if ttft is not None else None,
        "total_ms": round(total, 1),
        "provider": prov,
        "head": head[:40],
        "err": err,
    }


def main():
    key_name, key = load_key()
    fixtures = [
        ("What is 17*23? Reply with just the number.", "391"),
        ("Reply with exactly: Hatch-42.", "Hatch-42."),
    ]
    results = [probe(key, p, e) for p, e in fixtures]
    print(
        json.dumps(
            {
                "model": MODEL,
                "key_name": key_name,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "results": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
