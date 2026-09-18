# Meta-Research Toolkit — Architecture

v0.1.0. Polyglot (Python + TypeScript + Perl) research scaffold. Three
independent research tracks plus one piece of generic infrastructure.
The tracks share build tooling (Makefile, pytest, bun) but **no code**.

## Track 1 — Lottery EV analysis (`src/python/lottery/`)

Finite-population, without-replacement expected-value model for Colorado
scratch-off games.

- `ev_calculator.py` — `Game` frozen dataclass: `baseline_ev()` (price ×
  payout_pct, the statutory EV), `top_equity_per_ticket()` (remaining top
  prizes × top prize / implied remaining tickets),
  `dynamic_ev()` (baseline + top-prize lag surplus/deficit),
  `house_edge()` (1 − dynamic_ev/price; negative = player edge).
  Ships four audited games from the September 2026 snapshot:
  Casino Ca$h Chips (game 280, $20 — **positive EV**: both $1M top prizes
  still alive with ~300k tickets remaining, the "jackpot lag anomaly"),
  $250,000 Jumbo Bucks Crossword (390), Rocky Mountain Cube Bingo (371),
  $1,000 Mad Money (424).
- `scraper.py` — `GuidelinePDF` parser: builds a *heuristic* guideline-PDF
  URL under `static.coloradolottery.com/media`, regex-extracts total ticket
  counts (`OUT OF n`) and top-prize odds (`1 IN n`) from PDF text. The URL
  heuristic is documented as approximate — real paths use filer_public
  hashes.

Data flow: scrape guideline PDF → `Game` parameters → `dynamic_ev()`
verdict. `src/typescript/api/types.ts` (`LotteryAudit`) mirrors the report
shape for typed TS consumers.

## Track 2 — Refusal-geometry meta-analysis

Research premise (see `docs/refusal-geometry.md`): published 2026 findings
suggest LLM refusal is a low-dimensional, brittle routing behavior rather
than an ethical boundary — recognition signal nearly orthogonal to the
refusal direction (arXiv:2608.29109), diverse refusal prefixes raise stable
rank (arXiv:2608.25390), alignment trilemma (arXiv:2609.03887), published
safety metrics (arXiv:2606.12429), Meta's Rule of Two.

Python (`src/python/refusal_geometry/`):

- `models.py` — pydantic: `PromptClassification` (risk tier, eval/harm
  cues), `RefusalAnalysis` (routing_failure_score, is_porous,
  recognition_orthogonality_estimate, recommendation).
- `analyzer.py` — offline vector math: `RefusalVector` (cosine similarity),
  `SafetyReport` (published-metrics record), `RefusalSubspaceAnalyzer`.
  Pure math on supplied vectors — no live probing.
- `prompts.py` — five frozen `PromptStrategy` dataclasses, each targeting a
  distinct probe signal: `citation_activation`, `self_report_audit`,
  `mechanistic_steering`, `trilemma_argument`, `rule_of_two_framework`.
  All prompts are meta-analytical (analyze routing behavior, never request
  harmful content).

TypeScript (`src/typescript/`) mirrors the Python lane:

- `prompts/orchestrator.ts` — `PromptOrchestrator`: registry of the same
  five strategies, renders them into `ChatMessage[]`.
- `api/meta-client.ts` — zod-validated, OpenAI-compatible chat client
  (key from `META_API_KEY`, header-only, never logged).
- `api/types.ts` — `RefusalGeometryReport`, `LotteryAudit` interfaces.
- `index.ts` — entry: lists loaded strategies.

Data flow: citations → `PromptStrategy` → `PromptOrchestrator` →
`MetaClient.chat()` → model → `RefusalAnalysis` / `RefusalGeometryReport`;
`analyzer.py` does offline subspace math. **Gap:** the Python and TS
strategy registries are maintained by hand in parallel — the "mirror" is
honor-system, no conformance test enforces it.

## Track 3 — Shell tooling (`src/perl/ble-lint.pl`)

Dynamic ble.sh option linter. Discovers the valid-option list at runtime by
scanning the *installed* ble.sh source (never goes stale), lints `~/.blerc`,
`--fix` comments out invalid `bleopt` lines (timestamped backup).
Exit 0 = clean, 1 = invalid options found, 2 = usage/error. Untested.

## Infrastructure — `src/python/fsbus_orchestrator.py`

Dual-track filesystem message-bus orchestrator, **stdlib only**. Layout
under `$FSBUS_DIR` (default `./fsbus`): `inbox/` (immutable task payloads),
`claimed/` (atomic-rename claim target), `outbox/` (results via
tmp+fsync+rename), `dead/` (poison pills), `manifest.jsonl` (append-only
audit log). Invariants: `atomic_write_final` (tmp + fsync + rename + dir
fsync), `claim()` via atomic `rename(2)` with 30s leases and 3 attempts,
manifest appends are single `O_APPEND` writes. Threading-based with a STOP
event and signal handling. **Gap:** the bus has no real consumers — no
track submits jobs to it; tests cover primitives only.

## Build & test

- `Makefile`: `install` (pip + bun), `test` → `test-py` (pytest, 12 tests,
  coverage) + `test-ts` (bun test, 5 tests), `lint` (ruff + `tsc --noEmit`),
  `build` (bun build), `clean`.
- `pyproject.toml`: setuptools, requires-python ≥3.11, deps
  requests/pydantic/httpx/numpy/pandas. No `[tool.ruff]` section despite
  `make lint` calling ruff.
- `package.json`: bun module, zod + typescript, scripts for build/test/lint.

## What doesn't fit (yet)

1. `README.md` references `vendor/` submodules (ble.sh, awesome-selfhosted,
   nushell, brush) — the directory does not exist in the tree.
2. fsbus is generic infra with no wired consumers.
3. The refusal track is a prompt library + math toolkit, not yet a
   measurement harness — nothing runs the strategies end-to-end and records
   results.
4. The scraper's guideline-PDF URL is a heuristic, not a verified path.
