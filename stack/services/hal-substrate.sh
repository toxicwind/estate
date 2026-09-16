#!/usr/bin/env bash
# Compat shim 2026-09-14: hal-substrate.sh was renamed to coyote.sh.
# Maps legacy HAL_SUBSTRATE_PORT to COYOTE_PORT and execs the new script.
set -euo pipefail
export COYOTE_PORT="${COYOTE_PORT:-${HAL_SUBSTRATE_PORT:-25143}}"
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
exec "$SOV/stack/services/coyote.sh"
