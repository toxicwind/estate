#!/usr/bin/env bash
# Shared stack helpers — system packages only (no nix/devbox)
set -euo pipefail

STACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOV="${SOVEREIGN_ROOT:-$(cd "$STACK_ROOT/.." && pwd)}"
export SOVEREIGN_ROOT="$SOV"

# shellcheck source=ports.env
source "$STACK_ROOT/ports.env"
# shellcheck source=profiles.sh
source "$STACK_ROOT/profiles.sh"

mkdir -p "$SOV/.state/logs" "$SOV/.prometheus"

stack_configs() {
  local profile="${1:-core}"
  local -a mods
  mapfile -t mods < <(stack_profile_modules "$profile")
  printf '%s\n' "$SOV/stack/base.yaml"
  local m
  for m in "${mods[@]}"; do
    printf '%s\n' "$SOV/stack/modules/${m}.yaml"
  done
}

run_pc() {
  command -v process-compose >/dev/null || {
    echo "process-compose not found — install: sudo pacman -S process-compose-git prometheus" >&2
    exit 1
  }
  # Force IPv4 loopback globally to prevent Go's ::1 resolution panics on up/down/attach
  process-compose --address 127.0.0.1 "$@"
}

pc_config_args() {
  local profile="${1:-core}"
  local -a args=() cfg
  while IFS= read -r cfg; do
    args+=(-f "$cfg")
  done < <(stack_configs "$profile")
  printf '%s\0' "${args[@]}"
}