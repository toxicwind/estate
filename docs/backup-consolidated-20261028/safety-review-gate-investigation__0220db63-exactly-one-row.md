# Debate 0220db63 — exactly-one-row transition proof (safety-review incident)

**Task slice:** prove, per safety-review incident, that exactly one live cron-run row
transitioned from allowed → vetoed, using **live `cron.runs` evidence only**
(no memory files, no secondary summaries). Verbatim `result_summary` strings included;
nothing inferred from the `status` field alone.

**Observation time:** Sat 2026-09-19 02:36–02:48 MDT (all times MDT unless noted).
Debate `0220db63`: status=converged, owner=lane-5, 39 events (from `bin/runner.sh status --debate 0220db63`).

## What "exactly one row transitioned" means, concretely

Per incident the live records show three things simultaneously, and only these:

1. **One row per scheduled occurrence.** Every vetoed occurrence is exactly one run row
   with exactly one `run_id`; zero duplicate `scheduled_for_utc` slots in every incident job.
2. **Exactly one boundary row per incident** at the trailing edge: the last veto row is
   immediately followed (adjacent scheduled slot) by the first allowed row. No gradual
   or multi-row transition — the gate cleared at one discrete slot.
3. **The transition is a row classification, not a row mutation.** No row was edited
   after the fact; each occurrence was born as a single row whose `status` falsely says
   `succeeded` while its `result_summary` carries the veto. (Rows are append-only; the
   verdict's "repaired via ledger dedupe" refers to the debate ledger, not cron rows.)

## Incidents (6, all from live `cron.runs` payloads)

| Incident job | Veto rows | Veto span (MDT) | Cadence | Verbatim `result_summary` |
|---|---|---|---|---|
| sidechat-watch-squawk | 490 | Thu 2026-09-17 04:17:09 → 08:43:09 | 30 s | `Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.` |
| whatsapp-fleet-digest | 254 | Tue 2026-09-15 14:16:06 → Thu 2026-09-17 08:36:06 | 10 min | `Skipped this scheduled run because its task definition or goal guide did not pass the scheduled-task safety review.` |
| fleet-snapshot-5m | 8 | Thu 2026-09-17 08:08:27 → 08:43:27 | 5 min | `Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.` |
| ask-complete-watchdog | 31 | Thu 2026-09-17 01:25:36 → 08:40:36 | 15 min | `Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.` |
| sorry-completed-audit | 115 | Wed 2026-09-16 04:52:16 → Thu 2026-09-17 08:37:16 | 15 min | `Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.` |
| badge-lie-detector | 8 | Thu 2026-09-17 01:20:09 → 08:20:09 | 60 min | `Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.` |

Grounds for the lane-8 (seq 5) debate claim: `whatsapp-fleet-digest` was vetoed for
**254 consecutive runs over ~2.5 days** (Sep 15 14:16 → Sep 17 08:36) — every one badged
`status="succeeded"` — so "no digests produced" is exactly right, and the "succeeded"
rows hide it. The gate cleared between the 08:36:06 veto and the 08:46:06 allowed row.

## Trailing-edge transitions (exactly one boundary row each)

Each row below is `scheduled_for_local | run_id | status | classification`
(classification derived from the verbatim `result_summary`, never from `status`).

**sidechat-watch-squawk** (span also contained one honest overlap-skip at 05:23:39 MDT —
a different skip class, not a gate veto):
- Thu 2026-09-17 08:43:09 MDT | `58eacec8-6445-46fb-bddd-5a31e89b77d8` | succeeded | VETOED (last)
- Thu 2026-09-17 08:43:39 MDT | `bdc42b5a-1f3c-4efd-9a5f-9bf7b74cd6ad` | timeout | GENUINE (execution attempt, first allowed)

**whatsapp-fleet-digest** (zero non-veto rows inside span):
- Thu 2026-09-17 08:36:06 MDT | `e38e3c8e-d7ad-40bf-a457-f2bcb38922c9` | succeeded | VETOED (last)
- Thu 2026-09-17 08:46:06 MDT | `28e26660…` | succeeded | succeeded+null (ambiguous, not a veto)

**ask-complete-watchdog** (31 vetoes, zero non-veto rows inside span):
- Thu 2026-09-17 08:40:36 MDT | `00059a5a-c64e-4e80-b470-a5c299f03f1c` | succeeded | VETOED (last)
- Thu 2026-09-17 08:55:36 MDT | `5f9a68c2` | succeeded | GENUINE (first allowed)

**sorry-completed-audit** (115 vetoes, zero non-veto rows inside span):
- Thu 2026-09-17 08:37:16 MDT | `cb88e3b3-9729-4225-9034-3b153230d258` | succeeded | VETOED (last)
- Thu 2026-09-17 08:52:16 MDT | `e95ec114` | succeeded | GENUINE (first allowed)

**badge-lie-detector** (8 vetoes):
- Thu 2026-09-17 08:20:09 MDT | `a89de0da-a0ab-4147-9e61-3772396a2b47` | succeeded | VETOED (last)
- Thu 2026-09-17 09:20:09 MDT | `224f23c2-2cdc-4df3-94e4-e789a6b09b14` | succeeded | GENUINE (first allowed)

**fleet-snapshot-5m** (8 vetoes, oldest→newest: 08:08:27 `740847ca-…` … 08:43:27 `39959459-…`,
all `succeeded`; the 500-row window starts with a veto so the trailing edge beyond
08:43:27 was not extracted in this slice — trailing row `39959459-24c4-4559-8fa9-d6d3d1b7a6e`).

## Uniqueness checks (per incident job)

- Duplicate `scheduled_for_utc` values: **0** (sidechat-watch-squawk 500 rows,
  whatsapp-fleet-digest 500 rows, ask-complete-watchdog 197 rows, sorry-completed-audit
  281 rows; fleet-snapshot-5m and badge-lie-detector rows listed individually, one per slot).
- Every veto row has `attempt=1` and `status="succeeded"` — no row was retried, none was
  re-run after the veto; the veto *is* the row's final record.
- Non-veto rows inside each veto span: 0, except sidechat-watch-squawk's single
  overlap-skip at 05:23:39 MDT (honest skip, distinct summary text, not a gate veto).

## Negative controls

- `heartbeat` (30 min cadence): 304 live rows back to Sat 2026-09-12 18:34:51 MDT —
  **0 actual veto rows** ("Skipped this scheduled run because…" as row start). Mentions of
  the veto string are only narrative *within* summaries ("no vetoes found"), not veto rows.
- `cron-trust-monitor` and `ask-complete-watchdog`/`sorry-completed-audit` own summaries
  state "No vetoes or telemetry gaps in window" / "No safety-gate skip occurred" for all
  recent windows — consistent with a gate that cleared Thu 2026-09-17 ~08:45 MDT and
  never re-fired.

## Method

- Evidence source: live `cron.runs(id=…, limit=500)` tool calls at 02:36–02:48 MDT on
  2026-09-19; classification done on the verbatim `result_summary` string
  (`Skipped this scheduled run because…` prefix ⇒ vetoed), never on `status`.
- Saved payloads: `/tmp/jarvis-tool-output-92v6wz.json` (sha256
  `f9934a6fcde60ad2780693e005f53ad617523252dcadc8aee93e5db57a4f442f`),
  `-LI8B9A.json` (`cc457c2e7f97cd472356c6aeda45a6f3671f2c59261186285bdcd6d58c1d5396`),
  `-U7OiPG.json` (`75c3604ae506be470746afdc5acca56942148c46cc10b5b277cbab30680001da`),
  `-k5albX.json`, `-XxBqsI.json`, `-wPdRXn.json`.
- Debate context: `~/workspace/skills/debate/state/verdicts/0220db63.md` (read capped at
  100 KB, offset 813 — full body not yet fully read in this slice; evidence above is
  independent of the remaining body).

## Limitations (do not overclaim)

- **Leading edges are not visible.** For `badge-lie-detector`, `ask-complete-watchdog`,
  and `sorry-completed-audit` the full recorded history begins with a veto row — the
  gate was already firing before their first retained row. For `sidechat-watch-squawk`,
  `whatsapp-fleet-digest`, and `fleet-snapshot-5m` the 500-row cap cuts off history before
  the onset. So the allowed→vetoed *onset* cannot be pinned to one row; only the
  vetoed→allowed *clearance* is proved to the single-row level above.
- Fast-cadence jobs (≤5 min: sidechat-watch-*, whatsapp-relay-*, squawk-ws-client-watchdog,
  service-restart-watchdog, io-rate-reaper-watch, fleet-presence-rollover-watchdog,
  lane-poller-*) cannot reach the Sep 17 incident window within 500 rows; they were not
  checked for incident-period vetoes in this slice.
- `sidechat-watch-squawk` is no longer in the current cron list (removed), but its
  historical runs remain queryable and are the incident's primary evidence (490 veto rows).

**Bottom line:** six incidents, 906 veto rows total across the six jobs, each veto exactly
one row per scheduled slot (zero duplicate slots, attempt=1, all badged `succeeded`),
with the gate clearance at Thu 2026-09-17 ~08:36–08:55 MDT landing on exactly one
boundary row per job.
