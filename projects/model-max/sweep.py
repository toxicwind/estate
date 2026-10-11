#!/usr/bin/env python3
"""
MODEL-MAX sweep harness — measures every model exposed by the herd gateway.

Runs ON YOTE (local to the herd at 127.0.0.1:25100). Stdlib only.

Phases:
  liveness  - one real completion per model, fail-fast. Classifies healthy vs
              dead and captures error classes (incl. SEMANTIC failures: HTTP 200
              bodies carrying error text, empty completions, canned notices).
  deep      - for healthy models only: streaming probes measuring TTFT, total
              latency, tokens/sec, p50s, plus a 3-way concurrent burst for a
              measured valid-RPM and an ok-rate under load.
  report    - writes /home/toxic/sovereign/data/model-health.json

Usage:
  sweep.py [--phase liveness|deep|report|all] [--models id1,id2] [--workdir DIR]

Re-running is one command:  python3 sweep.py --phase all
"""
import json, time, sys, os, math, random
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "http://127.0.0.1:25100"
WORKDIR = os.environ.get("MODEL_MAX_WORKDIR", "/home/toxic/sovereign/projects/model-max")
HEALTH_JSON = "/home/toxic/sovereign/data/model-health.json"
PROMPT = "Reply with exactly: OK"
MAX_TOKENS = 64
WORKERS_LOCAL = 2
WORKERS_CLOUD = 8

CLOUD_PREFIXES = ("flock-direct/", "mistral/", "gemini/", "openrouter-free/",
                  "openrouter-ling/", "toolcall-local/", "moonshot/")
CLOUD_EXACT = {"kimi-auto"}

# Substrings (lowercased) that mark a completion as a SEMANTIC failure even
# when HTTP status is 200. Never cache or trust these as real output.
SEMANTIC_DENY = [
    "not enough credits", "insufficient credits", "insufficient_quota",
    "insufficient balance", "a valid api key is required", "invalid api key",
    "incorrect api key", "user not found", "queue full", "function-not-found",
    "model is unavailable", "unavailable for free", "no healthy candidate",
    "no healthy upstream", "no valid bids", "internal server error",
    "upstream error", "bad gateway", "service unavailable", "rate limit",
    "overloaded", "try again later", "temporarily unavailable",
    "context length", "max tokens", "content filter", "flagged",
]


def classify(model_id):
    """-> (provider, lane). lane is 'local' (llama-swap GPU) or 'cloud'."""
    if model_id.startswith(CLOUD_PREFIXES) or model_id in CLOUD_EXACT:
        if model_id.startswith("flock-direct/"):
            provider = "flock-direct"
        elif model_id.startswith("mistral/"):
            provider = "mistral"
        elif model_id.startswith("gemini/"):
            provider = "gemini"
        elif model_id.startswith("openrouter-free/"):
            provider = "openrouter"
        elif model_id.startswith("openrouter-ling/"):
            provider = "openrouter"
        elif model_id.startswith("toolcall-local/"):
            provider = "toolcall-local"
        elif model_id.startswith("moonshot/"):
            provider = "moonshot"
        else:
            provider = "kimi-auto-shim"
        return provider, "cloud"
    head = model_id.split("/")[0]
    if head in ("beellama", "ik_llama"):
        provider = head
    elif model_id.startswith("qwen/") or head == "qwen":
        provider = "qwen-local"
    elif head in ("mn", "mn-grand-23b"):
        provider = "mn-local"
    elif head in ("mradermacher", "jackrong"):
        provider = "community-gguf"
    else:
        provider = "local-alias"
    return provider, "local"


def _post(path, payload, timeout, stream=False):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={"Content-Type": "application/json",
                 "Accept": "text/event-stream" if stream else "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)


def semantic_hit(text):
    t = (text or "").lower()
    return next((s for s in SEMANTIC_DENY if s in t), None)


def probe_liveness(model_id, timeout):
    """One non-streaming completion. Returns a result dict."""
    t0 = time.time()
    res = {"id": model_id}
    try:
        with _post("/v1/chat/completions",
                   {"model": model_id,
                    "messages": [{"role": "user", "content": PROMPT}],
                    "max_tokens": MAX_TOKENS, "temperature": 0,
                    "stream": False}, timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            http = r.status
    except urllib.error.HTTPError as e:
        ms = (time.time() - t0) * 1000
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            detail = ""
        hit = semantic_hit(detail)
        return {**res, "http": e.code, "latency_ms": round(ms, 1),
                "healthy": False,
                "error_class": f"http_{e.code}",
                "notes": (f"semantic:{hit} " if hit else "") + detail[:150]}
    except TimeoutError:
        ms = (time.time() - t0) * 1000
        return {**res, "http": None, "latency_ms": round(ms, 1),
                "healthy": False, "error_class": "timeout",
                "notes": f"no response in {timeout}s"}
    except Exception as e:
        ms = (time.time() - t0) * 1000
        return {**res, "http": None, "latency_ms": round(ms, 1),
                "healthy": False, "error_class": "connection",
                "notes": f"{type(e).__name__}: {str(e)[:150]}"}
    ms = (time.time() - t0) * 1000
    try:
        d = json.loads(raw)
    except Exception:
        return {**res, "http": http, "latency_ms": round(ms, 1),
                "healthy": False, "error_class": "semantic",
                "notes": "non-JSON 200 body: " + raw[:150]}
    if isinstance(d, dict) and d.get("error"):
        err = d["error"]
        detail = (err.get("message") if isinstance(err, dict) else str(err)) or ""
        return {**res, "http": http, "latency_ms": round(ms, 1),
                "healthy": False, "error_class": "semantic",
                "notes": "200+error body: " + str(detail)[:150]}
    ch = (d.get("choices") or [{}])[0]
    content = ((ch.get("message") or {}).get("content") or "").strip()
    hit = semantic_hit(content)
    if hit:
        return {**res, "http": http, "latency_ms": round(ms, 1),
                "healthy": False, "error_class": "semantic",
                "notes": f"canned failure text ({hit}): " + content[:150]}
    if not content:
        return {**res, "http": http, "latency_ms": round(ms, 1),
                "healthy": False, "error_class": "empty",
                "notes": f"200 but empty content (finish={ch.get('finish_reason')})"}
    return {**res, "http": http, "latency_ms": round(ms, 1),
            "healthy": True, "error_class": "ok",
            "content_head": content[:60], "notes": ""}


def probe_streaming(model_id, timeout=90, deadline=150):
    """One streaming completion. Returns (ttft_ms, total_ms, out_tokens, ok, note).
    deadline = wall-clock ceiling for the whole stream (slow-token streams
    defeat per-recv socket timeouts)."""
    t0 = time.time()
    ttft = None
    content_parts = []
    out_tokens = None
    try:
        with _post("/v1/chat/completions",
                   {"model": model_id,
                    "messages": [{"role": "user", "content": PROMPT}],
                    "max_tokens": 64, "temperature": 0,
                    "stream": True, "stream_options": {"include_usage": True}},
                   timeout, stream=True) as r:
            for raw_line in r:
                if time.time() - t0 > deadline:
                    break
                line = raw_line.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    d = json.loads(data)
                except Exception:
                    continue
                if isinstance(d, dict) and d.get("error"):
                    return None, (time.time() - t0) * 1000, 0, False, "stream error chunk"
                usage = (d.get("usage") or {})
                if usage.get("completion_tokens"):
                    out_tokens = usage["completion_tokens"]
                delta = (((d.get("choices") or [{}])[0].get("delta")) or {})
                piece = delta.get("content") or ""
                if piece and ttft is None:
                    ttft = (time.time() - t0) * 1000
                content_parts.append(piece)
    except Exception as e:
        return None, (time.time() - t0) * 1000, 0, False, f"{type(e).__name__}"
    total = (time.time() - t0) * 1000
    content = "".join(content_parts).strip()
    if semantic_hit(content):
        return ttft, total, out_tokens or 0, False, "semantic in stream"
    if not content:
        # streaming unsupported or empty -> fall back to non-streaming sample
        fb = probe_liveness(model_id, timeout)
        if fb["healthy"]:
            return None, fb["latency_ms"], 8, True, "non-stream fallback"
        return None, total, 0, False, "empty stream"
    if out_tokens is None:
        out_tokens = max(1, len(content.split()))
    return ttft, total, out_tokens, True, ""


def p50(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = min(len(xs) - 1, int(0.5 * len(xs)))
    return round(xs[i], 1)


def p95(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = min(len(xs) - 1, int(0.95 * len(xs)))
    return round(xs[i], 1)


def deep_probe(model_id):
    """6 sequential streaming samples + one 3-way burst. Returns metrics dict."""
    samples = []
    for _ in range(6):
        ttft, total, toks, ok, note = probe_streaming(model_id)
        samples.append((ttft, total, toks, ok))
    ok_s = [s for s in samples if s[3]]
    # burst: 3 concurrent, single round
    b_t0 = time.time()
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(probe_streaming, model_id) for _ in range(3)]
        b_res = [f.result() for f in futs]
    b_wall = (time.time() - b_t0)
    b_ok = sum(1 for r in b_res if r[3])
    all_ok = ok_s + [r for r in b_res if r[3]]
    totals = [s[1] for s in all_ok]
    ttfts = [s[0] for s in all_ok if s[0] is not None]
    toks = [s[2] for s in all_ok if s[2]]
    tps = (sum(toks) / (sum(totals) / 1000)) if toks and totals else None
    elapsed_min = max(b_wall, sum(s[1] for s in samples) / 1000) / 60
    valid_rpm = round(len(all_ok) / elapsed_min, 1) if elapsed_min > 0 else None
    return {
        "ttft_ms_p50": p50(ttfts),
        "total_ms_p50": p50(totals),
        "total_ms_p95": p95(totals),
        "tps": round(tps, 1) if tps else None,
        "valid_rpm": valid_rpm,
        "burst_ok": f"{b_ok}/3",
        "deep_ok_rate": f"{len(ok_s)}/6",
        "deep_notes": "" if len(ok_s) == 6 and b_ok == 3
                      else f"flaky: {len(ok_s)}/6 seq, {b_ok}/3 burst",
    }


def fetch_models():
    with urllib.request.urlopen(BASE + "/v1/models", timeout=20) as r:
        d = json.load(r)
    return sorted(m["id"] for m in d.get("data", []))


def run_phase_liveness(model_ids, checkpoint_path):
    results = {}
    if os.path.exists(checkpoint_path):
        try:
            results = json.load(open(checkpoint_path))
            print(f"[liveness] resumed: {len(results)} already probed", flush=True)
        except Exception:
            results = {}
    todo = [m for m in model_ids if m not in results]

    def save():
        with open(checkpoint_path, "w") as f:
            json.dump(results, f, indent=1)

    def task(mid):
        provider, lane = classify(mid)
        timeout = 180 if lane == "local" else 60
        r = probe_liveness(mid, timeout)
        r["provider"] = provider
        r["lane"] = lane
        r["last_checked"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        return mid, r

    # local GPU lane and cloud lane get separate pools: the 3090 must not thrash
    groups = {"local": [m for m in todo if classify(m)[1] == "local"],
              "cloud": [m for m in todo if classify(m)[1] == "cloud"]}
    for lane, mids in groups.items():
        if not mids:
            continue
        workers = WORKERS_LOCAL if lane == "local" else WORKERS_CLOUD
        print(f"[liveness] lane={lane} models={len(mids)} workers={workers}", flush=True)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(task, m): m for m in mids}
            for f in as_completed(futs):
                mid, r = f.result()
                results[mid] = r
                save()  # checkpoint every model: progress is never lost
                flag = "OK " if r["healthy"] else "FAIL"
                print(f"  [{flag}] {mid} http={r['http']} "
                      f"{r.get('latency_ms', '-')}ms {r['error_class']} "
                      f"{r.get('notes', '')[:80]}", flush=True)
    return results


def run_phase_deep(liveness, checkpoint_path):
    healthy = [mid for mid, r in liveness.items() if r["healthy"]]
    deep = {}
    if os.path.exists(checkpoint_path):
        try:
            deep = json.load(open(checkpoint_path))
            print(f"[deep] resumed: {len(deep)} already deep-probed", flush=True)
        except Exception:
            deep = {}
    todo = [m for m in healthy if m not in deep]
    print(f"[deep] {len(todo)} healthy models to probe, 2 workers", flush=True)

    def save():
        with open(checkpoint_path, "w") as f:
            json.dump(deep, f, indent=1)

    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(deep_probe, m): m for m in todo}
        for f in as_completed(futs):
            mid = futs[f]
            try:
                deep[mid] = f.result()
                d = deep[mid]
                save()  # checkpoint every model
                print(f"  [deep] {mid} ttft={d['ttft_ms_p50']}ms "
                      f"total_p50={d['total_ms_p50']}ms tps={d['tps']} "
                      f"rpm~{d['valid_rpm']} burst={d['burst_ok']} {d['deep_notes']}",
                      flush=True)
            except Exception as e:
                deep[mid] = {"deep_error": f"{type(e).__name__}: {e}"}
                save()
                print(f"  [deep] {mid} ERROR {e}", flush=True)
    return deep


SCHEMA_DOC = (
    "model-health v1 — measured by MODEL-MAX sweep.py (toxicwind). "
    "healthy=true means a real completion was observed during the sweep window; "
    "anything else is guilty-until-proven-innocent. "
    "error_class: ok | http_<code> | timeout | connection | semantic | empty. "
    "semantic = HTTP 200 carrying error/canned text (never trust the body). "
    "latency_ms_p50 = phase-1 wall clock for one tiny completion. "
    "ttft_ms_p50/total_ms_p50/tps = phase-2 streaming medians (null if not deep-probed). "
    "valid_rpm = successful completions per minute actually observed during the "
    "deep window (6 sequential + 3-burst); an observed rate, not a claimed limit. "
    "Feed this into herd racing / robust.py / Tau; quarantine anything not healthy."
)


def write_report(liveness, deep):
    models = {}
    for mid, r in liveness.items():
        d = deep.get(mid, {})
        models[mid] = {
            "id": mid,
            "provider": r["provider"],
            "lane": r["lane"],
            "healthy": r["healthy"],
            "http": r["http"],
            "error_class": r["error_class"],
            "latency_ms_p50": r.get("latency_ms"),
            "ttft_ms_p50": d.get("ttft_ms_p50"),
            "total_ms_p50": d.get("total_ms_p50"),
            "total_ms_p95": d.get("total_ms_p95"),
            "tps": d.get("tps"),
            "valid_rpm": d.get("valid_rpm"),
            "burst_ok": d.get("burst_ok"),
            "last_checked": r["last_checked"],
            "notes": "; ".join(x for x in
                               [r.get("notes", ""), d.get("deep_notes", ""),
                                d.get("deep_error", "")] if x),
        }
    n_ok = sum(1 for r in liveness.values() if r["healthy"])
    out = {
        "_schema": SCHEMA_DOC,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "gateway": BASE,
        "sweep": {"total": len(liveness), "healthy": n_ok,
                  "dead": len(liveness) - n_ok,
                  "deep_probed": len(deep)},
        "models": models,
    }
    os.makedirs(os.path.dirname(HEALTH_JSON), exist_ok=True)
    with open(HEALTH_JSON, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {HEALTH_JSON}: {n_ok}/{len(liveness)} healthy")
    return out


def main():
    args = sys.argv[1:]
    phase = "all"
    only = None
    fresh = False
    global MAX_TOKENS, WORKERS_LOCAL, WORKERS_CLOUD
    for a in args:
        if a.startswith("--phase="):
            phase = a.split("=", 1)[1]
        elif a.startswith("--models="):
            only = a.split("=", 1)[1].split(",")
        elif a == "--fresh":
            fresh = True
        elif a.startswith("--max-tokens="):
            MAX_TOKENS = int(a.split("=", 1)[1])
        elif a.startswith("--workers-local="):
            WORKERS_LOCAL = int(a.split("=", 1)[1])
        elif a.startswith("--workers-cloud="):
            WORKERS_CLOUD = int(a.split("=", 1)[1])
    os.makedirs(WORKDIR, exist_ok=True)
    model_ids = fetch_models()
    if only:
        model_ids = [m for m in model_ids if m in only]
    print(f"models: {len(model_ids)} from {BASE}/v1/models", flush=True)
    with open(f"{WORKDIR}/model-ids.json", "w") as f:
        json.dump(model_ids, f)

    ckpt = f"{WORKDIR}/phase1.json"
    if fresh and os.path.exists(ckpt):
        os.remove(ckpt)
    liveness, deep = {}, {}
    if phase in ("liveness", "all"):
        liveness = run_phase_liveness(model_ids, ckpt)
    elif phase in ("deep", "report"):
        liveness = json.load(open(ckpt))
    if phase in ("deep", "all"):
        if only:
            liveness = {m: r for m, r in liveness.items() if m in only}
        deep = run_phase_deep(liveness, f"{WORKDIR}/phase2.json")
    elif phase == "report":
        deep = json.load(open(f"{WORKDIR}/phase2.json"))
    if phase in ("report", "all"):
        write_report(liveness, deep)


if __name__ == "__main__":
    main()
