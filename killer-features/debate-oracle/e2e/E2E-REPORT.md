# debate-oracle E2E Report (t3-e2e)

Date: 2026-09-20 · Corpus: `killer-features/debate-oracle/tasks/` (5 tasks, 39 hidden pytest tests)
Harness: `killer-features/debate-oracle/e2e/` · Model lanes via sovereign-router :25104

## Corpus

| Task | File | Tests | Skills stressed |
|---|---|---|---|
| token-bucket | `token_bucket.py` | 7 | time math, threading, edge cases |
| toposort | `toposort.py` | 9 | graph algos, cycle reporting, determinism |
| lru-cache | `lru_cache.py` | 8 | O(1) data structures, perf gate |
| expr-eval | `expr_eval.py` | 8 | parsing, precedence, no-eval constraint |
| bloom-filter | `bloom_filter.py` | 7 | sizing math, hashing, probabilistic reasoning |

Reference solutions: 39/39 pass (corpus validated before any model ran).
Debaters see ONLY `PROBLEM.md`; tests are copied into the sandbox by the gate at verdict time.

## Method

- **Debate arm** (per task): 3 candidates (lanes: qwen3.5-9b / deepseek-coder-6.7b / exaone-1.2b),
  3 timed rounds via `bin/debate-run`, hardened oracle judge → `verdict.json`
  → `e2e/gate.py` walks winner+ranking, first e2e pass wins.
- **Single-shot arm** (per task): ONE direct generation via qwen3.5-9b (the debate's
  default lane), same prompt shape, no retries on quality → same e2e gate.
- **Oracle-bug criterion**: judge crowns a candidate that FAILS e2e while a ranked
  candidate PASSES → filed as oracle bug. Judge crowns a passer → correct.

## Per-task results

| Task | Debate winner (lane) | Verdict conf | E2E | Single-shot (qwen3.5-9b) | Winner |
|---|---|---|---|---|---|
| token-bucket | TBD | TBD | TBD | TBD | TBD |
| toposort | TBD | TBD | TBD | TBD | TBD |
| lru-cache | TBD | TBD | TBD | TBD | TBD |
| expr-eval | TBD | TBD | TBD | TBD | TBD |
| bloom-filter | TBD | TBD | TBD | TBD | TBD |

## A/B comparison

| Metric | Debate | Single-shot |
|---|---|---|
| Tasks solved (e2e pass) | TBD /5 | TBD /5 |
| Mean end-to-end latency | TBD | TBD |
| Oracle bugs (picked-failer-while-passer-ranked) | TBD | n/a |
| Cases where debate hurt | TBD | n/a |

## Confidence assessment

TBD after runs. Decision framework (pre-registered):

- **Debate earns its latency** if: success_rate(debate) − success_rate(single) ≥ 1 task
  AND oracle-bug rate = 0 AND mean debate latency ≤ 5 min/task.
- **Marginal** if debate only wins via the e2e fallback chain (runner-up retry) —
  that means the *gate*, not the *judge*, did the work.
- **Not worth it** if single-shot matches debate on ≥4/5 tasks, or any oracle bug
  (judge crowning a failer over a passer) appears — a judge that can't beat
  "pick the candidate that passes tests" is decoration.
- **Production-trustworthy** requires: judge+gate agreement on all tasks, zero
  oracle bugs, fallback chain exercised at least once (proves it works),
  and debate latency bounded/predictable.

## Failure modes observed

TBD.

## What's next

TBD.
