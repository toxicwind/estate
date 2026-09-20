# E2E addendum to the frozen harness contract

`t1-impl-core/INTERFACE.md` v1 is the contract between harness core and
strategy adapters. This file is t1-e2e's addendum: how independent
verification works and what counts as a harness bug.

## Harness behavior (observed, run_candidate.py)

- Testbed is FLAT: `<outdir>/solution.py` + `tests/*` copied side-by-side into
  a temp dir; `python -m pytest -q --tb=short -p no:cacheprovider`, cwd=testbed.
- `import solution` works because pytest inserts the test file's dir (the bed).
- Valid = solution exists AND pytest rc==0 AND failed==0 AND passed>0
  (parsed from `-q` output: `N passed` / `N failed, M passed`).
- Per-candidate NDJSON `candidate_result` on stderr; winners appended to
  `winners/code-racer-<task>.jsonl`; race.py also logs tag `code-racer-<task>`
  to `~/.cache/shingle/hft_race_winners.jsonl`.

## E2E independent verification (t1-e2e, trust-but-verify)

After the harness declares a winner per task:

1. Take the winning `<outdir>/solution.py` (from `runs/` artifacts or
   re-materialized from the winners ledger).
2. Re-run the harness's own testbed procedure manually: fresh temp dir,
   copy solution.py + task `tests/*`, `pytest -q`, same timeout.
3. Diff the verdict. A race "win" that fails independent verification is a
   **false-win bug** filed against the harness (not the strategy).
4. Spot-check anti-cheat: grep the winning solution.py for strings unique to
   the hidden tests (`FakeClock`, `50k ops`, `OrderedDict` differential seed).
   A hit means the strategy read `tests/` — report as a harness isolation bug.

## Known harness limitations (to verify during e2e)

- Strategies receive `<task-dir>` which CONTAINS `tests/` (adapter interface:
  `run <task-dir> <output-path>`). Hidden-ness is by convention, not
  enforcement. E2E will test whether a deliberately cheating strategy can win.
- `parse_pytest` returns failed=-1 on unparseable output → invalid. A strategy
  that crashes pytest entirely (e.g. syntax error in solution.py → collection
  error) yields rc!=0 → invalid. Correct behavior; e2e confirms.
- Task-3's tests spawn subprocesses with cwd=HERE (the bed). `timeout=20` per
  CLI call; `test_timeout_s: 60` in limits.yaml. E2E confirms no flake.

## For t3-e2e (debate-vs-single-shot A/B)

Same corpus works for A/B: prompt = `task.md` + starter/buggy file(s);
outcome = hidden `tests/` pass/fail + wall-clock. Suggested metric: pass@k and
median latency per task, single-shot vs debate-of-3. Their debate-oracle corpus
(5 tasks) + this corpus (4 tasks) = 9-task A/B pool once test conventions align.
