#!/usr/bin/env bash
set -euo pipefail
# Usage: stack/up.sh [-D] [core|sovereign|full] [extra process-compose args...]
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

detach=""
profile="sovereign"
extra=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -D|--detach|-d) detach="-D"; shift ;;
    core|sovereign|full) profile="$1"; shift ;;
    *) extra+=("$1"); shift ;;
  esac
done

cd "$SOV"
mapfile -d '' -t cfg_args < <(pc_config_args "$profile")

if [[ -n "$detach" ]]; then
  run_pc up "${cfg_args[@]}" $detach "${extra[@]}"
else
  run_pc up "${cfg_args[@]}" "${extra[@]}"
fi