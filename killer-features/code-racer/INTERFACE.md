# code-racer harness — interface contract v1

Frozen 2026-09-20 by t1-impl-core. This is the agreement between the harness
core (this repo) and candidate-strategy adapters (t1-impl-strategies).

## Strategy registry

File: `strategies/registry.json`

```json
{"strategies": [
    {"name": "alpha",
     "cmd": ["python3", "/abs/path/solver_alpha.py", "{outdir}"],
     "env": {"FOO": "bar"},
     "timeout_s": 60}
]}
```

- `name`: unique string. `cmd`: argv list (absolute paths — no PATH luck).
- `"{outdir}"` (or `"$outdir"`) in any argv element is replaced with a fresh,
  unique per-run directory; `"{taskdir}"` (or `"$taskdir"`) is replaced with
  the task dir. `SOLUTION_DIR`, `TASK_DIR`, `TASK_MD` env vars are set to the
  same locations.
- `env`: extra env vars merged over the process env (optional).
- `timeout_s`: per-strategy solve cap, overrides the task default (optional).
- **The strategy MUST write its solution to `<outdir>/solution.py`** — a
  python module the task's acceptance tests import as `solution`. It reads
  the problem statement from `<taskdir>/task.md`.
- A plain executable taking `<task-dir> <output-path>` args registers as
  `{"cmd": ["/abs/exe", "{taskdir}", "{outdir}"]}` — no wrapper needed.
- Exit codes are advisory only. **VALIDITY = solution.py exists AND the
  task's acceptance tests pass against it.** A broken solution never wins,
  no matter how fast it finishes.

## Task spec (for t1-e2e)

```
tasks/<task-name>/
    task.md        # problem statement
    tests/         # real pytest acceptance tests
    limits.yaml    # solve_timeout_s / test_timeout_s / workers (optional)
```

- Every test module must do `import solution` and call into it. The harness
  copies `<outdir>/solution.py` into a fresh testbed dir together with
  `tests/*` and runs `pytest -q` there — no magic imports, no conftest
  tricks required.
- Tests must be deterministic and self-contained (no network).

## Race semantics

- All selected strategies run concurrently (ThreadPoolExecutor, `workers`
  from limits.yaml or `--workers`).
- Per-strategy fail-fast: solve phase killed at `solve_timeout_s`, test
  phase at `test_timeout_s`.
- Winner = **first solution whose acceptance tests all pass**, tie-broken by
  lowest total latency. Measured per hop: solve_s, test_s, total_s.
- Every race appends to `winners/code-racer-<task>.jsonl`:
  `{ts, task, race_id, tag, winner, strategy_latency, candidates: {name:
  {solve, tests, valid, total_s}}, solve_timeout_s, test_timeout_s, wall_s}`.
- race.py also logs to the global HFT winners log
  (`~/.cache/shingle/hft_race_winners.jsonl`) under tag
  `code-racer-<task>` — the race-optimizer daemon watches this.

## CLI

```
race-task <task-dir> --strategies all|name,name --timeout N [--workers N]
```

Examples:

```
./race-task tasks/smoke-two-sum --strategies all
./race-task tasks/smoke-two-sum --strategies demo-fast,demo-slow --timeout 30
./race-task /abs/path/to/task --strategies alpha --workers 4
```
