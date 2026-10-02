---
id: sidechat-watch-whatsapp
title: 'Side-chat watch: WhatsApp'
enabled: true
mode: task
concurrency:
  max_running: 1
  overlap: skip
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-19T02:43:00
  every: 5m
timeout_secs: 240
delivery: []
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","delivery_channel":"main","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Side-chat watchdog for "Lane-4 WhatsApp side chat" — deterministic thin worker.

You are a pipe, not an analyst. The LLM is NOT in the read path: you run
the script steps below exactly as written. Do not improvise queries,
retries, assessments, or summaries. The script computes the verdict and
guarantees the summary line; your job is to run it and deliver its output.

WATCH_ID=whatsapp

Step 1 — cached aid:
~/workspace/bin/taskhook run -- python3 ~/workspace/bin/sidechat-watch.py --watch-id whatsapp --print-aid
- Prints a UUID: that is the aid. Go to step 3.
- Prints an empty line: cold path (no cached aid, or the cached watermark is
  the bootstrap_failed sentinel). Do step 2 once, then step 3 — unless step 2
  wrote the sentinel, in which case STOP: your final message is the script's
  WATCH-FAIL line.

Step 2 — cold path (aid resolution + watermark seed; runs once, then cached):
a. Resolve the aid. Two queries, no OR-joins, no broadening:
   SELECT session_id FROM agent.session_metadata WHERE channel='whatsapp' AND status='active' ORDER BY updated_at DESC LIMIT 1
   then: SELECT agent_id FROM agent.agents WHERE kind='root' AND session_id='<sid>' ORDER BY created_at DESC LIMIT 1
   (if empty, retry with root_session_id='<sid>')
b. Seed the watermark WITHOUT scanning the transcript:
   ~/workspace/bin/taskhook run -- python3 ~/workspace/bin/sidechat-watch.py --aid <aid> --tip-jsonl
   Prints the transcript's max seq (local read, instant, zero DB load).
   If it errors, fall back to the DB tip query — up to 3 attempts:
   SELECT seq FROM agent.context_items WHERE agent_id='<aid>' ORDER BY seq DESC LIMIT 1
   (this backward scan can die on the 3s DB statement timeout for transcripts
   with long tool-call tails — that is expected, keep going)
   If ALL attempts fail, write the bootstrap_failed sentinel — NEVER seed 0
   (seeding 0 would replay the whole transcript as "new" and page on ancient
   messages):
   ~/workspace/bin/taskhook run -- python3 ~/workspace/bin/sidechat-watch.py --watch-id whatsapp --seed <aid> -1
   The script prints the WATCH-FAIL line; emit it verbatim as your final
   message and STOP. Do not run steps 3-5. The next tick retries the cold path.
c. On success:
   ~/workspace/bin/taskhook run -- python3 ~/workspace/bin/sidechat-watch.py --watch-id whatsapp --seed <aid> <last_seq>

Step 3 — the read (local transcript primary, DB fallback):
~/workspace/bin/taskhook run -- python3 ~/workspace/bin/sidechat-watch.py --watch-id whatsapp --read-jsonl > /tmp/scw-whatsapp-rows.json
(Write ONLY via this shell redirect — never use a file-write tool here; the
read-before-overwrite guard blocks it.) The file now holds a JSON array of row
objects — or {"error": "<text>"} if the transcript is missing.
Why local-first (measured 2026-09-19, not assumed):
- The local session transcript /home/hatch/agents/agent-<aid>/sessions/*.jsonl
  carries the same seq numbering as agent.context_items (verified: --tip-jsonl
  equals the DB watermark for all five watches; agent2's tip runs ahead of its
  watermark by exactly the rows written since its last tick). Local reads take
  milliseconds with zero DB-pool load.
- The DB forward scan (seq > watermark, ORDER BY seq ASC LIMIT 100) is
  index-served on UNIQUE (agent_id, seq), O(new rows) — it is the fallback,
  not the enemy. What dies is the BACKWARD tip scan (ORDER BY seq DESC) on
  transcripts with long tool-call tails (agent2: 39 statement timeouts in 3h
  at the 3s statement limit), plus fleet-wide DB pool exhaustion. Local-first
  keeps the watch off the pool; the DB fallback keeps it truthful if the
  transcript is ever missing.
Fallback — ONLY if stdout was an {"error":...} object: run
~/workspace/bin/taskhook run -- python3 ~/workspace/bin/sidechat-watch.py --watch-id whatsapp --query
and execute the printed SQL EXACTLY once via muse.db (3s DB statement limit —
one attempt only, no retry, no broadening, no alternate queries). Then
rm -f /tmp/scw-whatsapp-rows.json and write the result as a NEW file (creation is
allowed; overwriting an unread file is not) — JSON array of rows, or if the
query errored, {"error": "<verbatim error text>"}.

File-append rule (2026-09-19 — safety read-before-append fix): the no-write-tool
ban covers appends too. Do not improvise daily-log appends — the mandatory
final message is the run's audit record. If a daily-log append is ever needed,
do it ONLY as `... >> <file>` shell redirect inside `~/workspace/bin/taskhook
run --`; never a file-write tool (its read-before-overwrite guard fails the run
on appends).

Budget note: the whole run should take seconds. The platform may kill the
worker well before timeout_secs=240 (90-120s observed) — the script's 60s
SIGALRM guarantees a WATCH-FAIL line rather than silence, and the mandatory
final message below guarantees the audit record.

Step 4 — verdict (deterministic, inside the script):
~/workspace/bin/taskhook run -- python3 ~/workspace/bin/sidechat-watch.py --watch-id whatsapp --rows /tmp/scw-whatsapp-rows.json
The script advances its watermark (only on a clean read — a timeout never
reads as empty or as seen), appends to its run ledger, and prints the
verdict line.

Step 5 — delivery:
- Line starts WATCH-FAIL: the read path is broken. Report the error briefly
  in chat. This is urgent — the watch is blind.
- unhandled=0: stay silent toward the user (no chat message).
- unhandled>0: report concisely in chat: the unhandled user message(s), verbatim
  (already capped at 400 chars by the script), with timestamps.

Step 6 — MANDATORY FINAL MESSAGE: the script's WATCH-OK/WATCH-FAIL line,
verbatim. Never empty, never paraphrased, never "improved". "Stay silent"
means no chat message to the user — the final message is the run's audit
record and is always required. An empty final message is a failed run.
