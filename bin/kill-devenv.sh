#!/usr/bin/env bash
# Permanently stop devenv orchestration — sovereign uses devbox+mise+process-compose.
set -euo pipefail

SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
ARCHIVE="${HOME}/.archive/consolidation-$(date +%Y-%m-%d)"

log() { printf '[kill-devenv] %s\n' "$*"; }

mkdir -p "$ARCHIVE/devenv-tombstone"

log "Stopping devenv processes..."
cd "$SOV"
devenv processes down 2>/dev/null || true
devenv down 2>/dev/null || true

log "Killing devenv daemons..."
pkill -f 'devenv-wrapped daemon-processes' 2>/dev/null || true
pkill -f 'devenv processes' 2>/dev/null || true
pkill -f '/devenv up' 2>/dev/null || true
sleep 1

log "Freeing :25001 from devenv llama-server (swap owns upstream on demand)..."
fuser -k 25001/tcp 2>/dev/null || true

if [[ -f "$SOV/devenv.yaml" && ! -f "$SOV/devenv.yaml.disabled" ]]; then
  mv "$SOV/devenv.yaml" "$SOV/devenv.yaml.disabled"
  log "Renamed devenv.yaml -> devenv.yaml.disabled"
fi

uid="$(id -u)"
devenv_run="/run/user/${uid}/devenv-8f1eeea"
if [[ -d "$devenv_run" ]]; then
  cp -a "${devenv_run}/processes/daemon-config.json" \
    "$ARCHIVE/devenv-tombstone/" 2>/dev/null || true
fi

log "Ensuring devbox stack is up (core, swap-only)..."
eval "$(devbox shellenv --init-hook 2>/dev/null)" || true
"$SOV/bin/sovereign-stack.sh" up-d core 2>/dev/null || true

log "Done. Orchestrator: devbox+mise+process-compose (:25021 ingress)"