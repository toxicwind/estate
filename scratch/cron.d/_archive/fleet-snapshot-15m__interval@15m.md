---
id: fleet-snapshot-15m
title: Fleet snapshot (15m)
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-14T04:55:25
  every: 15m
timeout_secs: 180
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"9d61bc1f6c96ea07"}'
  presentation_locale: en-US
---
Fleet snapshot digest — the user explicitly asked for this every 15 minutes, on top of immediate completion/failure pings.

Steps:
1. Read `/opt/hatch/skills/muse_db/references/schema.md` for the table layout.
2. Query `agent.subagent_spawns`: all rows with `status='running'` (child_agent_id, parent_agent_id, created_at, LEFT(prompt,120) AS preview), plus rows with status completed/errored/failed where completed_at is within the last 30 minutes (child_agent_id, status, completed_at, LEFT(final_response,300) AS outcome).
3. Compose a COMPACT digest: one short line per running agent (task name, age), one line per recently finished (done/failed + one-line outcome). Note anything that looks stuck (running for hours with no progress) or failed.
4. If literally nothing changed since the last snapshot, reply with a single "no changes" line.

Keep it tight and phone-readable. Read-only: do not start, stop, resume, close, or message any agent, and do not edit any files.
