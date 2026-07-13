#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$PWD}"
PORT="${LLAMA_SWAP_PORT:-25100}"

BIN_CAND=("/home/toxic/projects/llama-swap-main/llama-swap" "/usr/local/bin/llama-swap" "$SOV/bin/llama-swap")
BIN=""; for c in "${BIN_CAND[@]}"; do [[ -x "$c" ]] && { BIN="$(realpath "$c")"; break; }; done
[[ -n "$BIN" ]] || { echo "bin missing" >&2; exit 1; }

CONF_CAND=("$SOV/tools/llama-swap/config.yaml" "$SOV/config/llama-swap.yaml")
CONF=""; for c in "${CONF_CAND[@]}"; do [[ -f "$c" ]] && { CONF="$(realpath "$c")"; break; }; done
[[ -n "$CONF" ]] || { echo "conf missing" >&2; exit 1; }

SP="$(grep -E '^\s*startPort:\s*[0-9]+' "$CONF" | grep -oE '[0-9]+' | head -n1 || true)"
SP="${SP:-25000}"
MC="$(grep -cE '^\s{2}"[^"]+":' "$CONF" 2>/dev/null || true)"
MC="${MC:-30}"

# sanitize - ensure numbers
[[ "$SP" =~ ^[0-9]+$ ]] || SP=25000
[[ "$MC" =~ ^[0-9]+$ ]] || MC=30

EP=$((SP + MC + 10))
if (( PORT >= SP && PORT <= EP )); then
  echo "collision $PORT in $SP-$EP, bump LLAMA_SWAP_PORT" >&2
  exit 1
fi

fuser -k ${PORT}/tcp 2>/dev/null || true

( for i in {1..60}; do curl -sf --max-time 1 http://127.0.0.1:${PORT}/health >/dev/null && break; sleep 1; done
  curl -sf --max-time 30 http://127.0.0.1:${PORT}/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"beellama/qwen-flash-64k","messages":[{"role":"user","content":"ok"}],"max_tokens":1}' >/dev/null 2>&1 || true ) & disown

echo "[llama-swap] $BIN $CONF $PORT startPort=$SP count=$MC range=$SP-$EP"
exec "$BIN" --config "$CONF" --listen "127.0.0.1:${PORT}"
