#!/usr/bin/env bash
# loop.sh — run openfang-health.sh every OPENFANG_HEALTH_INTERVAL seconds (default 300),
# posting to the squawk fleet channel on status transitions (or daily digest).
# Fail-loud: any crash of the health script is logged and the loop keeps going.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERVAL="${OPENFANG_HEALTH_INTERVAL:-300}"
LOG="${SHINGLE_HOME:-/home/toxic/shingle}/var/openfang-health/loop.log"

while true; do
  echo "[$(date -Iseconds)] run" >>"$LOG"
  "$DIR/openfang-health.sh" --squawk --quiet >>"$LOG" 2>&1 || echo "[$(date -Iseconds)] HEALTH SCRIPT EXIT $?" >>"$LOG"
  sleep "$INTERVAL"
done
