#!/usr/bin/env bash
# Source-owned VansRouter server from the Ranch stockyard checkout.
# Lifecycle is owned by pitchfork; this wrapper never kills or steals the port.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_port VANSROUTER_PORT

VANS_SECRETS_FILE="${VANSROUTER_SECRETS_FILE:-$HOME/.secrets}"
if [[ -f "$VANS_SECRETS_FILE" ]]; then
  _vans_had_u=0
  [[ "$-" == *u* ]] && _vans_had_u=1
  set +u
  set -a
  # The canonical shell secret store may contain forward references.
  if ! source "$VANS_SECRETS_FILE" >/dev/null 2>&1; then
    set +a
    (( _vans_had_u )) && set -u
    unset _vans_had_u
    echo "VansRouter failed to load secrets file: $VANS_SECRETS_FILE" >&2
    exit 1
  fi
  set +a
  (( _vans_had_u )) && set -u
  unset _vans_had_u
fi

VANS_ENV_FILE="${VANSROUTER_ENV_FILE:-$HOME/.config/vansrouter/env}"
if [[ -f "$VANS_ENV_FILE" ]]; then
  mode="$(stat -c '%a' "$VANS_ENV_FILE")"
  if (( (8#$mode & 077) != 0 )); then
    echo "VansRouter env file must not be group/world readable: $VANS_ENV_FILE" >&2
    exit 1
  fi
  set -a
  source "$VANS_ENV_FILE"
  set +a
fi
: "${API_KEY_SECRET:?set API_KEY_SECRET in $VANS_SECRETS_FILE or $VANS_ENV_FILE}"

APP_DIR="$SOV/projects/range/ranch/stockyard/vansrouter/cli/app"
[[ -f "$APP_DIR/custom-server.js" ]] || {
  echo "VansRouter source build missing: $APP_DIR/custom-server.js" >&2
  exit 1
}

export DATA_DIR="${VANSROUTER_DATA_DIR:-$HOME/.9router}"
export NODE_PATH="$APP_DIR/node_modules:$DATA_DIR/runtime/node_modules${NODE_PATH:+:$NODE_PATH}"
export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1
export PORT="$VANSROUTER_PORT"
export HOSTNAME=127.0.0.1

cd "$APP_DIR"
exec node --enable-source-maps custom-server.js
