#!/bin/bash
# Watches for browser-toggle.sh execution for N seconds, logs hits with timestamps.
# Usage: watch_toggle.sh [seconds]
SECS=${1:-12}
END=$((SECONDS + SECS))
> /tmp/toggle_hits.log
while [ $SECONDS -lt $END ]; do
  for p in $(pgrep -f 'browser-toggle' 2>/dev/null); do
    cmd=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null)
    case "$cmd" in
      *watch_toggle*) continue ;;
      *browser-toggle.sh*)
        echo "$(date +%T) pid=$p $cmd" >> /tmp/toggle_hits.log ;;
    esac
  done
  sleep 0.1
done
echo "watch done"; cat /tmp/toggle_hits.log
