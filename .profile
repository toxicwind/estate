#!/usr/bin/env bash
# ==============================================================================
# /home/toxic/sovereign/.profile — Sovereign Modular Profile Entrypoint
# ==============================================================================
SOVEREIGN_ROOT="${SOVEREIGN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
export SOVEREIGN_ROOT

if [ -f "${SOVEREIGN_ROOT}/profiles/loader.sh" ]; then
    . "${SOVEREIGN_ROOT}/profiles/loader.sh"
fi
