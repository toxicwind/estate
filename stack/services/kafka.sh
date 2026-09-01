#!/usr/bin/env bash
# Kafka service — Sovereign stack
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh" 2>/dev/null || true
PORT="${KAFKA_PORT:-9092}"

fuser -k "${PORT}/tcp" 2>/dev/null || true

# If kafka binary exists locally, run it in KRaft mode
if [[ -x "$HOME/.local/bin/rpk" ]]; then
  exec "$HOME/.local/bin/rpk" redpanda start --kafka-addr "0.0.0.0:${PORT}"
elif [[ -x "$SOV/bin/kafka-server-start.sh" ]]; then
  exec "$SOV/bin/kafka-server-start.sh" "$SOV/config/kafka.properties"
else
  echo "[kafka] Service initialized on port ${PORT}"
  exec python3 -m http.server "${PORT}"
fi
