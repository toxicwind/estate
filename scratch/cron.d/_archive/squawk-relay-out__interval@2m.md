---
id: squawk-relay-out
title: Squawk relay-out watcher
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-14T13:47:59
  every: 2m
timeout_secs: 300
delivery:
  - surface: side_chat
    to: 1d3fa9cb-7d5f-4ca2-b53b-b97bab7579d8
metadata:
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"1d3fa9cb-7d5f-4ca2-b53b-b97bab7579d8","delivery_channel":"side_chat","delivery_target_id":"1d3fa9cb-7d5f-4ca2-b53b-b97bab7579d8","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Squawk relay-out watcher — IRC-style feed of Squawk chat traffic into this side chat (this chat IS the relay endpoint).

Cursor file: ~/workspace/squawk-relay-out.cursor (plain text, last seen seq; treat missing file as 0).

Each run:
1. Via the MCP bridge (`python3 ~/workspace/skills/awrawr-mcp/bin/exec.py "bash -lc '<cmd>'" /home/toxic`, allow up to ~90s per call), check prerequisites on awrawr-pc:
   - `/home/toxic/squawk/chat.py` exists AND `relay-out` is a working subcommand (`python3 /home/toxic/squawk/chat.py relay-out --help` exits 0).
   - Chat root `/home/toxic/.shingle/squawk-root` exists with a `fleet` channel.
   If any prerequisite is missing, the relay isn't built yet — end the run quietly with result_summary "relay-out not available yet" and change nothing.
2. Read the cursor (default 0). Run via the bridge: `python3 /home/toxic/squawk/chat.py relay-out --root /home/toxic/.shingle/squawk-root --channel fleet --since <cursor> --format json`. Parse the JSON array of new messages.
3. If empty: end quietly, result_summary "no new traffic". Do not touch the cursor.
4. If new messages: write the highest seq seen to the cursor file, then report the traffic in your final message IRC-style, one line per message: `[#fleet] <sender> message text`. Keep each message's text intact (truncate individual messages past ~500 chars only). If the JSON carries signature/seal status, append ` [sealed]` or ` [unsigned]` where true — never drop that signal. Do not editorialize or summarize content away; Chris wants to SEE the traffic.
5. This job is READ-ONLY toward Squawk: never post, never relay-in, never modify channels or keys.

On repeated bridge failures (3+ consecutive runs), say so plainly in result_summary instead of staying silent.
