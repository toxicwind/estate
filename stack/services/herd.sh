#!/usr/bin/env bash
# herd (llama-swap) loopback launcher — binds Go binary to 127.0.0.1:HERD_PORT (25100).
# Renamed from llama-swap.sh — project-wide herd naming, llama-swap binary kept for compatibility.
# No proxy/middleware hop. mesh-hub (25115) serves 20 GHAS /mesh/* features.
# Config: --config <main> plus --config-dir /home/toxic/kimi-auto/herd.d
# (additive, watch-config hot-reload) for the kimi-auto virtual model.
# Lifecycle is owned by pitchfork (supervisor); this script does NOT kill or
# steal the port — if the bind fails, pitchfork sees the failure and retries.
set -euo pipefail
SOV="$HOME/sovereign"
source "$SOV/stack/lib-ports.sh"
require_env HERD_PORT
# Canonical secrets for provider keyEnvs (FLOCK_API_KEY, OPENROUTER_API_KEY, ...).
# Sourced, never copied — keys stay in /home/toxic/.secrets.
if [[ -f /home/toxic/.secrets ]]; then
  set -a
  set +u  # .secrets has forward refs (e.g. ${NVIDIA_API_KEY}); don't crash
  source /home/toxic/.secrets
  set -u
  set +a
fi
PORT="$HERD_PORT"
BIN="$HOME/projects/sovereign-projects/sovereign-swap/build/llama-swap"
[[ -x "$BIN" ]] || { echo "herd (llama-swap) bin not found at $BIN" >&2; exit 1; }
CONF="$SOV/config/herd.yaml"
[[ -f "$CONF" ]] || CONF="$SOV/config/llama-swap.yaml"
[[ -f "$CONF" ]] || { echo "herd config not found at $CONF" >&2; exit 1; }

# Launch Go binary — loopback bind only (no 0.0.0.0 exposure)
"$BIN" --config "$CONF" --config-dir /home/toxic/kimi-auto/herd.d --watch-config --listen "127.0.0.1:${PORT}" &
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
