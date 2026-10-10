# Upstream assessment — vllm-project/guidellm, 2026-10-02

**Fork HEAD:** `6b40c21e251a5095a7ae8064a6603a3f2c4b6d32` (unchanged since the
2026-09-20 audit; our 4 upstreamable commits intact).
**Upstream HEAD:** `bfcae5a3` (2026-09-30).

## Commits since the fork point (latest 8)

| Commit | Date | What | Valuable to us? |
|---|---|---|---|
| `bfcae5a3` | 2026-09-30 | build(deps): bump urllib3 2.7.0 → 2.8.0 | no — dep bump only |
| `4545d7cd` | 2026-09-30 | Few Small Cleanup items before v0.8.0 | no — cleanup |
| `4d733288` | 2026-09-30 | Add `generation_delay` metric (#1200) | **candidate** — measures data-generator delay vs benchmark delay |
| `3dd649c5` | 2026-09-30 | docs: correct benchmark constraint parameter names | no — docs |
| `58ea2f3e` | 2026-09-30 | Confidence intervals for request-level metrics (#1163) | **candidate** — CIs on percentiles; our p99 at n=5 is the slowest single request |
| `a938aaa6` | 2026-09-29 | Per-turn-position metrics for multi-turn workloads (#1181) | no — multi-turn only, our sweeps are single-turn |
| `f6392b34` | 2026-09-29 | Trace Relative Timing (#1190) | no — tracing infra |
| `337fc750` | 2026-09-29 | Turn predecessor delay + scheduler delay metrics (#1191) | no — multi-turn scheduler |

## Decision: audit, do not merge (2026-10-02)

Two candidates are genuinely relevant to estate benchmarking:

1. **`58ea2f3e` (confidence intervals)** — directly addresses our weakest
   methodology point: with `--requests 5`, the reported p99 IS the max of 5
   samples. Upstream now computes CIs around request-level metrics, which
   would let the router weight small-sample benchmarks honestly.
2. **`4d733288` (generation_delay)** — separates data-generator latency from
   model latency; useful when sweeps run synthetic workloads at scale.

Neither is a bugfix; both are additive metric systems that touch
`schemas/benchmark.py` and the accumulator — the same files our commits #3/#4
modify. A merge now risks destabilizing the four cited-by-hash commits and
the in-tree venv that the live sweeps depend on, right before the first
estate-wide sweep run.

Per the merge rules (`docs/UPSTREAM-MERGE.md`), the merge happens in the
standalone `toxicwind/roundup` repo (not on this box) with a merge commit,
then syncs into `fork/` via `scripts/upstream-merge.sh`, with the decision
recorded in `fork/MERGE-DECISIONS.md`. That is a lane of its own — not a
drive-by inside this one.

**Action:** no merge this lane. Revisit when the estate sweep is producing
steady numbers; `58ea2f3e` is the first candidate to pull, paired with a
sweep-config bump to n≥30 for percentile stability.
