#!/bin/bash
# fleet-watchdog direct sweeper daemon (runs ON awrawr-pc).
#
# This is the PRIMARY heartbeat path: a lightweight loop running sweep.py
# every 60s with no agent-wrapper dispatch and no bridge hop. sovereign-chat
# presence TTL is 120s, so a 60s cadence keeps the lane-7 heartbeat alive
# with 60s of margin — immune to agent-dispatch jitter and bridge 502s.
#
# Supervised by the 2m platform cron (supervise.sh restarts this if it dies
# or wedges). Single instance via flock on $VARDIR/sweepd.lock.
# Logs: /home/toxic/var/fleet-watchdog/sweepd.log
#
# No `sleep` binary (standing rule): pacing uses isleep (interruptible,
# queryable). `isleep interrupt fleet-watchdog-sweep` wakes the wait early.
set -uo pipefail
WD=/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog
VARDIR=/home/toxic/var/fleet-watchdog
LOG=$VARDIR/sweepd.log
LOCK=$VARDIR/sweepd.lock
ISLEEP=/home/toxic/bin/isleep
INTERVAL=60
mkdir -p "$VARDIR"
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "sweepd: another instance holds $LOCK, exiting" >&2
  exit 0
fi
printf '%s sweepd: started pid=%s interval=%ss\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$$" "$INTERVAL" | tee -a "$LOG"
while true; do
  cycle_start=$(date +%s)
  if ! python3 "$WD/sweep.py" >>"$LOG" 2>&1; then
    printf '%s sweepd: sweep.py failed\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$LOG"
  fi
  elapsed=$(( $(date +%s) - cycle_start ))
  wait_s=$(( INTERVAL - elapsed ))
  if [ "$wait_s" -gt 0 ]; then
    "$ISLEEP" "$wait_s" --name fleet-watchdog-sweep --tick 5 >/dev/null 2>&1 || true
  fi
done
