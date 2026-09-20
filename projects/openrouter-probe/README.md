# openrouter-probe — GuideLLM quality-first eval stack

Deterministic instruction-following evaluation of provider-free OpenRouter
models, run **through the GuideLLM fork** (`toxicwind/guidellm`), not a
parallel harness. Ranking rule: **quality first, provider-free status
second, GuideLLM-measured performance third.**

## Components

| File | Role |
|---|---|
| `eval_runner.py` | **The runner (permanent).** Discovers live provider-free models from the OpenRouter catalogue, liveness-probes each, runs 6 synchronous GuideLLM requests per model with the deterministic `instruction_following` scorer (sentinel `ABSTRACT-7X3Q`, thinking-strip on) and per-model real HF tokenizers, then writes raw per-model JSON + aggregate ranking JSON/Markdown. |
| `models-bench.json` | OpenRouter model → HF tokenizer repo manifest. `openrouter/free` has no stable tokenizer (explicitly labelled `gpt2` fallback, not tokenizer-comparable). |
| `ranking-eval-<ts>.json` / `RANKING-eval-<ts>.md` | Aggregate reports. Each names its instrument: scorer, semantics, tokenizer policy, scope, formality tier, prompt, timestamp. |
| `eval-<ts>-<model>.json` | Raw per-model GuideLLM reports (with `scores`/`score_details` per request, `quality`/`quality_instrument` at benchmark level). |
| `probe_abstract.py` | Original abstract probe. Semantics borrowed by the fork's scorer (exact `ABSTRACT-7X3Q` = 2.0, contains = 1.0, missing/empty = 0.0). Kept as reference; ranking runs through the fork. |
| `probe_all.py`, `deep_pass.py`, `guidellm_sweep.sh` | Legacy sweep tooling (key: `OPENROUTER_API_KEY_FREE`). |

## Running

```bash
# yote, from this directory:
/home/toxic/.venv-guidellm/bin/python3 eval_runner.py            # all manifest models
/home/toxic/.venv-guidellm/bin/python3 eval_runner.py --models "a/b:free,c/d:free" --n 6
```

The runner reads `OPENROUTER_API_KEY_FREE` from the environment (never
logged). GuideLLM source: `/home/toxic/sovereign/projects/guidellm`
(remote `toxicwind/guidellm`).

## Latest ranking

`RANKING-eval-20260920-final.md` — 10 provider-free models, 6 requests
each, prompt `Output exactly: ABSTRACT-7X3Q. No other text.`
Leader: `nex-agi/nex-n2.5-mini:free` (quality 2.0, fastest p50).

## Semantics (quality policy)

- Every terminal request is scored for its per-request record.
- Completed requests with empty output score `0.0` (model silence is data).
- Scorer exceptions record `0.0` + error metadata, never abort the run.
- **Quality aggregates cover completed requests only.** Provider/transport
  failures (429, overload, ResourceExhausted) are reliability signal, not
  instruction-following signal, and do not move quality means.
- Deterministic instrument only; LLM-as-judge is out of scope for this tier.

## Links

- Fork: [toxicwind/guidellm](https://github.com/toxicwind/guidellm) —
  pluggable scoring (`src/guidellm/benchmark/scoring/`), README documents
  the scoring feature.
- Upstream: [vllm-project/guidellm](https://github.com/vllm-project/guidellm)
- Eval plan: `GUIDELLM_EVAL_PLAN.md` (in this directory)
- Fleet knowledgebase: `docs/fleet-knowledgebase.md`
  ([canonical](https://github.com/toxicwind/sovereign-projects/blob/main/docs/fleet-knowledgebase.md))
- Papers: Zheng et al. arXiv `2306.05685`; *LLM Judges Have Dark Current*
  arXiv `2606.15610`; *Judging LLM-as-a-Judge* arXiv `2609.02942`;
  *Evaluation Scores Are Perishable Knowledge Claims* arXiv `2607.26191`;
  *RouteBalance* arXiv `2606.17949`; *RouterWise* arXiv `2604.10907`
