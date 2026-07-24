#!/usr/bin/env bash
# Grafana on backend port + mesh-front on public GRAFANA_PORT.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
# shellcheck source=../lib-ports.sh
source "$SOV/stack/lib-ports.sh"
PORT="${GRAFANA_PORT:?}"
BACKEND="${GRAFANA_BACKEND_PORT:-26110}"

fuser -k "${PORT}/tcp" 2>/dev/null || true
fuser -k "${BACKEND}/tcp" 2>/dev/null || true

export GF_SERVER_HTTP_PORT="${BACKEND}"
export GF_SERVER_HTTP_ADDR="127.0.0.1"
export GF_SERVER_ROOT_URL="http://127.0.0.1:${PORT}/"
export GF_SERVER_SERVE_FROM_SUB_PATH="false"
export GF_SECURITY_ADMIN_USER="${GF_SECURITY_ADMIN_USER:-admin}"
export GF_USERS_ALLOW_SIGN_UP="false"
export GF_PATHS_PROVISIONING="${GF_PATHS_PROVISIONING:-$SOV/grafana/provisioning}"
export GF_PATHS_DATA="${GF_PATHS_DATA:-$SOV/grafana/data}"
export GF_PATHS_LOGS="${GF_PATHS_LOGS:-$SOV/grafana/logs}"
export GF_PATHS_PLUGINS="${GF_PATHS_PLUGINS:-$SOV/grafana/plugins}"

/usr/bin/grafana server --homepath=/usr/share/grafana --config=/etc/grafana.ini &
GPID=$!
cleanup() { kill "$GPID" 2>/dev/null || true; }
trap cleanup EXIT

for i in $(seq 1 60); do
  curl -sf -m 0.5 "http://127.0.0.1:${BACKEND}/api/health" >/dev/null 2>&1 && break
  sleep 0.3
done

exec /home/toxic/.bun/bin/bun run "$SOV/src/services/mesh-front.ts" \
  --service grafana \
  --listen "0.0.0.0:${PORT}" \
  --backend "127.0.0.1:${BACKEND}"
