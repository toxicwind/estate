#!/usr/bin/env bash
# Keeps the Squawk websocket push client running. Runs every minute via cron.
#
# Liveness is tracked with a pidfile + /proc cmdline verification — NOT with
# pgrep substring matching. pgrep -f "[s]quawk-ws-client.py" false-positives on
# any probe wrapper / diagnostic / editor whose command line merely contains
# the string, causing the watchdog to skip startup while no client runs.
# A pidfile names one exact PID; /proc confirms that PID is really our client
# (argv == "python3 $CLIENT"). Stale pidfiles (dead PID, PID reused by another
# program, or garbage) are detected and replaced.
set -uo pipefail
CLIENT="$HOME/workspace/squawk-ws-client.py"
LOG="$HOME/workspace/squawk-ws-client.log"
PIDFILE="$HOME/workspace/squawk-ws-client.pid"
LOCKDIR="$HOME/workspace/.squawk-ws-client.lock"

client_alive() {
  # 0 iff PIDFILE names a live process whose argv is exactly our client.
  local pid cmdline
  pid="$(cat "$PIDFILE" 2>/dev/null)" || return 1
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  cmdline="$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null)" || return 1
  [[ -n "$cmdline" ]] || return 1
  # We always start it as: nohup python3 "$CLIENT"  (no args, no wrapper).
  # Anything else holding this PID is not our client (stale pidfile).
  [[ "$cmdline" == "python3 $CLIENT " || "$cmdline" == "python3 $CLIENT" ]]
}

if client_alive; then
  exit 0
fi
# Stale or missing pidfile: drop it so it can never be trusted again.
rm -f "$PIDFILE"
# Mutual exclusion: two cron runs must not start two clients.
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  exit 0
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT
# Re-check under the lock (a concurrent run may have just started it).
if client_alive; then
  exit 0
fi
# Re-exec detached so it survives the cron run.
nohup python3 "$CLIENT" >>"$LOG" 2>&1 &
echo "$!" > "$PIDFILE"
echo "$(date -u +%FT%TZ) watchdog: started squawk-ws-client (pid $(cat "$PIDFILE"))" >>"$LOG"
