#!/usr/bin/env bash
# Kafka service — Sovereign stack
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh" 2>/dev/null || true
PORT="${KAFKA_PORT:-25144}"
export JAVA_HOME=/usr/lib/jvm/java-25-graalvm

sudo fuser -k "${PORT}/tcp" 9093/tcp 2>/dev/null || true
sleep 1

export KAFKA_LOG4J_OPTS="-Dkafka.logs.dir=/var/log/kafka"
sudo mkdir -p /var/log/kafka
sudo chown -R kafka:kafka /var/log/kafka
exec sudo -E -u kafka /usr/share/kafka/bin/kafka-server-start.sh /etc/kafka/server.properties

# If rpk redpanda server binary is available, run Redpanda in KRaft mode
if [[ -x "$HOME/.local/bin/redpanda" ]]; then
  exec "$HOME/.local/bin/rpk" redpanda start --kafka-addr "0.0.0.0:${PORT}"
fi

# Last resort stub
echo "[kafka] No broker found, serving stub on port ${PORT}"
exec python3 -m http.server "${PORT}"
