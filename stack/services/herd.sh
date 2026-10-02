#!/usr/bin/env bash
# herd (llama-swap) loopback launcher — binds Go binary to 127.0.0.1:HERD_PORT (25100).
# Renamed from llama-swap.sh — project-wide herd naming, llama-swap binary kept for compatibility.
# No proxy/middleware hop. mesh-hub (25115) serves 20 GHAS /mesh/* features.
# Config: --config <main> plus --config-dir /home/toxic/kimi-auto/herd.d
# (additive, watch-config hot-reload) for the kimi-auto virtual model.
# Lifecycle is owned by pitchfork (supervisor); this script does NOT kill or
# steal the port — if the bind fails, pitchfork sees the failure and retries.
set -euo pipefail
SOV="/home/toxic/estate"
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

# The binary lives beside its source in ranch/herd, not under var/ (var/ is
# runtime state, and a launcher that points there means the path rots the next
# time var/ is swept). The var/llama-swap-backups copy is the last-known-good
# restore point if the in-tree build is ever lost.
for BIN in \
  "$SOV/ranch/herd/herd" \
  "$SOV/var/herd-backups/herd/herd"
do
  [[ -x "$BIN" ]] && break
  BIN=""
done
[[ -n "$BIN" ]] || { echo "herd bin not found in ranch/herd or var/llama-swap-backups/herd" >&2; exit 1; }
CONF="$SOV/config/herd.yaml"
[[ -f "$CONF" ]] || CONF="$SOV/config/llama-swap.yaml"
[[ -f "$CONF" ]] || { echo "herd config not found at $CONF" >&2; exit 1; }

# Launch Go binary — loopback bind only (no 0.0.0.0 exposure).
# exec replaces this shell so the supervisor tracks the ACTUAL server PID,
# not a bash wrapper (2026-09-18: fixes stale-ownership where wrapper PID
# != server PID). pitchfork ready_http gates on /health; no background+wait.
exec "$BIN" --config "$CONF" --config-dir /home/toxic/kimi-auto/herd.d --watch-config --listen "127.0.0.1:${PORT}"
