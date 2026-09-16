#!/usr/bin/env bash
# ==============================================================================
# Sovereign Orphan Cleaner Helper
# Scans for and cleans orphan compiler loops (cargo-watch), headless CLI workers,
# and zombie build tasks that cause CPU load spikes and terminal lag.
# NEVER kills WezTerm, WezTerm-gui, Pitchfork supervisor, or active editors.
# ==============================================================================
set -euo pipefail

echo "=== [1/3] Scanning for runaway cargo-watch processes ==="
WATCH_PIDS=$(pgrep -f "cargo-watch watch" || true)
if [ -n "$WATCH_PIDS" ]; then
    echo "Found orphan cargo-watch PIDs: $WATCH_PIDS"
    for pid in $WATCH_PIDS; do
        echo "Terminating cargo-watch PID $pid..."
        kill "$pid" 2>/dev/null || true
    done
else
    echo "No orphan cargo-watch processes running."
fi

echo "=== [2/3] Scanning for zombie tiny-inference workers ==="
ZOMBIE_WORKERS=$(pgrep -f "__omp_worker_tiny_inference" || true)
if [ -n "$ZOMBIE_WORKERS" ]; then
    echo "Found orphan tiny inference worker PIDs: $ZOMBIE_WORKERS"
    for pid in $ZOMBIE_WORKERS; do
        echo "Terminating zombie worker PID $pid..."
        kill -9 "$pid" 2>/dev/null || true
    done
else
    echo "No zombie workers running."
fi

echo "=== [3/3] Current System Load Status ==="
cat /proc/loadavg
uptime
