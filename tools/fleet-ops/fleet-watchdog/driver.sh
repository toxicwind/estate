#!/bin/bash
# fleet-watchdog cell-side driver.
# Durable copy: /home/toxic/sovereign/tools/fleet-ops/fleet-watchdog/driver.sh
# The platform scheduler runs THIS (bash ~/workspace/fleet-watchdog/driver.sh).
#
# The hot sweep path is DIRECT on awrawr-pc: sweepd.sh loops sweep.py every
# 60s with no agent-wrapper dispatch and no bridge hop (presence TTL 120s,
# so 60s keeps the lane-7 heartbeat alive with 60s margin). This driver is
# the 2m supervisor/backstop entrypoint. Three steps:
#   1. sync the rollover mirror cell -> awrawr-pc (best effort; sweep still
#      runs on the last good mirror if this fails)
#   2. sync the io-governor pages file (best effort; skipped if absent)
#   3. run the awrawr-pc supervisor: ensures sweepd is alive (restarts it if
#      dead/wedged) and runs ONE backstop sweep only when the last sweep is
#      stale. Prints one JSON line.
set -uo pipefail
AWR="$HOME/workspace/skills/awrawr-mcp/bin"
WD=/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog
if ! "$AWR/xfer.py" put /home/hatch/fleet-rollover.md "$WD/fleet-rollover.md" 2>&1 | tail -1; then
  echo "driver: rollover mirror sync FAILED (continuing on last mirror)" >&2
fi
# Best-effort: sync the io-governor pages file (lease-aware stall triage pages).
# Never fatal; skipped silently when the file does not exist yet.
"$AWR/xfer.py" put /home/hatch/workspace/state/io-governor.pages.jsonl \
    "$WD/io-governor.pages.jsonl" >/dev/null 2>&1 || true
# Best-effort: sync the lane-redrive pages file (dirty-state reactor pages).
# Never fatal; skipped silently when the file does not exist yet.
"$AWR/xfer.py" put /home/hatch/workspace/state/lane-redrive.pages.jsonl \
    "$WD/lane-redrive.pages.jsonl" >/dev/null 2>&1 || true
"$AWR/exec.py" --json --timeout 40 --argv bash "$WD/supervise.sh"
