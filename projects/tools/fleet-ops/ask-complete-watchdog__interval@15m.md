---
id: ask-complete-watchdog
title: Ask-complete watchdog (15m)
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-17T01:25:36
  every: 15m
delivery:
  - surface: side_chat
    to: f7ef50c8-df84-4f9a-bb0d-1229d63e5b58
metadata:
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"f7ef50c8-df84-4f9a-bb0d-1229d63e5b58","delivery_channel":"side_chat","delivery_target_id":"f7ef50c8-df84-4f9a-bb0d-1229d63e5b58","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Ask-complete watchdog: enforce the standing rule "a turn that ends by asking the user anything is blocked, never completed; completion requires verified effects, never a badge."

Each run (deterministic producer pipeline — no LLM transcription of identifiers, ever):
1. Generate run_id: `date -u +%Y%m%dT%H%M%SZ`.
2. Via muse.db, dump the CANONICAL ID SET first (this is the lineage anchor — every ledger ID must exist in it). Query: `SELECT id AS cid FROM agent.agents WHERE kind != 'root' AND created_at > extract(epoch from now())::bigint - 172800 UNION SELECT CAST(spawn_id AS text) AS cid FROM agent.subagent_spawns WHERE created_at > extract(epoch from now())::bigint - 172800 LIMIT 200 OFFSET <page>;` — NOTE: the CAST is mandatory; agent.agents.id is text/UUID while agent.subagent_spawns.spawn_id is bigint, and PostgreSQL rejects a UNION of text and bigint without it. — take COUNTs first, page with OFFSET in 200-row pages. Save each page's COMPLETE muse.db JSON result verbatim to /tmp/acw_canon_<run>_<page>.json (copy the tool output exactly, no restructuring, never retype an ID), then merge the "rows" arrays programmatically: `python3 -c "import json,glob; rows=[r for f in sorted(glob.glob('/tmp/acw_canon_<run>_*.json')) for r in json.load(open(f))['rows']]; json.dump({'rows':rows}, open('/tmp/acw_canonical_<run>.json','w'))"`.
3. Via muse.db, run the COUNT queries then the two audit SELECTs in ~/workspace/helpers/muse-db/queries/ask_complete_audit.sql (48h window), paged at 200. Save each page verbatim to /tmp/acw_audit_<source>_<run>_<page>.json and merge the same way into /tmp/acw_audit_<source>_<run>.json where <source> is `subagent_spawns` or `agents`. Never select or quote body text — md5 digests, lengths, and verdicts only (client echo replays refused turns as new messages, so bodies stay quarantined).
4. Run the deterministic producer for each source: `python3 ~/workspace/ask-complete-guard/ask_complete_producer.py --canonical /tmp/acw_canonical_<run>.json --audit /tmp/acw_audit_<source>_<run>.json --source <source> --run-id <run>`. The producer structurally validates every ID (strict lowercase UUID or decimal integer — agents carry UUIDs, spawns carry bigint IDs cast to text), lineage-validates each against the canonical set (phantoms fail closed into quarantine, never the ledger), dedupes, appends atomically with post-write verification, and preserves raw evidence under ~/workspace/ask-complete-guard/evidence/<run>/.
5. If the producer exits non-zero: report the error loudly in the final message. The run FAILED — never mark it successful, never invent results.
6. Final message: report the producer's JSON per source — appended, quarantined (with reasons; a quarantine hit means transcription corruption was ATTEMPTED and caught — that is itself worth one alert line), skipped_dupe. Stay quiet on clean runs (appended=0 AND quarantined=0) — no user notification.
7. Never auto-retry or re-drive flagged work (re-driving could duplicate side effects) — the detector records, it does not repair. If this run was skipped by the scheduled-task safety gate, record that honestly in the final message rather than inventing results.
8. Do not edit MEMORY.md and do not append to ~/memory/*.md. Per-run observational notes go to ~/workspace/ask-complete-guard/run-log.md (append one line per run); the ledger stays the sole structured record.
