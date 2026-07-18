#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
# shellcheck source=../lib-ports.sh
source "$SOV/stack/lib-ports.sh"
require_env LLAMA_SWAP_PORT
PORT="$LLAMA_SWAP_PORT"
BACKEND="${LLAMA_SWAP_BACKEND_PORT:-26100}"
BIN_CAND=("$SOV/bin/llama-swap" "/usr/local/bin/llama-swap" "$HOME/projects/llama-swap-main/llama-swap")
BIN=""
for c in "${BIN_CAND[@]}"; do
  [[ -x "$c" ]] && BIN="$(realpath "$c")" && break
done
[[ -n "$BIN" ]] || {
  echo "llama-swap bin missing ${BIN_CAND[*]}" >&2
  exit 1
}
CONF="$SOV/tools/llama-swap/config.yaml"
[[ -f "$CONF" ]] || CONF="$SOV/config/llama-swap.yaml"
fuser -k "${PORT}/tcp" 2>/dev/null || true
fuser -k "${BACKEND}/tcp" 2>/dev/null || true
# Backend on loopback only
"$BIN" --config "$CONF" --listen "127.0.0.1:${BACKEND}" &
BPID=$!
cleanup() { kill "$BPID" 2>/dev/null || true; }
trap cleanup EXIT TERM INT
# Wait backend health
for i in $(seq 1 40); do
  if curl -sf -m 0.3 "http://127.0.0.1:${BACKEND}/health" >/dev/null 2>&1; then break; fi
  sleep 0.25
done
exec /home/toxic/.bun/bin/bun run "$SOV/src/services/mesh-front.ts" \
  --service llama-swap \
  --listen "0.0.0.0:${PORT}" \
  --backend "127.0.0.1:${BACKEND}"
