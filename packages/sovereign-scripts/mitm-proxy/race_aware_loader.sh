#!/bin/bash
set -euo pipefail
export MITM_DIR="/mnt/agents/mitm-proxy"
export RATE_LIMIT_DELAY=0.15
export FUSE_MOUNT="/mnt/agents"
export TIMEOUT=20
log() { echo "[$(date +%H:%M:%S.%N | cut -c1-12)] $*"; }
if ! mountpoint -q "$FUSE_MOUNT"; then log "WARNING: $FUSE_MOUNT not a mountpoint"; fi
log "Starting MITM proxy..."
timeout 3600 python3 "$MITM_DIR/playwright_mitm.py" &
MITM_PID=$!
log "MITM PID: $MITM_PID"
trap 'kill $MITM_PID 2>/dev/null; exit' INT TERM EXIT
while true; do
    sleep 60
    if ! kill -0 $MITM_PID 2>/dev/null; then
        log "MITM died, restarting..."
        timeout 3600 python3 "$MITM_DIR/playwright_mitm.py" &
        MITM_PID=$!
    fi
done
