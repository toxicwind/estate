---
id: squawk-archive-hourly
title: Squawk chat-log archive (hourly)
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-14T15:06:45
  every: 1h
delivery: []
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"9d61bc1f6c96ea07"}'
  presentation_locale: en-US
---
Hourly squawk chat-log archive. Run the snapshot script on this machine:

python3 ~/workspace/skills/encrypted-github-fs/squawk_snapshot.py

It incrementally fetches new messages from the fleet and leads squawk channels on awrawr-pc (via the MCP bridge), groups them into hourly JSONL chunks, and stores them in the dedicated Google Drive folder `squawk-archive` (aliases like `squawk/fleet/2026-09-14-13.jsonl`) using the encrypted-github-fs skill's DRIVE route. State is tracked in the skill's store/squawk_state.json so reruns are idempotent.

Report in your final message: how many new messages were archived per channel (0 is a normal quiet result), the Drive aliases written, and any errors. If the bridge or Drive calls fail, say so plainly with the error text. Do not print secrets. Do not write per-run report files.
