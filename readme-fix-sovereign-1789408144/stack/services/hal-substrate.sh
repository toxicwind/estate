#!/usr/bin/env bash
# HAL Substrate v3.1 — Autonomous Agent Inference Engine
# First-class sovereign service. OpenFang agent with Yote integration.
# Routes through AST matrix (llama-swap :25100) with 14 providers.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_env HAL_SUBSTRATE_PORT
PORT="$HAL_SUBSTRATE_PORT"

# Find hal-loop.py — sovereign src/ is canonical
BIN_CAND=(
  "$SOV/src/hal-substrate/hal-loop.py"
  "$HOME/projects/project-name/src/hal-loop.py"
)
BIN=""
for c in "${BIN_CAND[@]}"; do
  [[ -f "$c" ]] && BIN="$c" && break
done

if [[ -z "$BIN" ]]; then
  echo "[hal-substrate] hal-loop.py not found" >&2
  exit 1
fi

# Verify deps
if ! python3 -c "import requests" 2>/dev/null; then
  python3 -m pip install requests urllib3 --quiet
fi

# Kill existing
fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 0.3

# Launch: HTTP server on 0.0.0.0:PORT
# Connects to llama-swap AST matrix, integrates with Yote messaging
exec python3 "$BIN" \
  --base-url "http://127.0.0.1:25100" \
  --api-key "sk-hal-local" \
  --model "kimi-auto" \
  --session "sovereign-$(date +%s)" \
  --port "${PORT}" \
  --host "0.0.0.0" \
  --verbose
