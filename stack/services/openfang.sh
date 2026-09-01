#!/usr/bin/env bash
# Openfang service — Rust binary on OPENFANG_PORT.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_env OPENFANG_PORT
PORT="$OPENFANG_PORT"

# Find the openfang binary
BIN_CAND=("$SOV/bin/openfang" "$HOME/.local/bin/openfang" "$HOME/.openfang/bin/openfang" "/usr/local/bin/openfang" "$HOME/projects/openfang/target/release/openfang")
BIN=""
for c in "${BIN_CAND[@]}"; do
  [[ -x "$c" ]] && BIN="$(realpath "$c")" && break
done

if [[ -z "$BIN" ]]; then
  echo "[openfang] binary not found, trying cargo build..."
  if [[ -f "$SOV/src/services/openfang.ts" ]]; then
    exec /home/toxic/.bun/bin/bun --hot run "$SOV/src/services/openfang.ts"
  fi
  echo "[openfang] no binary or TS entry found" >&2
  exit 1
fi

fuser -k "${PORT}/tcp" 2>/dev/null || true
exec "$BIN" --listen "0.0.0.0:${PORT}"
