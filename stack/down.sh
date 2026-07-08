#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
cd "$SOV"

# 1. Attempt graceful API shutdown, forcing IPv4 resolution if supported by your PC version.
run_pc --address 127.0.0.1 down "$@" 2>/dev/null || run_pc down "$@" >/dev/null 2>&1 || true

# 2. Hard fallback: If the API is wedged, send SIGTERM directly to the daemon.
# Process-compose intercepts 15 and initiates its own graceful child shutdown tree.
if pgrep -x "process-compose" >/dev/null; then
  pkill -15 -x process-compose || true
  sleep 2
  # 3. Nuke if it hangs.
  pkill -9 -x process-compose || true
fi