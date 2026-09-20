---
id: tau-bench-watch
title: tau bench completion watch
enabled: false
owner: goal:tau-bench-run
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-14T17:10:43
  every: 20m
delivery:
  - surface: side_chat
    to: 0fcb5f23-25d7-44de-9a7d-76342c7b4dd8
metadata:
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"0fcb5f23-25d7-44de-9a7d-76342c7b4dd8","delivery_channel":"side_chat","delivery_target_id":"0fcb5f23-25d7-44de-9a7d-76342c7b4dd8","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Check whether the tau bench run on awrawr-pc has finished. Run: `cd ~/workspace/skills/awrawr-mcp && python3 bin/exec.py 'tail -30 /home/toxic/bench-run.log; echo "---"; pgrep -f bench-run.sh > /dev/null && echo RUNNING || echo NOT_RUNNING'`. If the log contains BENCH_DONE, summarize the bench results (each bench's headline numbers and any failures) for the user and note the tracked item goal_d0c2b3ed3956 should be closed. If not done yet, stay quiet (report nothing). If the process is NOT_RUNNING and the log has no BENCH_DONE, flag it as a failure worth surfacing.
