#!/usr/bin/env bash
# Sovereign AST Router — Bun TS entry on SOVEREIGN_ROUTER_PORT.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-$HOME/sovereign}"
source "$SOV/stack/lib-ports.sh"
require_env SOVEREIGN_ROUTER_PORT
PORT="$SOVEREIGN_ROUTER_PORT"

fuser -k "${PORT}/tcp" 2>/dev/null || true
exec /home/toxic/.bun/bin/bun --hot run "$SOV/tools/sovereign-router/sovereign-ast-router/server.ts"
