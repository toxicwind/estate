#!/usr/bin/env python3
"""Sweep all OpenRouter models via the keypool (pinned to FREE key).
Sends a neutral probe prompt to each; records availability + latency + instruction-following.
Output: JSONL to /home/toxic/sovereign/var/or-free-sweep.jsonl"""
import json, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

POOL = "http://127.0.0.1:25109/openrouter"
PROMPT = "Reply with exactly: PROBE-OK"
OUT = "/home/toxic/sovereign/var/or-free-sweep.jsonl"

def get_models():
    req = urllib.request.Request(POOL + "/v1/models", method="GET")
    return [m["id"] for m in json.load(urllib.request.urlopen(req, timeout=30))["data"]]

def probe(model_id):
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 16,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(POOL + "/v1/chat/completions", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=45)
        d = json.load(resp)
        lat = (time.time() - t0) * 1000
        content = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return {"model": model_id, "ok": True, "http": 200,
                "latency_ms": round(lat, 1),
                "exact_match": content.strip() == "PROBE-OK",
                "content": content.strip()[:120]}
    except urllib.error.HTTPError as e:
        try: err = e.read()[:200].decode(errors="replace")
        except Exception: err = ""
        return {"model": model_id, "ok": False, "http": e.code,
                "latency_ms": round((time.time()-t0)*1000, 1), "error": err[:150]}
    except Exception as e:
        return {"model": model_id, "ok": False, "http": -1,
                "latency_ms": round((time.time()-t0)*1000, 1), "error": str(e)[:150]}

def main():
    models = get_models()
    print(f"probing {len(models)} models", flush=True)
    done = 0
    with open(OUT, "w") as f, ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(probe, models):
            f.write(json.dumps(r) + "\n"); f.flush()
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{len(models)}", flush=True)
    print("sweep complete", flush=True)

if __name__ == "__main__":
    main()
