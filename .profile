#!/usr/bin/env bash
# Estate Modular Profile System - absolute, no dynamic dirname
export ESTATE_ROOT="/home/toxic/estate"
# legacy alias: old callers still read the retired root variable name
export SOVEREIGN_ROOT="$ESTATE_ROOT"
export ESTATE_PROFILE="${ESTATE_PROFILE:-toxic}"
PROFILE_DIR="${ESTATE_ROOT}/profiles/${ESTATE_PROFILE}"
DEFAULT_DIR="${ESTATE_ROOT}/profiles/default"
if [ -f "${PROFILE_DIR}/env.sh" ]; then
    . "${PROFILE_DIR}/env.sh"
elif [ -f "${DEFAULT_DIR}/env.sh" ]; then
    . "${DEFAULT_DIR}/env.sh"
fi
export ESTATE_PROFILE
export ESTATE_ROOT
