#!/usr/bin/env bash
# llama-swap direct-bind launcher — binds Go binary to 0.0.0.0:LLAMA_SWAP_PORT (25100).
# No proxy/middleware hop. mesh-hub (25115) serves 20 GHAS /mesh/* features for the mesh.
set -euo pipefail
SOV="$HOME/sovereign"
source "$SOV/stack/lib-ports.sh"
require_env LLAMA_SWAP_PORT
PORT="$LLAMA_SWAP_PORT"
BIN="$HOME/projects/llama-swap-main/llama-swap"
[[ -x "$BIN" ]] || { echo "llama-swap bin not found at $BIN" >&2; exit 1; }
CONF="$SOV/config/llama-swap.yaml"
[[ -f "$CONF" ]] || { echo "llama-swap config not found at $CONF" >&2; exit 1; }

# Kill any existing llama-swap on this port
fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 0.3

# Launch Go binary — direct bind to 0.0.0.0:PORT (no proxy hop)
"$BIN" --config "$CONF" --listen "0.0.0.0:${PORT}" &
BPID=$!
cleanup() { kill "$BPID" 2>/dev/null || true; }
trap cleanup EXIT TERM INT

# Wait for health endpoint (max 15s)
for i in $(seq 1 40); do
  if curl -sf -m 0.3 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then break; fi
  sleep 0.25
done

# Keep the script running (waits for the Go binary)
wait "$BPID"
