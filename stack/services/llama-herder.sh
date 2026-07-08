#!/usr/bin/env bash
set -euo pipefail

SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
PORT="${LLAMA_HERDER:-25021}"

# Safe release in case a previous hard-kill orphaned the port.
# (The 'exec' handoff below will eventually make this fuser call obsolete).
fuser -k "${PORT}/tcp" 2>/dev/null || true

# Run warmup asynchronously so it doesn't block the server startup.
(
  echo "[warmup] Waiting for llama-swap health endpoint..."
  
  # Poll for readiness instead of relying on a fragile sleep timeout.
  for _ in {1..60}; do
    if curl -sf --max-time 1 "http://127.0.0.1:${PORT}/health" >/dev/null; then
      echo "[warmup] Server ready, executing warmup completion..."
      
      curl -sf --max-time 120 "http://127.0.0.1:${PORT}/v1/chat/completions" \
        -H 'Content-Type: application/json' \
        -d '{"model":"beellama/qwen-flash","messages":[{"role":"user","content":"ok"}],"max_tokens":1,"temperature":0}' \
        >/dev/null 2>&1 || true
        
      echo "[warmup] Done."
      exit 0
    fi
    sleep 1
  done
  
  echo "[warmup] Failed to reach health endpoint within 60s."
) &

# Use 'exec' to replace the bash shell process with llama-swap.
# This guarantees lifecycle signals (SIGTERM/SIGINT) from process-compose
# route directly to the binary, preventing orphaned background processes.
exec "${SOV}/tools/llama-swap/llama-swap" \
  --config "${SOV}/tools/llama-swap/config.yaml" \
  --listen "127.0.0.1:${PORT}"