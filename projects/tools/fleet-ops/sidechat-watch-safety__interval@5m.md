---
id: sidechat-watch-safety
title: 'Side-chat watch: safety layer'
enabled: true
mode: task
concurrency:
  max_running: 1
  overlap: skip
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-19T02:39:00
  every: 5m
timeout_secs: 240
delivery: []
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"70daa860e14ee343"}'
  presentation_locale: en-US
---
Side-chat watchdog for chat d5c06065-f0b5-4e0b-8026-44a2482806d7 ("Fix safety layer with subagent"). Chris explicitly requested this monitor.

The chat tool namespace is NOT available in this worker runtime — do not call
tool_search.load_tool_namespace(paths=["chat"]) or chat.read_messages; both fail
here. Read messages through muse.db instead. Only the reviewed SQL functions in
the muse_db skill guide are accepted; keep every query small and bounded.

1. Resolve the chat's root agent (a side chat's chat_id equals its agent's session_id):
   SELECT agent_id AS aid FROM agent.agents
   WHERE session_id = 'd5c06065-f0b5-4e0b-8026-44a2482806d7' AND kind = 'root'
   ORDER BY created_at DESC LIMIT 1
   If no row, report that and stop.
2. Read the agent's latest turns (bounded, index-backed). Do NOT put a
   created_at predicate in the query — the range scan times out against the
   5s DB statement limit (repaired 2026-09-18). Apply the 5-minute recency
   window yourself on ca:
   SELECT seq AS s, role AS r, left(text_content, 400) AS txt, created_at AS ca
   FROM agent.context_items
   WHERE agent_id = '<aid>' AND role IN ('user', 'assistant')
   ORDER BY seq DESC LIMIT 20
   Keep only rows with ca within the last 5 minutes (the window covers
   scheduling backlog).
   If this returns 0 rows, that is a COMPLETE check: no recent user/assistant
   turns exist. Do not retry, broaden, or run additional queries — an empty result
   is the answer, not an error.
2b. Timeout/error path: if ANY DB query returns an error — including a statement
   timeout — write the error text into your final message and STOP immediately.
   Do NOT retry the query. One attempt per query; a failed query is a failed run,
   reported honestly, never a retry loop.
3. If Chris's latest user message already has a substantive assistant reply
   addressing it, proceed to step 5. A canned refusal
   ("Sorry, I can't help you...") does NOT count as substantive.
4. If his latest message has no substantive reply yet, send a brief nudge to this
   chat: the timestamp and a one-line topic summary. Do not quote his message
   text. Report only; take no other action.
5. MANDATORY FINAL STATUS LINE: end EVERY run with a one-line final message —
   it becomes the run's result_summary, and an empty summary makes the run
   unverifiable (fleet trust counts it against this job). "Stay silent" means no
   chat delivery, never an empty final message. Format: `WATCH-OK safety |
   <what checked> | <finding>` or `WATCH-FAIL safety | <step> | <error>`.
   Never leave the final message empty.
