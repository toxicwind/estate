#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$SOV"

echo "[down] Stopping services..."

# Stop specific services gracefully first (better than killing the whole thing)
run_pc stop openfang "$@" 2>/dev/null || true
sleep 1

# Then bring down the whole compose
run_pc down "$@" 2>/dev/null || run_pc --address 127.0.0.1 down "$@" 2>/dev/null || true

# Final safety kill if process-compose is still up
if pgrep -x process-compose >/dev/null; then
    echo "[down] Force killing process-compose supervisor..."
    pkill -15 -x process-compose || true
    sleep 2
    pkill -9 -x process-compose || true
fi

echo "[down] All done."