#!/usr/bin/env bash
# mise/tasks/_lib.sh — shared helpers for sovereign stack tasks
set -euo pipefail

export SOV="${SOVEREIGN_ROOT:-{{ config_root }}}"
cd "$SOV"

# Ensure directories exist
mkdir -p "$SOV/.state/logs" "$SOV/.prometheus"

# Build the process-compose -f argument list for a given profile
pc_args() {
  local profile="${1:-sovereign}"
  local -a args=("$SOV/stack/base.yaml")
  case "$profile" in
    core)     local mods=(llama-herder openfang prometheus) ;;
    sovereign) local mods=(llama-herder openfang prometheus yote rust-web) ;;
    full)     local mods=(llama-herder openfang prometheus yote rust-web landing watchdog hf-downloader) ;;
    *) echo "unknown profile: $profile (core|sovereign|full)" >&2; exit 1 ;;
  esac
  for m in "${mods[@]}"; do
    args+=("$SOV/stack/modules/${m}.yaml")
  done
  printf '%s\0' "${args[@]}"
}

# Wrapper that forces IPv4 loopback (avoids Go ::1 panics)
run_pc() {
  process-compose --address 127.0.0.1 "$@"
}
