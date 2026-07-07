#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
PORT="${LLAMA_HERDER:-25021}"

fuser -k -9 "${PORT}/tcp" 2>/dev/null || true
sleep 1

"${SOV}/tools/llama-swap/llama-swap" \
  --config "${SOV}/tools/llama-swap/config.yaml" \
  --listen "127.0.0.1:${PORT}" &
swap_pid=$!

(
  sleep 3
  curl -sf --max-time 120 "http://127.0.0.1:${PORT}/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    -d '{"model":"beellama/qwen-flash","messages":[{"role":"user","content":"ok"}],"max_tokens":1,"temperature":0}' \
    >/dev/null 2>&1 || true
) &

wait "$swap_pid"