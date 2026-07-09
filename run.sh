#!/usr/bin/env bash
set -euo pipefail

ROOT="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
PROXY_PORT="${LLAMA_HERDER:-25001}"
CONFIG="$ROOT/tools/llama-swap/config.yaml"

# Use the binary you built with embed_ui
BINARY="$ROOT/projects/llama-swap-main/llama-swap"

[[ -x "$BINARY" ]] || { echo "FATAL: $BINARY not found or not executable (did you build with -tags=embed_ui ?)"; exit 1; }

fuser -k "${PROXY_PORT}/tcp" 2>/dev/null || true

echo "Starting llama-swap (with embedded UI) on :${PROXY_PORT} ..."
exec "$BINARY" \
  --config "$CONFIG" \
  --listen "127.0.0.1:${PROXY_PORT}"