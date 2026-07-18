#!/usr/bin/env bash
# Shared helpers for mise file tasks.
set -euo pipefail
export SOV="${SOVEREIGN_ROOT:-$PWD}"
cd "$SOV"

# shellcheck source=/dev/null
if [ -f "$SOV/stack/lib-ports.sh" ]; then
  source "$SOV/stack/lib-ports.sh"
fi
