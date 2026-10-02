---
id: sidechat-watch-squawk
title: 'Side-chat watch: Squawk hosting'
enabled: false
mode: task
concurrency:
  max_running: 1
  overlap: skip
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-15T00:36:09
  every: 30s
timeout_secs: 120
delivery: []
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"70daa860e14ee343"}'
  presentation_locale: en-US
---
Side-chat watchdog for "Squawk — first-class hosting" (chat_id: 1d3fa9cb-7d5f-4ca2-b53b-b97bab7579d8).

The chat tool namespace is NOT available in this worker runtime — do not call
tool_search.load_tool_namespace(paths=["chat"]) or chat.read_messages; both fail
here. Read messages from the agent's local session transcript via
sidechat-watch.py --read-jsonl (see step 2) instead of muse.db: filtered reads
against agent.context_items go through a security-barrier view that cannot use
the (agent_id, seq) index and time out as full table scans under load
(profiled 2026-09-19).

1. Resolve the chat's root agent (a side chat's chat_id equals its agent's session_id):
   SELECT agent_id AS aid FROM agent.agents
   WHERE session_id = '1d3fa9cb-7d5f-4ca2-b53b-b97bab7579d8' AND kind = 'root'
   ORDER BY created_at DESC LIMIT 1
   If no row, report that and stop.
2. Read the agent's latest turns from the local transcript (no DB on the hot
   path):
   ~/workspace/bin/taskhook run -- python3 ~/workspace/bin/sidechat-watch.py --aid <aid> --read-jsonl --tail-jsonl 20 > /tmp/scw-squawk-rows.json
   (Write ONLY via this shell redirect — never use a file-write tool here; the
   read-before-overwrite guard blocks it. The same ban covers appends: any
   daily-log append goes through `>>` shell redirect only — the final message
   is the run's audit record.) Each row is
   {s: seq, r: role, txt: text<=400, ca: created_at as epoch seconds,
   is_canned: bool}. The transcript at
   /home/hatch/agents/agent-<aid>/sessions/*.jsonl carries the same seq
   numbering as agent.context_items with millisecond reads.
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
   one-paragraph assessment of what Chris needs. Report only — take no other action.
