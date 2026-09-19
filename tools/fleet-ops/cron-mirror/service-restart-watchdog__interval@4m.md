---
id: service-restart-watchdog
title: Service restart watchdog (4m)
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-19T02:28:30
  every: 4m
timeout_secs: 180
delivery: []
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"70daa860e14ee343"}'
  presentation_locale: en-US
---
Service-health alert check. A lightweight poller (~/workspace/service-health-poller.sh) appends a metrics line every 30s to ~/workspace/service-health.log; your job is alerting and self-healing, not measuring.
1. Self-heal: if `pgrep -f service-health-poller.sh` finds nothing, restart it detached: `setsid nohup bash ~/workspace/service-health-poller.sh >/dev/null 2>&1 < /dev/null &`
1b. io-governor: if `pgrep -f "bin/io-governor"` finds nothing, restart it as root: `sudo -n setsid nohup python3 /home/hatch/workspace/bin/io-governor >> /home/hatch/workspace/psi-monitor/governor.log 2>&1 < /dev/null &`. The daemon is the reactive I/O-stall triage (never kills; leased work paged only, unleased heavy writers ionice-idled + paged). If sudo fails, report WATCH-FAIL with the sudo error — do not run it unprivileged (ionice on other PIDs needs root).
2. STATE=~/workspace/service-health.state (single line: last alerted boot_id). Take the last line of the log; extract LATEST_BOOT (the value after `boot=`).
   - STATE file missing: if the log contains more than one distinct `boot=` value, a restart happened while unmonitored — report it to the user (old boot -> new boot, timestamp of the first line carrying the new boot). Write LATEST_BOOT to STATE either way. Single boot in log: write STATE silently, no message.
   - LATEST_BOOT differs from STATE content: RESTART detected. Tell the user briefly in this chat: service restarted, new boot first seen at <timestamp>, previous boot <old value>. Include fleet state: query muse.db with `SELECT status, count(*) FROM agent.subagent_spawns GROUP BY status` and report running vs errored counts. Then write LATEST_BOOT to STATE.
3. Pressure check on the latest log line: parse `M_avail` (number before `M_avail`) and disk (number before `%`). If avail < 1024 or disk >= 90, warn the user in this chat with the exact numbers — we may be causing resource pressure.
4. Hygiene: if the log exceeds 20000 lines, keep only the last 10000.
5. Otherwise stay silent (no chat delivery). Routine healthy runs never message the user.
6. MANDATORY FINAL STATUS LINE: end EVERY run with a one-line final message — it becomes the run's result_summary, and an empty summary makes the run unverifiable (fleet trust counts it against this job). "Stay silent" means no chat delivery, never an empty final message. Format: `WATCH-OK service-restart-watchdog | <what checked> | <finding>` or `WATCH-FAIL service-restart-watchdog | <step> | <error>`. Never leave the final message empty.

---

HONEST RUN RECEIPT (mandatory — the platform status badge is untrustworthy; this footer is the honest record):
End your final report with EXACTLY this line, filled in:
HONEST-RECEIPT job=service-restart-watchdog verdict=genuine|no-op|failed duration_s=<seconds> work="<one line: what actually happened>" evidence="<path|none>"
- Verdicts: genuine = did real work with an observable effect; no-op = ran correctly, nothing needed doing; failed = errored or produced nothing.
- This footer goes in your final message (it becomes the run's result_summary) even on silent runs. Never omit it: a missing footer marks the run AMBIGUOUS (unverifiable).
