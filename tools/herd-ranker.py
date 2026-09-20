#!/usr/bin/env python3
"""herd-ranker: sweep every loadable model in the llama-swap herd, rank by latency/validity.
Kimi-auto pattern: thread-local hot persistent connections, fail-fast ceilings,
sane concurrency (no thundering herd against one GPU), JSONL ledger.
Event-driven pacing: no artificial sleeps; the swap queue itself paces us.
"""
import json, re, time, sys, threading, http.client, os
from concurrent.futures import ThreadPoolExecutor

HERD = "/home/toxic/sovereign/config/herd.yaml"
OUTDIR = "/home/toxic/sovereign/data/herd-ranker"
HOST, PORT = "127.0.0.1", 25100
COLD_CEIL = 300   # includes model load
WARM_CEIL = 60
WORKERS = 2
PROMPT = "What is 2+2? Reply with ONLY the number, no explanation."

os.makedirs(OUTDIR, exist_ok=True)
LEDGER = os.path.join(OUTDIR, "ledger.jsonl")

def loadable_models():
    models, cur = [], None
    for line in open(HERD):
        m = re.match(r"^  ([A-Za-z0-9_./-]+):$", line)
        if m:
            cur = {"id": m.group(1), "cmd": False}
            models.append(cur)
        elif cur and re.match(r"^    cmd:", line):
            cur["cmd"] = True
    return [m["id"] for m in models if m["cmd"]]

_tls = threading.local()
def conn():
    c = getattr(_tls, "c", None)
    if c is None:
        c = http.client.HTTPConnection(HOST, PORT, timeout=WARM_CEIL)
        _tls.c = c
    return c

def fresh_conn(ceiling):
    try:
        _tls.c.close()
    except Exception:
        pass
    _tls.c = http.client.HTTPConnection(HOST, PORT, timeout=ceiling)
    return _tls.c

def probe(model, ceiling, tag):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": PROMPT}],
                       "max_tokens": 32, "stream": True}).encode()
    t0 = time.monotonic(); first = None; ntok = 0
    status, err, finish = None, None, None
    c = fresh_conn(ceiling)
    try:
        c.request("POST", "/v1/chat/completions", body, {"Content-Type": "application/json"})
        r = c.getresponse()
        status = r.status
        if status != 200:
            err = "http_%d %s" % (status, r.read(200).decode("utf8", "replace")[:120])
        else:
            deadline = t0 + ceiling
            while time.monotonic() < deadline:
                line = r.readline()
                if not line:
                    break
                if line.startswith(b"data:"):
                    d = line[5:].strip()
                    if d == b"[DONE]":
                        break
                    try:
                        j = json.loads(d)
                        ch = j["choices"][0]
                        delta = ch.get("delta", {}) or {}
                        tok = delta.get("content") or delta.get("reasoning_content")
                        if ch.get("finish_reason"):
                            finish = ch["finish_reason"]
                        if tok:
                            if first is None:
                                first = time.monotonic() - t0
                            ntok += 1
                    except Exception:
                        pass
    except Exception as e:
        err = "%s: %s" % (type(e).__name__, str(e)[:100])
    total = time.monotonic() - t0
    tps = ntok / (total - first) if first and total > first else 0.0
    return {"model": model, "tag": tag, "status": status,
            "ttft": round(first, 3) if first else None,
            "total": round(total, 2), "toks": ntok,
            "tps": round(tps, 1), "finish": finish,
            "valid": bool(status == 200 and ntok > 0 and not err),
            "err": err}

def rank_one(model, idx, total):
    res = {}
    res["cold"] = probe(model, COLD_CEIL, "cold")
    # warm probe immediately: model should still be resident
    res["warm"] = probe(model, WARM_CEIL, "warm")
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": model,
             "cold_ttft": res["cold"]["ttft"], "cold_total": res["cold"]["total"],
             "warm_ttft": res["warm"]["ttft"], "warm_tps": res["warm"]["tps"],
             "warm_toks": res["warm"]["toks"], "valid": res["warm"]["valid"],
             "err": res["warm"]["err"] or res["cold"]["err"]}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print("[%d/%d] %-42s cold_total=%6.1fs warm_ttft=%7s tps=%6.1f valid=%s %s" % (
        idx, total, model, res["cold"]["total"],
        ("%.2f" % res["warm"]["ttft"]) if res["warm"]["ttft"] else "FAIL",
        res["warm"]["tps"], res["warm"]["valid"], entry["err"] or ""), flush=True)
    return entry

def main():
    models = loadable_models()
    print("herd-ranker: %d loadable models, %d workers, ceilings cold=%ds warm=%ds" % (
        len(models), WORKERS, COLD_CEIL, WARM_CEIL), flush=True)
    entries = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(rank_one, m, i + 1, len(models)): m for i, m in enumerate(models)}
        for fu in futs:
            try:
                entries.append(fu.result())
            except Exception as e:
                print("WORKER FAIL %s: %r" % (futs[fu], e), flush=True)
    ok = [e for e in entries if e["valid"]]
    bad = [e for e in entries if not e["valid"]]
    ok.sort(key=lambda e: (e["warm_ttft"] is None, e["warm_ttft"] or 1e9))
    ranked = ok + bad
    with open(os.path.join(OUTDIR, "ranked.json"), "w") as f:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "models": ranked}, f, indent=1)
    with open(os.path.join(OUTDIR, "ranked.md"), "w") as f:
        f.write("| rank | model | warm TTFT (s) | warm tok/s | cold total (s) | valid |\n")
        f.write("|---|---|---|---|---|---|\n")
        for i, e in enumerate(ranked, 1):
            f.write("| %d | %s | %s | %s | %s | %s |\n" % (
                i, e["model"], e["warm_ttft"], e["warm_tps"], e["cold_total"],
                "yes" if e["valid"] else "NO " + (e["err"] or "")[:60]))
    print("DONE: %d/%d valid. ranked.json + ranked.md written to %s" % (len(ok), len(entries), OUTDIR), flush=True)

if __name__ == "__main__":
    main()
