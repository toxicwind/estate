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
  at: 2026-09-19T02:38:00
  every: 5m
timeout_secs: 240
delivery: []
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"70daa860e14ee343"}'
  presentation_locale: en-US
---
Side-chat watchdog for "WhatsApp" (channel: whatsapp).

The chat tool namespace is NOT available in this worker runtime — do not call
tool_search.load_tool_namespace(paths=["chat"]) or chat.read_messages; both fail
here. Read messages through muse.db instead. Only the reviewed SQL functions in
the muse_db skill guide are accepted; keep every query small and bounded.

1. Resolve the WhatsApp side chat's root agent with a SINGLE joined query.
   Do NOT read a session id in one query and paste it into another: the
   transcribed id gets truncated or corrupted (34-char value observed in
   the wild against the real 36-char UUID), which silently breaks this
   watchdog every run. Resolve it here:
   SELECT a.agent_id AS aid
   FROM agent.session_metadata sm
   JOIN agent.agents a ON a.kind = 'root'
     AND (a.session_id = sm.session_id OR a.root_session_id = sm.session_id)
   WHERE sm.channel = 'whatsapp' AND sm.status = 'active'
   ORDER BY sm.updated_at DESC, a.created_at DESC LIMIT 1
   If this returns no row, report that and stop — do NOT proceed to step 2.
   Ignore the returned aid value: it is only a presence check; step 2
   re-resolves it inline, so nothing is ever copied by hand.
2. Read the agent's latest turns (bounded, index-backed) with the
   agent resolved inline by subquery — again, no id string is transcribed.
   Do NOT put a created_at predicate in the query — the range scan times out
   against the 5s DB statement limit (repaired 2026-09-18). Apply the 5-minute
   recency window yourself on ca:
   SELECT seq AS s, role AS r, left(text_content, 400) AS txt, created_at AS ca
   FROM agent.context_items
   WHERE agent_id = (SELECT a.agent_id
     FROM agent.session_metadata sm
     JOIN agent.agents a ON a.kind = 'root'
       AND (a.session_id = sm.session_id OR a.root_session_id = sm.session_id)
     WHERE sm.channel = 'whatsapp' AND sm.status = 'active'
     ORDER BY sm.updated_at DESC, a.created_at DESC LIMIT 1)
     AND role IN ('user', 'assistant')
   ORDER BY seq DESC LIMIT 20
   Keep only rows with ca within the last 5 minutes (the window covers
   scheduling backlog).
   If this returns 0 rows, that is a COMPLETE check: no recent user/assistant
   turns exist. Stay silent and report nothing. Do not retry, broaden, or run
   additional queries — an empty result is the answer, not an error.
3. Identify role=user messages from Chris in that window with NO substantive
   assistant reply after them. Substantive means the agent actually addressed the
   request. A canned refusal ("Sorry, I can't help you...") does NOT count.
4. If every recent user message already has a substantive reply: stay silent,
   report nothing.
5. If you find an unhandled user message: report concisely — the user's message
   verbatim, when it was sent, what the agent replied (if anything), and a
   one-paragraph assessment of what Chris needs. Report only — take no other
   action. (Read-only: never attempt to send messages into this channel chat.)
