"""Isolate openrouter/free into a non-comparable fallback tier.

Governing rule: openrouter/free has no stable tokenizer (gpt2 fallback) and
must never appear in the numbered tokenizer-valid ranking. Moves it out of
`ranking` into a top-level `fallback_tier` entry carrying its full result
dict + a note. Regenerates the Markdown with 9 ranked rows + a fallback
section.
"""
import json

DIR = "/home/toxic/sovereign-eval-wt/projects/openrouter-probe"
JP = DIR + "/ranking-eval-20260920-final.json"
MP = DIR + "/RANKING-eval-20260920-final.md"

d = json.load(open(JP))

if d.get("fallback_tier"):
    print("fallback_tier already present; regenerating Markdown only")
    fr = d["fallback_tier"][0]["result"]
else:
    fallback_results = [r for r in d["results"] if r["model"] == "openrouter/free"]
    assert len(fallback_results) == 1, "expected exactly one openrouter/free result"
    fr = fallback_results[0]

    d["ranking"] = [m for m in d["ranking"] if m != "openrouter/free"]
    assert len(d["ranking"]) == 9, d["ranking"]
    d["results"] = [r for r in d["results"] if r["model"] != "openrouter/free"]
    assert len(d["results"]) == 9, len(d["results"])

    d["fallback_tier"] = [
        {
            "model": fr["model"],
            "tokenizer_repo": fr.get("tokenizer_repo", "gpt2"),
            "note": (
                "No stable tokenizer for openrouter/free; ran on the explicitly "
                "labelled gpt2 fallback. Token counts and any tokenizer-derived "
                "metrics are NOT comparable with the ranked tier. Scores from "
                "deterministic instruction-following are still reported for the "
                "record."
            ),
            "result": fr,
        }
    ]
    inst = d.get("instrument", {})
    if isinstance(inst, dict):
        inst["tier_note"] = (
            "Ranked tier: 9 models with real per-model HF tokenizers. "
            "openrouter/free reported separately in fallback_tier (gpt2 fallback, "
            "non-comparable)."
        )
    else:
        d["instrument"] = inst + (
            " Ranked tier: 9 models with real per-model HF tokenizers. "
            "openrouter/free reported separately in fallback_tier (gpt2 fallback, "
            "non-comparable)."
        )

    json.dump(d, open(JP, "w"), indent=1, sort_keys=True)
    print("JSON rewritten:", JP)

# --- Markdown (iterate in RANKING order, not results order) ---
by_model = {r["model"]: r for r in d["results"]}
rows = []
for i, model in enumerate(d["ranking"], 1):
    r = by_model[model]
    rows.append(
        f"| {i} | {r['model']} | {r['quality_mean']:.2f} | "
        f"{int(r['quality_n'])} | {int(r['n_errored'])} | "
        f"{r['latency_p50_s']:.2f} | {r['ttft_p50_ms']:.0f} | "
        f"{r['output_tps']:.1f} | {r.get('tokenizer_repo', '')} |"
    )

md = f"""# Eval ranking 20260920-final — 9 ranked models + 1 fallback (2026-09-20)

Instrument: GuideLLM fork (`toxicwind/guidellm`) + deterministic `instruction_following` scorer (sentinel `ABSTRACT-7X3Q`, thinking-strip on), real per-model HF tokenizers.
Prompt: `Output exactly: ABSTRACT-7X3Q. No other text.` — 6 requests/model, synchronous profile, max_tokens=300.
Ranking: quality mean desc, provider-free desc, latency p50 asc.
Quality aggregates cover COMPLETED requests only; transport-errored requests are scored for the record and excluded from quality means (provider failures are reliability signal, not quality signal).
Free status verified live against the OpenRouter catalogue (446 models, 24 provider-free at run time).

| rank | model | quality mean | n | err | lat p50 (s) | ttft p50 (ms) | out tok/s | tokenizer |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## Fallback tier — NOT ranked (no stable tokenizer)

`openrouter/free` has no stable tokenizer; it ran on the explicitly labelled `gpt2` fallback and is NOT tokenizer-comparable with the ranked tier. Its deterministic quality score is reported for the record only.

| model | quality mean | n | err | lat p50 (s) | ttft p50 (ms) | out tok/s | tokenizer |
|---|---|---|---|---|---|---|---|
| openrouter/free | {fr['quality_mean']:.2f} | {int(fr['quality_n'])} | {int(fr['n_errored'])} | {fr['latency_p50_s']:.2f} | {fr['ttft_p50_ms']:.0f} | {fr['output_tps']:.1f} | gpt2 (fallback) |

## Notes
- `nvidia/nemotron-3-super-120b-a12b:free`: 3/6 requests errored at the provider (excluded from the quality mean); quality 2.0 over 3 completed.
- `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`: 1/6 errored; quality 2.0 over 5 completed.
- 14 live-free models lack tokenizer mappings and were not probed (see run logs).
- Raw per-model GuideLLM JSON: `eval-<ts>-<model>.json` in this directory.
- Preliminary sweep `20260920-150006` (pre-fix fork code) is superseded by this ranking and not committed.
"""
open(MP, "w").write(md)
print("MD rewritten:", MP)
