#!/usr/bin/env bash
# Prometheus on backend port + mesh-front on public PROMETHEUS_PORT; yml reload still works via backend.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
cd "$SOV"
# shellcheck source=../lib-ports.sh
source "$(dirname "$0")/../lib-ports.sh"
PORT="${PROMETHEUS_PORT:?}"
BACKEND="${PROMETHEUS_BACKEND_PORT:-26105}"

fuser -k "${PORT}/tcp" 2>/dev/null || true
fuser -k "${BACKEND}/tcp" 2>/dev/null || true

prometheus \
  --config.file=./prometheus.yml \
  --storage.tsdb.path=./.prometheus \
  --web.listen-address=127.0.0.1:${BACKEND} \
  --web.enable-lifecycle &
PROM_PID=$!
echo "[prom-hot] prometheus backend pid $PROM_PID :${BACKEND}"

cleanup() {
  kill "$PROM_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup EXIT

for i in $(seq 1 40); do
  curl -sf -m 0.3 "http://127.0.0.1:${BACKEND}/-/healthy" >/dev/null 2>&1 && break
  sleep 0.2
done

/home/toxic/.bun/bin/bun run "$SOV/src/services/mesh-front.ts" \
  --service prometheus \
  --listen "0.0.0.0:${PORT}" \
  --backend "127.0.0.1:${BACKEND}" &
FRONT_PID=$!

while inotifywait -qq -e modify -e attrib -e moved_to ./prometheus.yml; do
  echo "[prom-hot] change detected -> reloading"
  curl -fsS -X POST "http://127.0.0.1:${BACKEND}/-/reload" \
    && echo "[prom-hot] reloaded ok" \
    || echo "[prom-hot] reload failed"
done
