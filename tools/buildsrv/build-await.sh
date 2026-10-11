#!/usr/bin/env bash
# build-await.sh — poll a buildsrv job to completion (forward-only helper).
# Usage: build-await.sh <job-id> [timeout_s]
# Exits 0 when the job succeeds, 1 on failure/timeout/unknown.
# Prints the job log path so callers can tail it.
set -euo pipefail

JID="${1:?usage: build-await.sh <job-id> [timeout_s]}"
TIMEOUT="${2:-1200}"
BSRV="${BUILDSRV_BIN:-$HOME/bin/buildsrv}"
ROOT="${BUILDSRV_ROOT:-/home/toxic/buildsrv}"

deadline=$((SECONDS + TIMEOUT))
while :; do
  line=$("$BSRV" status "$JID" 2>/dev/null | sed -n '2p' || true)
  status=$(printf '%s' "$line" | sed -n 's/^ *status: \([a-z-]*\).*/\1/p')
  case "$status" in
    succeeded)
      echo "buildsrv: $JID succeeded"
      echo "buildsrv: log $ROOT/logs/$JID.log"
      exit 0
      ;;
    failed)
      echo "buildsrv: $JID FAILED — log tail:" >&2
      tail -n 40 "$ROOT/logs/$JID.log" >&2 || true
      exit 1
      ;;
  esac
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "buildsrv: $JID timed out after ${TIMEOUT}s (last: $line)" >&2
    exit 1
  fi
  sleep 2
done
