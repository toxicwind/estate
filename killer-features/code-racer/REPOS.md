# code-racer — vendored repo research (t1-repos, 2026-09-20)

Surveyed ~70 GitHub hits across "ensemble code generation", "code generation
reranking", "multi-sample code", "pass@k", "code candidate selection",
"llm code race". Cloned the 4 most reusable to `vendor/` on yote:
`/home/toxic/sovereign/killer-features/code-racer/vendor/`.

## CLONED

### 1. FSoft-AI4Code/SRank-CodeRanker — vendor/SRank-CodeRanker (e4672e1, 344K)
ACL Findings 2024: "Functional Overlap Reranking for Neural Code Generation"
(arXiv 2311.03366). **Closest match to the code-racer harness.**
- Pipeline is exactly our shape: `generation/` (code + test-case gen, model-agnostic
  run scripts) → `execution/` (`_execution.py`, `execution.py`, `run.py`,
  `run_greedy.py` — sandboxed multi-process code execution) → `reranking/`
  (`evaluator.py`, `AttentionRankingEvaluator`, `functionality_processing.py`,
  `pyminifier_canonicalize.py`, `codet_evaluation.py`).
- Selection logic: cluster candidates by *functional overlap* (outputs agree on
  generated test inputs), rank the best cluster by model logprob/reverse-logprob
  — beats Coder-Reviewer and CodeT on HumanEval (+2.1% avg margin, +23% over random).
- License: README claims MIT, **but no LICENSE file in repo** (API license field =
  NONE). Treat as ambiguous until resolved with the authors.
- How to invoke: `cd reranking/sh && ./run.sh <model> <dataset> <temp> <num_samples>
  <reranking_method>` (random|srank). Generation: `generation/gen_code/sh/run.sh
  <device_ids> <model> <dataset> <max_seq_len> <num_samples> <running_script>`.
- Reuse verdict: **PRIMARY SOURCE.** Lift `execution/` (execution harness) and
  `reranking/functionality_processing.py` + `evaluator.py` (functional-overlap
  clustering + ranking) as the execution-based selection core. Adapt the
  generation scripts' postprocessing for our candidate runner. t1-impl-strategies
  owns the srank strategy; t1-impl-core owns the execution sandbox.

### 2. facebookresearch/coder_reviewer_reranking — vendor/coder_reviewer_reranking (2044ef3, 440K)
Official code for "Coder Reviewer Reranking for Code Generation" (ICLR 2023,
arXiv 2211.16490). The paper SRank beats; still the reference implementation of
reviewer-based selection.
- `sample_selectors.py` (1180 lines): ~15 selectors per benchmark —
  executability filtering, sum-logprob, Coder-Reviewer / augmented-reviewer /
  reviewer-ensemble logprob combos, MBR-exec, oracle. This is a **menu of
  candidate-selection strategies** we can wire in as additional strategies.
- `execution.py` (642 lines) + `multi_exec.py` (101 lines): aggressive
  multiprocessing execution over cached samples; `evaluate.py` for pass@k.
- Requires datasets from `dl.fbairpublicfiles.com/coder-reviewer/datasets.zip`
  and `samples.zip`; python 3.8 + torch 1.12 stack.
- License: **CC-BY-NC 4.0 (non-commercial)** — fine as reference, cannot ship
  derived code in a commercial product without reimplementation.
- How to invoke: `python sample_selectors.py --model codex002 --num_samples_end 25
  --num_samples_gap 5 --data_path samples --out_dir result_db --dataset
  mbpp_sanitized --num_procs 10 --num_bootstraps 50 --temperature 0.4 --verbose`.
- Reuse verdict: **REFERENCE / STRATEGY MENU.** Read, don't ship. Port the
  selector ideas (reviewer-scoring, executability pre-filter, MBR-exec) as our
  own implementations; t1-impl-strategies maps each selector to a strategy.

### 3. jszheng21/RACE — vendor/RACE (3b8ee59, 3.4M)
"RACE: multi-dimensional benchmark for code generation" (arXiv 2407.11470):
Readability, mAintainability, Correctness, Efficiency. Apache-2.0.
- `race/` package: codegen, codeprocess (parser), dataloader
  (HumanEval/MBPP/LeetCode/ClassEval), virtualized-execution evaluation scripts.
  Ships data + Dockerfile.
- Not a candidate-race harness — a *benchmark* — but gives us the **evaluation
  side**: correctness + efficiency + readability metrics with sandboxed
  execution, directly useful for measuring which candidate won and why.
- Reuse verdict: **EVAL HARNESS INPUT.** Borrow the efficiency/readability metric
  ideas and the virtualized-execution pattern for our scoring; t1-architect
  decides how much of the benchmark to adopt for measuring race quality.

### 4. 2389-research/speed-run — vendor/speed-run (3baa3d9, 1.2M)
MIT. Claude Code plugin: `turbo` (direct codegen), `showdown` (same design,
parallel runners compete), `any-percent` (different approaches in parallel),
`judge` skill for picking winners. Cerebras-hosted first pass + surgical fixes.
- Reuse verdict: **WORKFLOW PATTERN ONLY.** No reranking math; the value is the
  taxonomy (compete vs explore vs direct) and the judge-skill prompt pattern for
  winner selection. Skim `skills/showdown/SKILL.md`, `skills/judge/SKILL.md`.

## EVALUATED, NOT CLONED

- juniorcharlie/llm-pipeline-selection (MIT) — "The Winner's Curse in LLM Pipeline
  Selection": measured selection bias in best-of-N (0.010–0.088 accuracy points;
  effective candidate count ≈ 1–3% of nominal). **Methodology caution**: correlated
  candidate pools break naive best-of-N reporting. t1-architect should budget
  dev/truth splits accordingly; no harness code worth cloning.
- WalkingDevFlag/MLE-STAR-Open (34★) — multi-agent ML-engineering pipeline with
  generate→debug→refine→ensemble. Heavyweight Kaggle scope, not a code-race
  harness. Read-only; don't clone.
- NinjaTech-AI/MPLE — README says "Coming soon". Dead.
- SecRank (wanyandengzi-png/...) — secure-code reranking, 0★, not evaluated deep.

## REUSE MAP (for t1-architect / t1-impl-core / t1-impl-strategies)

| Need | Source | File/dir |
|---|---|---|
| Execution sandbox (run N candidates) | SRank | `execution/{_execution.py,execution.py,run.py}` |
| Execution-based selection (functional overlap) | SRank | `reranking/{evaluator.py,functionality_processing.py}` |
| Reviewer-score selection strategies | coder_reviewer | `sample_selectors.py` (reimplement — CC-BY-NC) |
| Multi-process execution at scale | coder_reviewer | `multi_exec.py` |
| Correctness/efficiency/readability metrics | RACE | `race/` + eval scripts (Apache-2.0) |
| Race mode taxonomy + judge prompt pattern | speed-run | `skills/{showdown,any-percent,judge}/SKILL.md` |
| Selection-bias methodology guardrail | llm-pipeline-selection | paper/README (not cloned) |

License watch: coder_reviewer_reranking = CC-BY-NC (reference only);
SRank README claims MIT but ships no LICENSE file (confirm before shipping
derivatives); RACE = Apache-2.0; speed-run = MIT.
