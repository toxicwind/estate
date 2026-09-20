# code-racer adapter interface (proposed by t1-impl-strategies, 2026-09-20)

A **strategy** is a directory `strategies/<name>/` containing an executable `run`
(invoked as `./run <task-dir> <output-path>`). The harness is strategy-agnostic:
it runs the adapter, then judges the produced solution with REAL tests.

## Invocation

```
strategies/<name>/run <task-dir> <output-path>
```

- `<task-dir>`: directory containing the task.
  - `task.json` — the task spec: `{ "id", "title", "description", "language", "timeout_s", "entrypoint" }`
  - `tests/` — the VISIBLE tests (a subset; hidden tests exist but are not mounted)
  - `starter/` — optional starter files
- `<output-path>`: where the adapter must write its solution.
  - If `<output-path>` exists as a directory, write solution files into it.
  - Otherwise treat it as the solution FILE to create (e.g. `.../solution.py`).

## Exit contract

- Exit 0 → adapter claims success; harness runs real tests against the solution.
- Exit non-zero or output-path missing/empty → strategy scored as failed for that task.
- The adapter must NEVER fabricate test results or touch the hidden tests.
  Validity is judged by the harness's real test runs, not by the adapter.

## Environment (harness-supplied, adapter must honor)

- `CODERACER_DEADLINE` — unix timestamp; adapter must stop before it (fail-fast ceiling).
- `CODERACER_TIMEOUT_S` — wall-clock ceiling in seconds for this run.
- `CODERACER_MODEL` / `CODERACER_BASE_URL` — optional overrides for model backends.
- `CODERACER_TEMPERATURE` — optional; adapters with a genuinely different
  temperature schedule may use it, but temperature alone is NOT a distinct strategy.

## Conventions

- Every adapter is self-contained: no network beyond the configured model
  endpoints; adapters may use `curl`/`python3` present on yote.
- Adapters must be deterministic in structure (prompt files live in the strategy
  dir), but may use randomness in sampling.
- Logging to stderr is encouraged; stdout reserved for a one-line summary.

## Strategy index (shipped by t1-impl-strategies)

| name | approach | model backend |
|---|---|---|
| `direct-fast` | single-pass direct generation | beellama :25122 `fast` (exaone-1.2B) |
| `direct-tool` | single-pass direct generation | :25152 `qwen3.5-9b-tool` |
| `plan-then-code` | model writes plan → model writes code from plan | `fast` / tool depending on step |
| `test-first` | model writes tests → code → self-repair loop vs its own tests | tool model |
| `router-hedged` | ask sovereign-router-ts :25104 with hedgedChain | router decides |
| `kimi-auto` | shim-resolved Kimi model via herd :25100 | kimi-auto |
| `oracle-consensus` | two models propose, third judges | fast + tool, judge tool |
| `evolve` | N samples, behavioral self-consistency vote on spec-generated probes | tool |
| `reviewer-rank` | N samples, reviewer scores 1-10, top wins (CoderReviewer idea, reimplemented — vendor CC-BY-NC) | tool samples + reviews |
| `showdown` | 2 runners, probe evidence + judge worksheet (speed-run pattern) | fast vs tool, judge tool |
| `efficiency-duel` | cross-model duel, correctness-gated fastest-wins (RACE idea, reimplemented) | fast vs tool |

## Anti-cheat compliance (per tasks/CONTRACT.md)

No adapter opens or reads anything under `<taskdir>/tests/`. Execution-based
strategies (evolve, showdown, efficiency-duel, test-first) run only
model-generated probes or self-written tests against candidate code.
Solutions use stdlib only, no network.

License notes: coder_reviewer_reranking (CC-BY-NC 4.0) and SRank-CodeRanker
(MIT claimed, no LICENSE file — unconfirmed) are NOT wrapped directly;
reviewer-rank/efficiency-duel/evolve are clean-room reimplementations of the
published ideas. RACE is Apache-2.0 but its pipeline needs torch/transformers
(absent on yote) — idea reimplemented instead. Any future wrapper just drops an
executable `run <task-dir> <output-path>` into strategies/.

`t1-impl-core`: this is the interface I am building against. If you need a
field I missed, say so on fleet and I'll rev it — but the executable-taking
`<task-dir> <output-path>` shape is fixed per the brief.
