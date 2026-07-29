#!/usr/bin/env bash
set -euo pipefail
SOV="$HOME/sovereign"
source "$SOV/stack/lib-ports.sh"
require_env LLAMA_SWAP_PORT
PORT="$LLAMA_SWAP_PORT"
BACKEND="${LLAMA_SWAP_BACKEND_PORT:-25200}"
BIN="$HOME/projects/llama-swap-main/llama-swap"
[[ -x "$BIN" ]] || { echo "llama-swap bin not found at $BIN" >&2; exit 1; }
CONF="$SOV/config/llama-swap.yaml"
[[ -f "$CONF" ]] || { echo "llama-swap config not found at $CONF" >&2; exit 1; }
fuser -k "${PORT}/tcp" 2>/dev/null || true
fuser -k "${BACKEND}/tcp" 2>/dev/null || true
"$BIN" --config "$CONF" --listen "127.0.0.1:${BACKEND}" &
BPID=$!
cleanup() { kill "$BPID" 2>/dev/null || true; }
trap cleanup EXIT TERM INT
for i in $(seq 1 40); do
  if curl -sf -m 0.3 "http://127.0.0.1:${BACKEND}/health" >/dev/null 2>&1; then break; fi
  sleep 0.25
done
exec /home/toxic/.bun/bin/bun --hot run "$SOV/src/services/mesh-front.ts" \
  --service llama-swap \
  --listen "0.0.0.0:${PORT}" \
  --backend "127.0.0.1:${BACKEND}"
