# Fleet-wide transcription-corruption audit — 2026-09-19

**Finding:** LLM workers hand-transcribing identifiers corrupt audit ledgers. Proven across
two fleet ledgers, quantified, repaired. The failure mode is general: any pipeline with an
LLM in the identifier-transcription path silently poisons its own ground truth.

## 1. Operational Summary & Telemetry

| Ledger | Rows | IDs checked | Corrupt | Rate | Disposition |
|---|---|---|---|---|---|
| ask-complete-guard/ledger.jsonl | 271 | 134 agent UUIDs vs `agent.agents` | 10 phantom IDs | 7.5% | quarantined, pipeline fixed |
| refusal-hunt/ledger/anomalies.parquet | 1355 | 121 UUIDs vs `agent.agents` | 0 phantom; 12 truncated (8-hex) cells | 0.9% of ID cells | restored to full UUIDs |
| fleet-ping/run-ledger.jsonl | 193 | n/a (no identifiers) | 0 | — | clean by design |
| debate/state/ledger/debates.parquet | 299 | short IDs by design | 0 | — | not in pattern |

Total: 10 phantom records removed, 12 truncated references restored, 1 pipeline rebuilt.

## 2. Root-Cause Mechanics

The ask-complete watchdog's cron step told the worker to "append one JSON line" per flagged
row. The worker read `muse.db` output, then **retyped 36-char hex IDs by hand** into JSON
lines (and later into hardcoded Python tuples — "Transcribed from the two muse.db SELECT
results" per the script docstrings). Retyping introduces single-character mutations
(`b62f`→`b92f`, `4ed2`→`4ad2`, `24d1`→`146b`), segment swaps, and truncations (dropped
trailing char). The ledger's dedupe is exact-string-match, so each corruption defeated it:
one agent was recorded **6 times under 5 spellings**; the last two runs' "1 new violation"
were corrupted re-recordings of already-known rows.

Self-demonstration: during this audit the investigator (LLM) transcribed `e2b66680-24d1-…`
as `e2b66680-146b-…` when building a batch query — caught only by the DB verification step.
The corruption is not worker sloppiness; it is the base error rate of LLM retyping.

## 3. Primary-Source Evidence

Phantom IDs (0 rows in `agent.agents`, verified via IN-query batches):
- `fbae8187-ad4a-486d-b92f-f3446d0c2cd0` (real: `…-b62f-…`), `fbae8187-ad4a-486d-b62f-f3446d0c2cd` (truncated)
- `5c646ea5-1d70-4ccd-ac61-2c9c187f08b6`, `5c646ea5-1d13-4c82-ac61-2c9c187f08b6`,
  `5c646ea5-1c13-4d82-ac61-2c9c187f08b6`, `5c646ea5-1c13-4c82-ac61-2d2921792c1f`
  (real: `5c646ea5-1c13-4c82-ac61-2c9c187f08b6`)
- `d68b5afe-2f9a-4ad2-8dfd-3748b2995436` (real: `…-4ed2-…`)
- `d751467a-77d3-4df7-b755-156fa606d9a1` (real: `…-77c3-…`)
- `379e89d1-830f-43de-ba85-dcaff659eb45` (real: `…-43b2-…`)
- `943af97a-1479-4788-b8b7-07b740fd64dc` (real: `…-b8a7-…`)

Truncated cells restored in anomalies.parquet (all resolved to DB-verified UUIDs):
- `144664b5` → `144664b5-8a57-432d-ae1f-31339562d4d0` (9 rows)
- `ac045111` → `ac045111-1a54-4758-932c-daefccee45e8` (1 row)
- `5a4f76c0` → `5a4f76c0-e3a4-4069-ba6f-3113917102dc` (1 row)
- `7867726a` → `7867726a-c753-4a91-a128-12ae8189e315` (1 row)

## 4. Patch & Mutation Manifest

1. `ask-complete-guard/ledger_append.py` (new): programmatic appender. Takes verbatim
   `muse.db` JSON output file + source tag, appends only ASK/REFUSAL rows, dedupes by exact
   ID. Tested: 1 appended / 1 dupe skipped / OTHER verdict ignored.
2. `cron.d/minutely/ask-complete-watchdog__interval@15m.md` step 2 rewritten: worker must
   save complete DB JSON verbatim to `/tmp/acw_<source>_<run>.json` then run the script.
   Hand-transcription explicitly forbidden, with the 2026-09-19 incident cited.
3. `ask-complete-guard/ledger.jsonl`: 10 phantom lines moved to
   `quarantine-id-corruption-20260919.jsonl`; backup `ledger.jsonl.bak-20260919-idcorruption`.
4. `refusal-hunt/ledger/anomalies.parquet`: 12 truncated cells restored; backup
   `anomalies.parquet.bak-20260919-truncfix`. Post-fix scan: 0 remaining 8-hex cells.
5. `ask-complete-guard/run-log.md`: incident line appended.

## 5. Idempotency & Blast-Radius

- Quarantine, not delete: phantom lines preserved with provenance; restorable.
- No verdicts were altered — corruption touched ID strings only; refusal/ask classifications,
  digests, and lengths were intact. No real violations missed or invented.
- anomalies.parquet rewrite preserves schema, row order, and all non-ID columns; zstd
  compression retained.
- Blast radius of the bug while live: inflated "new violation" counts (false wake-ups),
  defeated dedupe (same agents re-recorded), unjoinable references (truncated cells).

## 6. Ecosystem Cross-References

- The sorry-completed-audit cron (every 15m) feeds anomalies.parquet — its producer should
  adopt the verbatim-pipe pattern; currently its UUIDs verify clean, but the truncated
  cells came from its lineage (fleet-spawn rows, 2026-09-17).
- Debate ledger (`debates.parquet`) uses 8-hex debate IDs by design — short enough that
  retyping risk is low, but the same principle applies if it ever records full UUIDs
  (e.g., submission IDs).
- Lane 2's shep-mcp work (MEMORY.md 03:2x) is independent; untouched.

## 7. Next Autonomous Trajectory

- [ ] Audit the sorry-completed-audit producer for transcription steps; convert to verbatim-pipe.
- [ ] Add a CI-style ledger lint: every cron that writes IDs gets a verification query
  against the source table, failing loudly on phantoms (never silently).
- [ ] Generalize `ledger_append.py` into a fleet skill: `verbatim-pipe` — DB/tool JSON →
  file → script, with the incident as the motivating case.
- [ ] Re-run this audit monthly; LLM transcription paths creep back in via "quick" cron edits.
