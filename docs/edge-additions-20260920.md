# edge-additions — September-2026 cutting-edge additions (2026-09-20)

Branch `edge-max-20260920`, worker **edge-additions** (under edge-max).
All work: permanent repo artifacts, committed, verified repeatedly.

## Impact-ordered additions

### 1. Keypool concurrent first-valid-wins racing — `bin/herd-keypool.py`

**Commits:** `ca0c6360d9` (racing) + `9cf22108ae` (recovery-semantics review fix)

The keypool sidecar (`:25109`) now races the top-N eligible provider keys
concurrently when `KEYPOOL_RACE_KEYS=N` (N>1); first successful upstream
response wins. `KEYPOOL_RACE_KEYS=1` (production default) is bit-for-bit the
legacy serial path. 401/402/429 park only the losing contestant; network
failures never mark keys dead; non-routing HTTP failures forward immediately.
`/status` exposes `race_keys` and `{races,wins,failed}` telemetry; audit logs
`race_win`/`race_loss` (key values never logged).

**Research lineage:** hedged/parallel request execution (Dean & Barroso
tail-tolerance lineage), speculative parallel fan-out evaluated against
TailSieve (arXiv `2608.22788`, 2026-08-24) and Speculative Programmatic Tool
Calling (alphaXiv `2608.spec-ptc`, 2026-08-24).

**Verification (2026-09-20):** compile OK; `--selftest` ALL PASS ×5;
mock-upstream (`:25129`) + sidecar (`:25119`) race suite, 17 checks ALL PASS ×3;
legacy `RACE_KEYS=1` serial slow-first check OK (0.70s). Live `:25109` and
production config untouched.

**Enablement:** `KEYPOOL_RACE_KEYS=1` is the production default — serial,
unchanged behavior. To experiment, run a sidecar copy with
`KEYPOOL_PORT=<alt>` + `KEYPOOL_RACE_KEYS=2` and point test traffic at it;
do not enable racing on the live `:25109` pool without a deliberate decision.

### 2. `--hedge-ms` hedged launch — `skills/hft-latency/`

**Commit:** `842d49709e`

The HFT racer skill (`bin/race.py`) gains `--hedge-ms N`: deadline-triggered
hedged launch. Default `0` keeps all-at-once launch. With N>0, contestants are
ordered by winners-log evidence; the best-known strategy launches at t=0 and
backups launch only if no valid result exists when the hedge deadline fires.
First-valid-wins and loser process-group killing unchanged. New events:
`attempt_start`, `hedge_armed`, `hedge_fired`, `hedge_standdown`; final JSON
includes `hedge_ms`. Catalog entry in `skills/README.md`.

**Verification:** compile OK; `tests/test_hedge.py` 5 deterministic tests ×3
runs; fast proven primary → `hedge_standdown` (backup never launched); slow
primary → backup fired at ~150ms and won at ~0.18s.

### 3. Read-only calibrated routing-score publisher — `tools/routing-score/`

**Commit:** `f8241e90cf`

`publish_scores.py` reads exact-output probe JSONL and writes an advisory
score artifact. **Read-only by construction** — never touches `herd.yaml`,
never parks peers, never alters selection (router-adjacent only, per lane
carve). Method: reliability = observed exact-output rate; Wilson 95% lower
bound penalizes small samples; latency P50/P95 from exact passes only;
separate error classes (`http_402`, `http_429`, `empty_200`, `wrong_200`,
`transport`); composite `wilson95_lower * 1000/(1000+p50_ms)`; artifact carries
`read_only: true`.

**Research lineage (September-2026 calibration grade):**
- Observed exact-output reliability over self-reported confidence —
  Claim-Level Confidence Calibration (arXiv `2608.22483`, 2026-08-23);
  SCOPE (arXiv `2602.13110`, 2026-08-18)
- Uncertainty via intervals, lower-bound publication — A-CRC-QA conformal
  spirit (arXiv `2608.12008`, 2026-08-12)
- Correlated-failure caution (agreement masking) — CAGE-CAL (arXiv `2605.30653`,
  2026-05-28)

**Verification:** tests ×3 runs; real probe data
(`projects/openrouter-probe/reverify-20260920.jsonl`, 8 records) ranked
sane — single-sample models correctly low-confidence.

### 4. Squawk history search — `projects/range/ranch/squawk/`

**Commit:** `82448e03f8`

`history_search.py` + `tests/test_history_search.py` + `HISTORY_SEARCH.md`
(linked from the squawk README). Batch CLI over message files (YAML
frontmatter + markdown body): substring/`--regex` query across title+body;
filters channel (repeatable), sender, status, seq range, ISO time range;
`--limit` (default 50) bounded, seq-sorted; JSONL or human output. No daemon,
no polling, read-only.

**Verification:** 5 tests ×3 runs ALL PASS; live run on the real squawk root:
2179 files scanned, 23 `keypool` matches, bounded 3 shown, malformed file
warned+skipped.

## Known conflict — orphan handoff (not integrated, per lane carve)

`~/workspace/skills/race` on hatch predates this work and was promoted into
`skills/hft-latency/` as the base of commit `842d49709e`. The lane carve
assigns orphan integration to **repo-integrator-max** — this is flagged (not
silently claimed): the hatch workspace copy was edited in place and the repo
copy is a promotion, not a fresh integration. Reconciliation belongs to
repo-integrator-max; the committed work stands unless they rule otherwise.

## Branch state

Base: `e4fa962ae4`. Commits on `edge-max-20260920`:
`ca0c6360d9` → `842d49709e` → `f8241e90cf` → `82448e03f8` → `9cf22108ae`.
No live daemon touched; no production setting enabled; no monkeypatches —
every change is a committed file.
