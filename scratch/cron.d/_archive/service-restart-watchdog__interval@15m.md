---
id: service-restart-watchdog
title: Service restart watchdog (15m)
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-14T13:34:49
  every: 15m
timeout_secs: 180
delivery:
  - surface: side_chat
    to: bb551bbc-81cd-4f77-a2d4-ead6d3eeaa78
metadata:
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"bb551bbc-81cd-4f77-a2d4-ead6d3eeaa78","delivery_channel":"side_chat","delivery_target_id":"bb551bbc-81cd-4f77-a2d4-ead6d3eeaa78","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Service restart + resource watchdog. Every run:
1. Exec and capture: BOOT=$(cat /proc/sys/kernel/random/boot_id), UPTIME=$(uptime -p), MEM=$(free -m | awk '/^Mem:/{print $3"/"$2"MB used, "$7"MB avail"}'), DISK=$(df -h / | awk 'NR==2{print $5" used"}').
2. Append one line to ~/workspace/service-health.log: `$(date -u +%Y-%m-%dT%H:%M:%SZ) boot=<BOOT> <UPTIME> mem=<MEM> disk=<DISK>`.
3. Read the previous boot id from the last non-current line of the log. If BOOT differs from it (or the log had no prior line): a service restart occurred. Report to the user in this chat, briefly: restart detected, approx time, and that running workers were bounced. Also query muse.db for current subagent counts by status (SELECT status, count(*) FROM agent.subagent_spawns GROUP BY status) and include the running vs errored numbers.
4. If available memory < 1024MB or disk use >= 90%: warn the user in this chat that the box is under resource pressure we might be causing.
5. Otherwise stay silent — the log line is the record. Do not message the user for routine healthy runs.
