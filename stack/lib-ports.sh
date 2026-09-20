#!/usr/bin/env bash
# Source port SSOT for shell services. No numeric defaults in callers.
SOV="$HOME/sovereign"
# shellcheck disable=SC1091
set -a
# shellcheck source=/dev/null
[[ -f "$SOV/config/ports.env" ]] && . "$SOV/config/ports.env"
# shellcheck source=/dev/null
[[ -f "$SOV/.env.local" ]] && . "$SOV/.env.local"
set +a

require_env() {
  local n="$1"
  if [[ -z "${!n:-}" ]]; then
    echo "missing $n — set in $SOV/config/ports.env" >&2
    return 1
  fi
}

# require_port VAR — require_env + numeric + valid TCP/UDP port range.
# Fails fast with a clear message instead of letting a downstream binary
# die cryptically (e.g. llama-server "stoi" usage dump on --port).
require_port() {
  local n="$1" v="${!1:-}"
  require_env "$n" || return 1
  if ! [[ "$v" =~ ^[0-9]+$ ]]; then
    echo "invalid $n=[$v] — must be numeric (got non-digit chars)" >&2
    return 1
  fi
  if (( v < 1 || v > 65535 )); then
    echo "invalid $n=[$v] — out of port range 1-65535" >&2
    return 1
  fi
}
