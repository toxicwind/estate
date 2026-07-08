#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ports.env
source "$SCRIPT_DIR/ports.env"

checks=(
  "${LLAMA_HERDER}:llama-swap:/health"
  "${OPENFANG_PORT}:openfang:/api/health"
  "${PROMETHEUS_PORT}:prometheus:/-/healthy"
  "${YOTE_PORT}:yote:/health"
  "${RUST_WEB_PORT}:rust-dash:/health"
  "${HF_DOWNLOADER}:hf-downloader:/health"
  "${WATCHDOG_PORT}:watchdog:/health"
  "${LANDING_PORT}:landing:/health"
)

for spec in "${checks[@]}"; do
  IFS=: read -r port name path <<<"$spec"
  if curl -sf --max-time 2 "http://127.0.0.1:${port}${path}" >/dev/null 2>&1 || \
     curl -sf --max-time 2 "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
    printf 'UP   :%s %s\n' "$port" "$name"
  else
    printf 'DOWN :%s %s\n' "$port" "$name"
  fi
done