---
id: tau-bench-nightly
title: tau bench nightly
enabled: true
owner: goal:tau-nightly-benchmark
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 03:30:00
delivery:
  - surface: side_chat
    to: 0fcb5f23-25d7-44de-9a7d-76342c7b4dd8
metadata:
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"0fcb5f23-25d7-44de-9a7d-76342c7b4dd8","delivery_channel":"side_chat","delivery_target_id":"0fcb5f23-25d7-44de-9a7d-76342c7b4dd8","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Run the permanent tau benchmark harness on awrawr-pc and report.

Steps:
1. Via the awrawr-mcp bridge (~/workspace/skills/awrawr-mcp/bin/exec.py), run `/home/toxic/bench-run.sh` with a 20-minute timeout. It is self-healing (native addon, hyperfine) and appends to /home/toxic/bench-run.log.
2. Read the newest run's section from the log (from the last "=== bench run started" to "=== BENCH_DONE").
3. Compare key numbers against the previous night's run (second-to-last section). Flag regressions >10% or newly failing benches.
4. Report to the user only if: a regression >10%, a bench newly fails/passes (e.g. coding-agent-guard starts working once the engine's src/config/ is restored), or the harness itself errors. Otherwise stay silent — log the run to the goal timeline via tracking.create_entry on goal_4a676af503b1.
