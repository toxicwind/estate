#!/usr/bin/env bash
# HAL Substrate — Autonomous agent inference engine
# Connects to llama-swap (:25100) via OpenAI-compatible API
# Does NOT run its own inference — uses sovereign's AST matrix
set -euo pipefail

SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_env HAL_SUBSTRATE_PORT
PORT="$HAL_SUBSTRATE_PORT"

# HAL substrate lives in user's projects directory
HAL_DIR="${HAL_DIR:-$HOME/projects/hal-substrate}"
HAL_BIN="$HAL_DIR/src/hal-loop.py"

# Fallback: check common locations
if [[ ! -f "$HAL_BIN" ]]; then
  HAL_CAND=(
    "$HOME/projects/project-name/src/hal-loop.py"
    "$HOME/projects/hal-substrate-v3/src/hal-loop.py"
    "$HOME/github/hal-substrate/src/hal-loop.py"
  )
  for c in "${HAL_CAND[@]}"; do
    [[ -f "$c" ]] && HAL_BIN="$c" && break
  done
fi

if [[ ! -f "$HAL_BIN" ]]; then
  echo "[hal-substrate] hal-loop.py not found. Expected at $HAL_DIR/src/hal-loop.py" >&2
  echo "[hal-substrate] Install: tar -xzf hal-substrate-v3.tar.gz -C ~/projects/" >&2
  exit 1
fi

# Verify Python deps
if ! python3 -c "import requests" 2>/dev/null; then
  echo "[hal-substrate] Installing Python deps..."
  python3 -m pip install requests urllib3 --quiet
fi

# Kill existing
fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 0.3

# Launch HAL loop in daemon mode
# Connects to llama-swap on :25100 (AST matrix with 14 providers)
exec python3 "$HAL_BIN" \
  --base-url "http://127.0.0.1:25100" \
  --api-key "sk-hal-local" \
  --model "kimi-auto" \
  --session "sovereign-$(date +%s)" \
  --verbose \
  --task "[HAL] Sovereign substrate initialized. Waiting for tasks via API."
