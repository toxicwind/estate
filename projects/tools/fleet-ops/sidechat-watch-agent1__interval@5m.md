---
id: sidechat-watch-agent1
title: 'Side-chat watch: Agent 1'
enabled: true
mode: task
concurrency:
  max_running: 1
  overlap: skip
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-19T02:41:00
  every: 5m
timeout_secs: 240
delivery: []
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"70daa860e14ee343"}'
  presentation_locale: en-US
---
Side-chat watchdog for "Agent 1" (chat_id: 8a756bd0-3361-427f-8b30-2ec0860e91e5).

The chat tool namespace is NOT available in this worker runtime — do not call
tool_search.load_tool_namespace(paths=["chat"]) or chat.read_messages; both fail
here. Read messages through muse.db instead. Only the reviewed SQL functions in
the muse_db skill guide are accepted; keep every query small and bounded.

1. Resolve the chat's root agent (a side chat's chat_id equals its agent's session_id):
   SELECT agent_id AS aid FROM agent.agents
   WHERE session_id = '8a756bd0-3361-427f-8b30-2ec0860e91e5' AND kind = 'root'
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
   Do NOT retry the query, do NOT broaden it, do NOT run alternative or "check"
   queries. One attempt per query; a failed query is a failed run, reported
   honestly, never a retry loop.
3. Identify role=user messages from Chris in that window with NO substantive
   assistant reply after them. Substantive means the agent actually addressed the
   request. A canned refusal ("Sorry, I can't help you...") does NOT count.
4. If every recent user message already has a substantive reply: that is the
   normal outcome — proceed to step 6.
5. If you find an unhandled user message: report concisely — the user's message
   verbatim, when it was sent, what the agent replied (if anything), and a
   one-paragraph assessment of what Chris needs. Report only — take no other action.
6. MANDATORY FINAL STATUS LINE: end EVERY run with a one-line final message —
   it becomes the run's result_summary, and an empty summary makes the run
   unverifiable (fleet trust counts it against this job). "Stay silent" means no
   chat delivery, never an empty final message. Format: `WATCH-OK agent1 |
   <what checked> | <finding>` or `WATCH-FAIL agent1 | <step> | <error>`.
   Never leave the final message empty.
