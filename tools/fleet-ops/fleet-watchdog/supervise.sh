#!/bin/bash
# fleet-watchdog supervisor — runs ON awrawr-pc, invoked by the 2m platform
# cron via the cell driver (driver.sh).
#
# 1. Ensures the direct 60s sweeper (sweepd.sh) is alive: starts it if dead,
#    restarts it if wedged (alive but no sweep for >200s).
# 2. Runs ONE backstop sweep only when the last sweep is stale (>100s) —
#    i.e. sweepd just died/was restarted. Otherwise stays out of sweepd's
#    way (healthy steady state = supervisor no-op).
#
# Prints one JSON line for the driver log: either the supervisor status or
# the full sweep result when a backstop sweep ran.
set -uo pipefail
WD=/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog
VARDIR=/home/toxic/var/fleet-watchdog
LOG=$VARDIR/sweepd.log
STATE=$WD/state.json
STALE_AFTER=100   # backstop sweep when last sweep older than this
WEDGED_AFTER=200  # restart sweepd when alive but silent longer than this
UNIT=fleet-watchdog-sweepd.service
mkdir -p "$VARDIR"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { printf '%s supervise: %s\n' "$(ts)" "$*" >>"$LOG"; }

# --- sweeper supervision: systemd unit preferred, pgrep/setsid fallback ---
use_systemd=false
if systemctl --user cat "$UNIT" >/dev/null 2>&1; then use_systemd=true; fi

sweepd_alive() {
  if [ "$use_systemd" = true ]; then
    [ "$(systemctl --user is-active "$UNIT" 2>/dev/null)" = "active" ]
  else
    pgrep -f "[s]weepd\.sh" >/dev/null 2>&1
  fi
}

restart_sweepd() {
  if [ "$use_systemd" = true ]; then
    systemctl --user restart "$UNIT" >/dev/null 2>&1
  else
    pkill -f "[s]weepd\.sh" 2>/dev/null || true
    setsid nohup bash "$WD/sweepd.sh" >>"$LOG" 2>&1 < /dev/null &
  fi
}

now=$(date +%s)
last=0
if [ -f "$STATE" ]; then
  last=$(python3 -c 'import json,sys,datetime
d=json.load(open(sys.argv[1])); ts=d.get("last_sweep_ts")
print(int(datetime.datetime.fromisoformat(ts.replace("Z","+00:00")).timestamp()) if ts else 0)' \
    "$STATE" 2>/dev/null || echo 0)
fi
age=$(( now - last ))

restarted=false
if ! sweepd_alive; then
  restart_sweepd
  restarted=true
  log "sweepd was DOWN, restarted (via $([ "$use_systemd" = true ] && echo systemd || echo setsid))"
elif [ "$age" -gt "$WEDGED_AFTER" ]; then
  restart_sweepd
  restarted=true
  log "sweepd WEDGED (last sweep ${age}s ago), restarted"
fi

if [ "$age" -gt "$STALE_AFTER" ]; then
  # Backstop: immediate coverage while the (re)started sweepd spins up.
  # sweep.py's flock serializes against sweepd — no double pages.
  python3 "$WD/sweep.py"
else
  if sweepd_alive; then alive_json=true; else alive_json=false; fi
  printf '{"ok":true,"supervisor":"ok","sweepd_alive":%s,"sweepd_restarted":%s,"last_sweep_age_s":%s,"backstop_sweep":false,"hb_ok":true,"pages":[],"posted":false}\n' \
    "$alive_json" "$restarted" "$age"
fi
