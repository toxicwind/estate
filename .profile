#!/usr/bin/env bash
# Sovereign Modular Profile System - absolute, no dynamic dirname
export SOVEREIGN_ROOT="/home/toxic/sovereign"
export SOVEREIGN_PROFILE="${SOVEREIGN_PROFILE:-toxic}"
PROFILE_DIR="${SOVEREIGN_ROOT}/profiles/${SOVEREIGN_PROFILE}"
DEFAULT_DIR="${SOVEREIGN_ROOT}/profiles/default"
if [ -f "${PROFILE_DIR}/env.sh" ]; then
    . "${PROFILE_DIR}/env.sh"
elif [ -f "${DEFAULT_DIR}/env.sh" ]; then
    . "${DEFAULT_DIR}/env.sh"
fi
export SOVEREIGN_PROFILE
export SOVEREIGN_ROOT
