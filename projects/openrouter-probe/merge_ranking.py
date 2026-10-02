"""Build the final 10-model ranking.

The 151629 run crashed on model 9 before writing its aggregate report, so
the 8 completed models are reconstructed from their raw per-model
GuideLLM JSONs using the SAME extraction logic as eval_runner.run_model.
The 2-model remainder report (152756) is loaded as-is.
"""
import json, glob, os
import ranking_lib

D = "/home/toxic/sovereign-eval-wt/projects/openrouter-probe/"
bench = json.load(open(D + "models-bench.json"))
tokmap = {m["openrouter_id"]: m for m in bench["models"]}


def get(d, *path):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def extract(model_id, raw_path, tok_repo):
    d = json.loads(open(raw_path).read())
    b = d["benchmarks"][0]
    quality = b.get("quality") or {}
    qkey = next((k for k in quality if k.startswith("instruction_following")), None)
    q = quality.get(qkey, {}) if qkey else {}
    m = b.get("metrics") or {}
    return {
        "model": model_id,
        "tokenizer_repo": tok_repo,
        "wall_s": None,
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
    }


results = []
for raw in sorted(glob.glob(D + "eval-20260920-151629-*.json")):
    slug = os.path.basename(raw)[len("eval-20260920-151629-"):-len(".json")]
    # slug has / replaced with _ ; recover model id via manifest match
    mid = next((m for m in tokmap if m.replace("/", "_") == slug), None)
    assert mid, slug
    r = extract(mid, raw, tokmap[mid]["tokenizer_repo"] or "gpt2")
    r["status"] = "ok"
    r["free"] = tokmap[mid].get("free", True)
    r["tokenizer_status"] = tokmap[mid].get("tokenizer_status")
    results.append(r)

b = json.load(open(D + "ranking-eval-20260920-152756.json"))
for x in b["results"]:
    lat = x.get("latency_p50_s")
    print("remainder:", x["model"], x.get("status"), "q=", x.get("quality_mean"),
          "n=", x.get("quality_n"), "err=", x.get("n_errored"),
          "lat=", round(lat, 2) if lat else None)
results += b["results"]

ok_valid, fallback = ranking_lib.split_tiers(results)
ranked = ranking_lib.rank_models(ok_valid)

ts = "20260920-final"
instrument = {
    "harness": "guidellm fork toxicwind/guidellm (pluggable scorers)",
    "scorer": "instruction_following (deterministic)",
    "scorer_semantics": ("borrowed from probe_abstract.py: exact=2.0, contains=1.0, "
                          "completed-empty=0.0; transport-errored requests scored for the "
                          "record only, excluded from quality aggregates"),
    "thinking_strip": True,
    "tokenizers": "per-model HF repos (models-bench.json); openrouter/free on explicitly labelled gpt2 fallback (not tokenizer-comparable)",
    "prompt": "Output exactly: ABSTRACT-7X3Q. No other text.",
    "max_tokens": 300,
    "requests_per_model": 6,
    "profile": "synchronous",
    "formality_tier": "deterministic-instrument",
    "scope": ("provider-free OpenRouter models, abstract instruction-following task; "
              "10 models across two runs (8 x 20260920-151629 reconstructed from raw "
              "per-model JSON after the runner crashed on model 9's null-content "
              "liveness probe — since fixed — plus 2 x 20260920-152756); same prompt, "
              "profile, n=6; free status verified live against the OpenRouter "
              "catalogue (446 models, 24 provider-free)"),
    "ranking_rule": "quality desc, provider-free desc, latency p50 asc",
}
report = ranking_lib.build_report(ts, instrument, results)
rp = D + "ranking-eval-%s.json" % ts
json.dump(report, open(rp, "w"), indent=1)

md = ranking_lib.render_markdown(
    title="# Eval ranking %s — final, 10 models (2026-09-20)" % ts,
    header_lines=[
        "Instrument: GuideLLM fork (`toxicwind/guidellm`) + deterministic "
        "`instruction_following` scorer (sentinel `ABSTRACT-7X3Q`, thinking-strip "
        "on), real per-model HF tokenizers.",
        "Prompt: `Output exactly: ABSTRACT-7X3Q. No other text.` — 6 requests/model, "
        "synchronous profile, max_tokens=300.",
        "Ranking: quality mean desc, provider-free desc, latency p50 asc.",
        "Quality aggregates cover COMPLETED requests only; transport-errored "
        "requests are scored for the record and excluded from quality means "
        "(provider failures are reliability signal, not quality signal).",
        "Free status verified live against the OpenRouter catalogue (446 models, "
        "24 provider-free at run time).",
    ],
    ranked=ranked,
    fallback=fallback,
    dead_or_errored=report["dead_or_errored"],
    notes=[
        "`openrouter/free` has no stable tokenizer; it ran on the explicitly "
        "labelled `gpt2` fallback and is NOT tokenizer-comparable with the rest.",
        "`nvidia/nemotron-3-super-120b-a12b:free`: 3/6 requests errored at the "
        "provider (excluded from the quality mean); quality 2.0 over 3 completed.",
        "`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`: 1/6 errored; "
        "quality 2.0 over 5 completed.",
        "14 live-free models lack tokenizer mappings and were not probed "
        "(see run logs).",
        "Raw per-model GuideLLM JSON: `eval-<ts>-<model>.json` in this directory.",
        "Preliminary sweep `20260920-150006` (pre-fix fork code) is superseded "
        "by this ranking and not committed.",
    ],
)
mp = D + "RANKING-eval-%s.md" % ts
open(mp, "w").write(md)
print("wrote", rp, "and", mp)
print(json.dumps(report["ranking"], indent=1))
