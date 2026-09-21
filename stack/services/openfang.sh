#!/usr/bin/env bash
# OpenFang public front — mesh-front proxy on OPENFANG_PORT -> OPENFANG_KERNEL_PORT.
# (The kernel itself is pitchfork daemons.openfang on :25196 and owns its own
# lifecycle via ops/openfang-run.sh. This service never spawns the openfang
# binary — see src/services/openfang.ts.)
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_port OPENFANG_PORT
PORT="$OPENFANG_PORT"

fuser -k "${PORT}/tcp" 2>/dev/null || true
if [[ -f "$SOV/src/services/openfang.ts" ]]; then
  exec /home/toxic/.bun/bin/bun run "$SOV/src/services/openfang.ts"
fi
echo "[openfang] TS entry not found at $SOV/src/services/openfang.ts" >&2
exit 1
