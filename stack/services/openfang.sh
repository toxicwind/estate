#!/usr/bin/env bash
# Openfang service — Rust binary on OPENFANG_PORT.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_env OPENFANG_PORT
PORT="$OPENFANG_PORT"

fuser -k "${PORT}/tcp" 2>/dev/null || true
if [[ -f "$SOV/src/services/openfang.ts" ]]; then
  exec /home/toxic/.bun/bin/bun run "$SOV/src/services/openfang.ts"
fi
echo "[openfang] TS entry not found at $SOV/src/services/openfang.ts" >&2
exit 1
