# Meta-Research Toolkit — Iteration Plan

Ordered by dependency and payoff. Each item names the files it touches.
Docs only describe; code changes are listed so whoever implements them
knows exactly where to cut.

## P0 — Correctness of what exists

1. **Fix the README vendor fiction** (`README.md`).
   `vendor/` (ble.sh, awesome-selfhosted, nushell, brush) does not exist in
   the tree. Either add the submodules (`git submodule add …`) or delete the
   section. A README that describes absent directories is a trust bug.
2. **Python↔TS strategy conformance test**
   (`tests/python/test_refusal.py`, `tests/typescript/prompts.test.ts`).
   The five strategies exist in both `src/python/refusal_geometry/prompts.py`
   and `src/typescript/prompts/orchestrator.ts` by hand-copy. Add a test that
   loads both registries (TS side via `bun run` emitting JSON, or a checked-in
   snapshot) and asserts name/kind/citation equality. Today a one-line edit
   on either side silently forks them.
3. **Add `[tool.ruff]` to `pyproject.toml`.**
   `make lint` runs `ruff check src/python` with default ruleset — pin the
   intended selects/ignores so lint is reproducible, not ambient.

## P1 — Make the infrastructure real

4. **Wire fsbus to a real lane** (`src/python/fsbus_orchestrator.py`,
   new `src/python/lottery/bus_worker.py`).
   Implement the missing consumer: a worker loop that `claim()`s tasks,
   runs an EV recomputation job, and writes results to `outbox/`. Suggested
   first job: "recompute dynamic EV for all four games from a fresh
   remaining-prizes snapshot." Until a consumer exists, fsbus is untested
   architecture — `test_orchestrator.py` only covers primitives.
5. **Harden the scraper** (`src/python/lottery/scraper.py`).
   - Replace the heuristic guideline-PDF URL with a real index crawl
     (Colorado Lottery game-list pages link the actual filer_public URLs).
   - Add retry/backoff + on-disk PDF cache (`data/pdfs/`), so audits are
     reproducible without re-hammering the site.
   - Parse remaining-prize counts from `coloradolottery.com/en/scratch`
     (currently documented as an endpoint but unimplemented).

## P2 — Close the loop on each track

6. **Lottery: scheduled EV watch** (new `src/python/lottery/watch.py`).
   Poll remaining prizes on a schedule, recompute `dynamic_ev()`, and emit
   an alert when a game flips positive-EV. The Casino Ca$h Chips "jackpot lag
   anomaly" in `ev_calculator.py` is the proof case — the watch turns a
   static snapshot into a standing detector. Output rows to parquet, not
   stdout.
7. **Refusal geometry: experiment harness** (new
   `src/python/refusal_geometry/harness.py`).
   Run the five strategies via `MetaClient` (or a Python equivalent) against
   a real endpoint, score the responses, and record `RefusalAnalysis` rows
   (model, routing_failure_score, is_porous, orthogonality estimate) to
   parquet. Without this the track is a prompt library, not a measurement
   toolkit. Keep every prompt meta-analytical — the existing strategies
   already are; the harness must not add jailbreak attempts.
8. **Perl: test ble-lint.pl** (new `tests/perl/` or a pytest wrapper).
   The linter is the only untested component. At minimum: fixture ble.sh
   source tree + fixture `.blerc` with known-bad options → assert exit 1
   and the exact invalid-option report; `--fix` → assert backup created and
   lines commented.

## P3 — Packaging & CI

9. **Decide the packaging story** (`pyproject.toml`).
   Either make it pip-installable (proper `[tool.setuptools]` packages for
   `lottery` / `refusal_geometry`, entry points for fsbus) or declare it
   script-style and drop the build-system pretense. Half-packaged is the
   worst of both.
10. **CI** (new `.github/workflows/ci.yml`).
    Run `make test` + `make lint` on push. The repo currently has no CI;
    the 12+5 green tests only stay green if something runs them.
11. **Typecheck the TS/Python boundary** (`src/typescript/api/types.ts`).
    Add a contract test asserting the JSON emitted by the Python models
    validates against the TS interfaces (via a zod schema generated from or
    checked against `types.ts`). Same class of bug as #2.

## Explicitly out of scope

- Live jailbreak/red-team tooling. The refusal track studies routing
  behavior via published findings and meta-analysis only.
- Real-money lottery automation. EV computation and alerting only.
