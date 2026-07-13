#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
PORT="${LLAMA_SWAP_PORT:-25100}"
BIN_CAND=("$SOV/bin/llama-swap" "/usr/local/bin/llama-swap" "$HOME/projects/llama-swap-main/llama-swap")
BIN=""; for c in "${BIN_CAND[@]}"; do [[ -x "$c" ]] && BIN="$(realpath "$c")" && break; done
[[ -n "$BIN" ]] || { echo "llama-swap bin missing ${BIN_CAND[*]}" >&2; exit 1; }
CONF="$SOV/tools/llama-swap/config.yaml"; [[ -f "$CONF" ]] || CONF="$SOV/config/llama-swap.yaml"
fuser -k ${PORT}/tcp 2>/dev/null || true
exec "$BIN" --config "$CONF" --listen "127.0.0.1:${PORT}"
