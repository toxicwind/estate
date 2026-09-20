#!/usr/bin/env python3
"""eval_runner.py -- maximal referenced evaluation: GuideLLM + deterministic
instruction-following scoring over provider-free OpenRouter models.

Instrument: guidellm fork (toxicwind/guidellm) pluggable scorers,
  scorer=instruction_following (deterministic, borrowed from probe_abstract.py),
  thinking-block stripping on, real per-model HF tokenizers (no gpt2 fallback
  except where explicitly labeled).
Ranking: quality desc, provider-free status, latency p50 asc.

Reads OPENROUTER_API_KEY_FREE from /home/toxic/.secrets IN-PROCESS.
Key NEVER printed or logged (sanitize defense).

Usage: /home/toxic/.venv-guidellm/bin/python3 eval_runner.py [--models a,b] [--n 6]
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

import ranking_lib  # shared tier/ranking/report logic
from ranking_lib import split_tiers, rank_models

sys.path.insert(0, "/home/toxic/sovereign/projects/guidellm/src")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

SECRETS = "/home/toxic/.secrets"
HERE = os.path.dirname(os.path.abspath(__file__))
BENCH_JSON = os.path.join(HERE, "models-bench.json")
OUTDIR = HERE
BASE = "https://openrouter.ai/api/v1"
KEY_NAME = "OPENROUTER_API_KEY_FREE"
PROMPT = "Output exactly: ABSTRACT-7X3Q. No other text."
SENTINEL = "ABSTRACT-7X3Q"
MAX_TOKENS = 300  # reasoning headroom (north-mini-code truncates at 50)
TIMEOUT = 90


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
                 "X-Title": "sovereign-eval"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode()), (time.time() - t0) * 1000, None
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()[:160]
        except Exception:
            detail = ""
        return e.code, None, (time.time() - t0) * 1000, sanitize(detail)
    except Exception as e:
        return -1, None, (time.time() - t0) * 1000, sanitize(str(e)[:160])


def live_probe(model_id):
    """One cheap abstract request. Returns (alive, http, ms, err)."""
    st, data, ms, err = api("/chat/completions", {
        "model": model_id, "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": MAX_TOKENS, "temperature": 0}, timeout=60)
    content = ((data or {}).get("choices") or [{}])[0].get("message", {}).get("content")
    ok = st == 200 and bool((content or "").strip())
    return ok, st, round(ms, 1), err


def discover_free_models(timeout=60):
    """Live OpenRouter catalogue -> set of provider-free model ids.

    Free = pricing.prompt == 0 and pricing.completion == 0 (string or
    numeric). No auth required. Returns (free_ids, total_count, error).
    """
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"HTTP-Referer": "https://sovereign.local",
                 "X-Title": "sovereign-eval"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read().decode())
    except Exception as e:
        return set(), 0, sanitize(str(e)[:160])
    free = set()
    models = payload.get("data") or []
    for m in models:
        pr = (m.get("pricing") or {})
        try:
            p0 = float(pr.get("prompt", "nan"))
            c0 = float(pr.get("completion", "nan"))
        except (TypeError, ValueError):
            continue
        if p0 == 0.0 and c0 == 0.0 and m.get("id"):
            free.add(m["id"])
    return free, len(models), None


def get(d, *path):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


async def run_model(model_id, tok_repo, n, out_json):
    from guidellm.schemas.benchmark.entrypoints import BenchmarkArgs, BenchmarkScenario
    from guidellm.benchmark.entrypoints import benchmark_generative_text

    args = BenchmarkScenario(
        spec=BenchmarkArgs(
            backend={
                "kind": "openai_http",
                "target": "https://openrouter.ai/api/v1",
                "model": model_id,
                "api_key": KEY,
                "validate_backend": False,
                "max_tokens": MAX_TOKENS,
            },
            data=[{
                "kind": "in_memory_dict_list",
                "data": [{"prompt": PROMPT} for _ in range(n)],
            }],
            profile={"kind": "synchronous"},
            tokenizer={"kind": "huggingface_auto", "model": tok_repo},
            metrics={
                "kind": "generative",
                "scorers": ["instruction_following"],
                "scorer_config": {
                    "instruction_following": {
                        "sentinel": SENTINEL,
                        "strip_thinking": True,
                    }
                },
            },
            outputs=[{"kind": "json", "path": out_json}],
            constraints=[{"kind": "max_requests", "count": n}],
        )
    )
    t0 = time.time()
    report, _ = await benchmark_generative_text(args)
    wall_s = round(time.time() - t0, 1)
    d = json.loads(open(out_json).read())
    b = d["benchmarks"][0]
    quality = b.get("quality") or {}
    qkey = next((k for k in quality if k.startswith("instruction_following")), None)
    q = quality.get(qkey, {}) if qkey else {}
    m = b.get("metrics") or {}
    return {
        "model": model_id,
        "tokenizer_repo": tok_repo,
        "wall_s": wall_s,
        "quality_mean": q.get("mean"),
        "quality_min": q.get("min"),
        "quality_max": q.get("max"),
        "quality_n": q.get("n"),
        "quality_key": qkey,
        "latency_p50_s": get(m, "request_latency", "successful", "percentiles", "p50"),
        "ttft_p50_ms": get(m, "time_to_first_token_ms", "successful", "percentiles", "p50"),
        "output_tps": get(m, "output_tokens_per_second", "successful", "mean"),
        "prompt_tok_mean": get(m, "text", "tokens", "input", "total", "mean"),
        "output_tok_mean": get(m, "text", "tokens", "output", "total", "mean"),
        "n_successful": len((b.get("requests") or {}).get("successful") or []),
        "n_errored": len((b.get("requests") or {}).get("errored") or []),
        "instrument": b.get("quality_instrument"),
        "guidellm_json": out_json,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="")
    ap.add_argument("--n", type=int, default=6)
    a = ap.parse_args()
    only = {m.strip() for m in a.models.split(",") if m.strip()}

    bench = json.load(open(BENCH_JSON))
    models = bench["models"]
    if only:
        models = [m for m in models if m["openrouter_id"] in only]

    live_free, catalogue_n, derr = discover_free_models()
    if derr:
        print(f"[eval] WARNING: live catalogue unreachable ({derr}); "
              f"falling back to manifest free labels", flush=True)
        live_free = None
    else:
        print(f"[eval] live catalogue: {catalogue_n} models, "
              f"{len(live_free)} provider-free", flush=True)
        manifest_ids = {m["openrouter_id"] for m in models}
        not_free = sorted(manifest_ids - live_free)
        for mid in not_free:
            print(f"[eval] SKIP {mid}: not provider-free in live catalogue",
                  flush=True)
        models = [m for m in models if m["openrouter_id"] in live_free]
        unmapped = sorted(live_free - manifest_ids)
        if unmapped:
            print(f"[eval] note: {len(unmapped)} live-free models lack "
                  f"tokenizer mappings (not probed): "
                  f"{', '.join(unmapped[:8])}"
                  f"{'...' if len(unmapped) > 8 else ''}", flush=True)

    ts = time.strftime("%Y%m%d-%H%M%S")
    print(f"[eval] {len(models)} models x {a.n} requests, ts={ts}", flush=True)

    results = []
    for i, m in enumerate(models):
        mid = m["openrouter_id"]
        print(f"[eval {i+1}/{len(models)}] liveness {mid}", flush=True)
        alive, http, ms, err = live_probe(mid)
        if not alive:
            print(f"[eval] SKIP {mid} http={http} err={err}", flush=True)
            results.append({"model": mid, "status": "dead",
                            "http": http, "error": err,
                            "free": (mid in live_free) if live_free is not None else m.get("free", True)})
            continue
        tok = m["tokenizer_repo"] or "gpt2"
        out_json = os.path.join(OUTDIR, f"eval-{ts}-{mid.replace('/', '_')}.json")
        print(f"[eval] RUN {mid} tok={tok}", flush=True)
        try:
            r = asyncio.run(run_model(mid, tok, a.n, out_json))
            r["status"] = "ok"
            r["free"] = (mid in live_free) if live_free is not None else m.get("free", True)
            r["tokenizer_status"] = m.get("tokenizer_status")
            print(f"[eval] DONE {mid} q={r['quality_mean']} n={r['quality_n']} "
                  f"err={r['n_errored']} lat_p50={r['latency_p50_s']} "
                  f"wall={r['wall_s']}s", flush=True)
        except Exception as e:
            print(f"[eval] FAIL {mid}: {sanitize(str(e)[:200])}", flush=True)
            r = {"model": mid, "status": "error",
                 "error": sanitize(str(e)[:200]), "free": m.get("free", True)}
        results.append(r)

    ok_valid, fallback = split_tiers(results)
    ranked = rank_models(ok_valid)
    instrument = {
            "harness": "guidellm fork toxicwind/guidellm (pluggable scorers)",
            "scorer": "instruction_following (deterministic)",
            "scorer_semantics": "borrowed from probe_abstract.py: exact=2.0, contains=1.0, completed-empty=0.0; transport-errored requests scored for the record only, excluded from quality aggregates (provider failures are reliability signal, not quality signal)",
            "thinking_strip": True,
            "tokenizers": "per-model HF repos (models-bench.json); fallbacks labeled",
            "prompt": PROMPT,
            "max_tokens": MAX_TOKENS,
            "requests_per_model": a.n,
            "profile": "synchronous",
            "formality_tier": "deterministic-instrument",
            "scope": "provider-free OpenRouter models, abstract instruction-following task",
            "ranking_rule": "quality desc, provider-free desc, latency p50 asc",
    }

    report = ranking_lib.build_report(ts, instrument, results)
    rp = os.path.join(OUTDIR, f"ranking-eval-{ts}.json")
    json.dump(report, open(rp, "w"), indent=1)
    md = ranking_lib.render_markdown(
        title=f"# Eval ranking {ts}",
        header_lines=[
            f"Instrument: GuideLLM fork + deterministic `instruction_following` scorer "
            f"(sentinel `{SENTINEL}`, thinking-strip on), real per-model tokenizers.",
            f"Prompt: `{PROMPT}` — {a.n} requests/model, synchronous profile.",
            f"Ranking: quality desc, provider-free, latency p50 asc.",
        ],
        ranked=ranked,
        fallback=fallback,
        dead_or_errored=report["dead_or_errored"],
        dead_lines=[
            f"- {r['model']}: {r.get('status')} {r.get('http', '')} {r.get('error', '')}"
            for r in report["dead_or_errored"]
        ] or None,
    )
    mp = os.path.join(OUTDIR, f"RANKING-eval-{ts}.md")
    open(mp, "w").write(md)
    print(f"[eval] wrote {rp} and {mp}", flush=True)
    print(json.dumps(report["ranking"], indent=1))


if __name__ == "__main__":
    main()
