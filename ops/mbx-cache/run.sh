#!/usr/bin/env bash
# mbx-cache launcher — estate mise remote task cache server (:25148).
#
# Contract (mbx-cache skill): daemon pitchfork [daemons.mbx-cache], port
# MBX_CACHE_PORT=25148 (config/ports.env), binary from vendored mr-boxington-cache
# cargo release build, data at var/runtime/mbx-cache. Loopback-only + anonymous
# (nothing outside the host can reach it).
set -euo pipefail

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BIN="${MBX_CACHE_BIN:-$BASE/ranch/vendored/mr-boxington-cache/target/release/mbx-cache}"
PORT="${MBX_CACHE_PORT:-25148}"
DATA="${MBX_CACHE_DATA:-$BASE/var/runtime/mbx-cache}"
LISTEN="127.0.0.1:${PORT}"

if [ ! -x "$BIN" ]; then
  echo "mbx-cache: binary not built: $BIN (run: cd $BASE/ranch/vendored/mr-boxington-cache && cargo build --release)" >&2
  exit 1
fi

mkdir -p "$DATA"
exec "$BIN" --allow-anonymous --data-dir "$DATA" --listen "$LISTEN"