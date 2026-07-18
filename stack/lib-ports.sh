#!/usr/bin/env bash
# Source port SSOT for shell services. No numeric defaults in callers.
SOV="${SOVEREIGN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
# shellcheck disable=SC1091
set -a
# shellcheck source=/dev/null
[[ -f "$SOV/config/ports.env" ]] && . "$SOV/config/ports.env"
# shellcheck source=/dev/null
[[ -f "$SOV/.env.local" ]] && . "$SOV/.env.local"
set +a

require_env() {
  local n="$1"
  if [[ -z "${!n:-}" ]]; then
    echo "missing $n — set in $SOV/config/ports.env" >&2
    return 1
  fi
}
