#!/usr/bin/env bash
# Thin wrapper — canonical logic in stack/
set -euo pipefail
SOV="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export SOVEREIGN_ROOT="$SOV"

cmd="${1:-up}"
shift || true

case "$cmd" in
  up)
    exec "$SOV/stack/up.sh" "${1:-core}" "$@"
    ;;
  up-d|up-detach)
    if [[ "${1:-}" == "core" ]]; then shift; fi
    exec "$SOV/stack/up.sh" -D core "$@"
    ;;
  down)
    exec "$SOV/stack/down.sh" "$@"
    ;;
  status|list)
    cd "$SOV"
    if command -v devbox >/dev/null 2>&1; then
      devbox run -- process-compose process list "$@" 2>/dev/null && exit 0
    elif process-compose process list "$@" 2>/dev/null; then
      exit 0
    fi
    echo "[sovereign] process-compose server not running — port health:"
    exec "$SOV/stack/health.sh"
    ;;
  health)
    exec "$SOV/stack/health.sh"
    ;;
  *)
    echo "usage: sovereign-stack.sh {up|up-d|down|status|health}" >&2
    exit 1
    ;;
esac