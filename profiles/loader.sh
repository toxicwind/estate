#!/usr/bin/env bash
# ==============================================================================
# Estate Modular Profile Loader
# Usage: source this file or run via /home/toxic/estate/.profile
# ==============================================================================
ESTATE_ROOT="${ESTATE_ROOT:-$HOME/estate}"
ESTATE_PROFILE="${ESTATE_PROFILE:-toxic}"

PROFILE_DIR="${ESTATE_ROOT}/profiles/${ESTATE_PROFILE}"
DEFAULT_DIR="${ESTATE_ROOT}/profiles/default"

if [ -f "${PROFILE_DIR}/env.sh" ]; then
    . "${PROFILE_DIR}/env.sh"
elif [ -f "${DEFAULT_DIR}/env.sh" ]; then
    . "${DEFAULT_DIR}/env.sh"
fi

export ESTATE_PROFILE
export ESTATE_ROOT
