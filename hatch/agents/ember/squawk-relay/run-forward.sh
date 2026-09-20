#!/bin/bash
# run-forward.sh: pitchfork launcher for the squawk-relay forwarder (shingle side).
set -euo pipefail
export SQUAWK_RELAY_DIR="${SQUAWK_RELAY_DIR:-/home/toxic/.shingle/squawk-relay}"
export SQUAWK_CHAT_ROOT="${SQUAWK_CHAT_ROOT:-/home/toxic/.shingle/squawk-root}"
export FLEET_KEYS_DIR="${FLEET_KEYS_DIR:-$SQUAWK_CHAT_ROOT/keys}"
export SQUAWK_RELAY_IDENTITY="${SQUAWK_RELAY_IDENTITY:-relay}"
# CANONICAL chat tree (absolute path; survives the shingle symlink reorg).
# The stale mesh checkout (sovereign/projects/mesh/squawk) signs a v3
# canonical form that canonical verify_on_read rejects -- pointing this
# at the mesh checkout fail-closed fleet reads. Never revert to /home/toxic/squawk.
export SQUAWK_CODE_DIR="${SQUAWK_CODE_DIR:-/home/toxic/sovereign/hatch/agents/ember/chat}"
export SQUAWK_RELAY_DEST="${SQUAWK_RELAY_DEST:-fleet}"
exec python3 "$SQUAWK_RELAY_DIR/forward.py"
