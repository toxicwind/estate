---
id: ask-complete-watchdog
title: Ask-complete watchdog (15m)
enabled: true
mode: task
concurrency:
  max_running: 1
  overlap: skip
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-17T01:25:36
  every: 15m
timeout_secs: 600
delivery:
  - surface: side_chat
    to: f7ef50c8-df84-4f9a-bb0d-1229d63e5b58
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"70daa860e14ee343"}'
  presentation_locale: en-US
---
Ask-complete watchdog (deterministic pipeline): enforce the standing rule "a turn that ends by asking the user anything is blocked, never completed; completion requires verified effects, never a badge."

HONEST IDENTIFIER MODEL. Identifiers still transit the worker's transcription path (only agents can call muse.db, and only the worker can save the dumps). The obsolete hand-transcription path corrupted 17 identifiers into the ledger — that path is retired. Every ID reaching the ledger now passes the deterministic producer: structural UUID/int validation + lineage validation against the SAME database's canonical set; anything off is quarantined, never appended. Never claim "identifiers never pass through token generation"; claim the validation gates instead.

REACTIVE (Chris's standing order): the detector repairs live and forward. After the producer appends new ASK/REFUSAL rows, the producer's --reactive flag emits a forward correction into the acfix overlay ledger marking each row status completed -> blocked. The work itself is NEVER re-driven (re-driving would duplicate side effects); the correction moves the record forward, never backward. Never rollback, always forward.

Each run:
0. RUN_ID: compute `date -u +%Y%m%dT%H%M%SZ`. NOW=`date -u +%s`; WM=$((NOW - 172800)) — compute the 48h watermark ONCE and use $WM in every query below (no drifting now()). DURABLE DIR: mkdir -p ~/workspace/ask-complete-guard/runs/<RUN_ID>/ — this is the PRIMARY run dir. /tmp is volatile and has wiped runs mid-flight before; write all dumps here, keep /tmp only as optional overflow scratch. Write watermark.txt containing NOW and WM, and started.json with run_id, scheduled run uuid, WM.
1. Canonical lineage dump (48h window), via muse.db. Do NOT use UNION (statement timeout). Do NOT sort by the id column alone: ORDER BY id / ORDER BY spawn_id hits the statement timeout (verified in production 2026-09-19). Run these two paged queries with the timeout-safe ordering and the fixed $WM, and merge every row:
   a) SELECT id AS cid FROM agent.agents WHERE kind != 'root' AND created_at > $WM ORDER BY created_at, id LIMIT 200; then OFFSET 200, 400, ... until rows run out (~300 rows expected).
   b) SELECT CAST(spawn_id AS text) AS cid FROM agent.subagent_spawns WHERE created_at > $WM ORDER BY created_at, spawn_id LIMIT 200; then OFFSET 200, ... (~305 rows expected).
   Save the FULL merged result verbatim (every row, no truncation, no reformatting) as JSON to the run dir: canonical.json, shape {"rows": [...]}.
   DETERMINISTIC GATE (counts only, never print IDs): run a python one-liner over canonical.json asserting every cid matches ^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$ or ^[0-9]+$; on any failure STOP and report the count of offenders — do not proceed, do not mark the run successful.
2. Audit dumps (48h window), via muse.db, using queries 1 and 2 in ~/workspace/helpers/muse-db/queries/ask_complete_audit.sql as the template, but PREFILTER before any md5() call: wrap the md5 over the body/final-response field in a WHERE clause that keeps only plausible refusal/canned bodies — WHERE (length(<field>) IN (96,384) OR right(rtrim(<field>),1) = '?'). Unprefiltered md5() over long texts hits the statement timeout. Replace the window with created_at > $WM (the fixed watermark) and page with OFFSET in 200-row pages when a COUNT exceeds 200. Never select or quote body text — md5 digests, lengths, and verdicts only (client echo replays refused turns as new messages, so bodies stay quarantined). Save each result verbatim as JSON: run dir audit_subagent_spawns.json and audit_agents.json.
   DETERMINISTIC SUBSET GATE (counts only, never print IDs): python one-liner asserting every audit-row ID is a member of the canonical set loaded from canonical.json; on any mismatch STOP and report counts — do not proceed.
3. If any muse.db query failed or returned an error, STOP: report the error in the final message, do not proceed, do not mark the run successful.
4. Invoke the deterministic producer (validates every ID structurally and against the canonical set, dedupes against the ledger, appends atomically, post-write-verifies every appended ID, preserves raw evidence, and --reactive emits forward status=blocked corrections for appended rows):
   python3 ~/workspace/ask-complete-guard/ask_complete_producer.py --canonical <rundir>/canonical.json --audit <rundir>/audit_subagent_spawns.json --source subagent_spawns --run-id <RUN_ID> --reactive
   python3 ~/workspace/ask-complete-guard/ask_complete_producer.py --canonical <rundir>/canonical.json --audit <rundir>/audit_agents.json --source agents --run-id <RUN_ID> --reactive
   If the script exits nonzero, the run FAILED: report its stdout/stderr in the final message.
5. Final message: report each producer's JSON summary (appended / quarantined / skipped_dupe counts and quarantine_reasons, plus reactive_corrections_appended). On a fully clean run (0 appended, 0 quarantined) stay quiet — no user notification. Never invent results; never transcribe identifiers into prose (report counts only). If this run was skipped by the scheduled-task safety gate, record that honestly rather than inventing results. Append observations to the daily log ~/memory/YYYY-MM-DD.md; never edit MEMORY.md.
