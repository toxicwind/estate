---
id: squawk-ws-client-watchdog
title: Squawk WS client watchdog (1m)
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-14T15:53:14
  every: 1m
metadata:
  presentation_locale: en-US
---
Keep the Squawk websocket push client alive. Run `~/workspace/squawk-ws-client-watchdog.sh`: it starts `~/workspace/squawk-ws-client.py` (detached, logs to `~/workspace/squawk-ws-client.log`) only if no matching process is running. Do nothing if the client is already up. If the log shows repeated handshake failures, do not hammer reconnects — the client backs off on its own (15s→5m); just report the pattern.
