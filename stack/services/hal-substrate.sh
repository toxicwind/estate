#!/usr/bin/env bash
# HAL Substrate — Autonomous agent inference engine
# First-class service. Direct-bind Python daemon to 0.0.0.0:HAL_SUBSTRATE_PORT.
# Connects to llama-swap AST matrix (:25100) via OpenAI-compatible API.
# Does NOT run its own inference — routes through 14 providers (kimi primary).
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_env HAL_SUBSTRATE_PORT
PORT="$HAL_SUBSTRATE_PORT"

# Find hal-loop.py in candidate locations
BIN_CAND=(
  "$HOME/projects/project-name/src/hal-loop.py"
  "$HOME/projects/hal-substrate/src/hal-loop.py"
  "$HOME/projects/hal-substrate-v3/src/hal-loop.py"
  "$HOME/github/hal-substrate/src/hal-loop.py"
)
BIN=""
for c in "${BIN_CAND[@]}"; do
  [[ -f "$c" ]] && BIN="$c" && break
done

if [[ -z "$BIN" ]]; then
  echo "[hal-substrate] hal-loop.py not found. Expected at ~/projects/project-name/src/hal-loop.py" >&2
  echo "[hal-substrate] Install: tar -xzf hal-substrate-v3.tar.gz -C ~/projects/" >&2
  exit 1
fi

# Verify Python deps
if ! python3 -c "import requests" 2>/dev/null; then
  echo "[hal-substrate] Installing Python deps..."
  python3 -m pip install requests urllib3 --quiet
fi

# Kill any existing hal-substrate on this port
fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 0.3

# Launch Python daemon — direct bind to 0.0.0.0:PORT
# HAL runs its own HTTP server for task ingestion + health checks
exec python3 "$BIN" \
  --base-url "http://127.0.0.1:25100" \
  --api-key "sk-hal-local" \
  --model "kimi-auto" \
  --session "sovereign-$(date +%s)" \
  --port "${PORT}" \
  --host "0.0.0.0" \
  --verbose
