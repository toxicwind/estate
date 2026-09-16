#!/bin/bash
# Safe pitchfork wrapper - sanitizes output for LLM consumption
cd /home/toxic/sovereign
export PATH="/home/toxic/.local/share/mise/shims:$PATH"

cmd="$1"
shift

case "$cmd" in
  start)
    for daemon in "$@"; do
      pitchfork start "$daemon" 2>&1 | cat -v | sed 's/\^@//g; s/\[[0-9;]*m//g' &
      PF_PID=$!
      # Wait up to 30s for the daemon to be ready
      for i in $(seq 1 60); do
        if ! kill -0 $PF_PID 2>/dev/null; then break; fi
        sleep 0.5
      done
      kill $PF_PID 2>/dev/null
      echo "started: $daemon"
    done
    ;;
  stop)
    for daemon in "$@"; do
      pitchfork stop "$daemon" 2>&1 | cat -v | sed 's/\^@//g; s/\[[0-9;]*m//g' &
      PF_PID=$!
      for i in $(seq 1 30); do
        if ! kill -0 $PF_PID 2>/dev/null; then break; fi
        sleep 0.5
      done
      kill $PF_PID 2>/dev/null
      echo "stopped: $daemon"
    done
    ;;
  list)
    pitchfork list 2>&1 | cat -v | sed 's/\^@//g; s/\[[0-9;]*m//g'
    ;;
  *)
    echo "Usage: pf.sh {start|stop|list} [daemon...]"
    ;;
esac
