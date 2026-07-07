#!/usr/bin/env bash
# Tombstone — kill any leftover nix/devenv artifacts; start pacman stack
set -euo pipefail

SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
log() { printf '[kill-nix] %s\n' "$*"; }

log "Stopping nix-daemon..."
sudo systemctl stop nix-daemon.socket nix-daemon.service 2>/dev/null || true
sudo systemctl disable nix-daemon.socket nix-daemon.service 2>/dev/null || true

log "Killing devenv/nix stragglers..."
pkill -f 'devenv-wrapped|nix-daemon|determinate-nixd' 2>/dev/null || true
sleep 1

log "Freeing :25001 (llama-swap owns upstream)..."
fuser -k 25001/tcp 2>/dev/null || true

uid="$(id -u)"
rm -rf "/run/user/${uid}/devenv-"* 2>/dev/null || true

if command -v nix >/dev/null 2>&1 || [[ -d /nix ]]; then
  log "WARN: nix still present — run: sudo pacman -Rns nix nix-busybox"
else
  log "nix binary/store: absent (ok)"
fi

log "Starting sovereign core stack..."
"$SOV/stack/up.sh" -D core 2>/dev/null || true

log "Done. Orchestrator: mise+process-compose (:25021 ingress)"