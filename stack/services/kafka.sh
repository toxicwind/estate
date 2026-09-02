#!/usr/bin/env bash
# Kafka service — Sovereign stack
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh" 2>/dev/null || true
PORT="${KAFKA_PORT:-9092}"

fuser -k "${PORT}/tcp" 2>/dev/null || true

export KAFKA_LOG4J_OPTS="-Dkafka.logs.dir=$HOME/.local/state/kafka/logs"
mkdir -p "$HOME/.local/state/kafka/logs"
exec sudo -u kafka /usr/share/kafka/bin/kafka-server-start.sh /etc/kafka/server.properties

# If rpk redpanda server binary is available, run Redpanda in KRaft mode
if [[ -x "$HOME/.local/bin/redpanda" ]]; then
  exec "$HOME/.local/bin/rpk" redpanda start --kafka-addr "0.0.0.0:${PORT}"
fi

# Last resort stub
echo "[kafka] No broker found, serving stub on port ${PORT}"
exec python3 -m http.server "${PORT}"
