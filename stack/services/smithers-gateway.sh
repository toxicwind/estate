#!/usr/bin/env bash
# smithers-gateway.sh — DEPRECATED.
#
# The estate Smithers Gateway singleton has been migrated to Bun/TypeScript:
#   stack/services/smithers-gateway.ts   (#!/usr/bin/env bun, keyring-first)
#   pitchfork.d/smithers-gateway.toml    (port = ${SMITHERS_GATEWAY_PORT} = 25280)
#
# This file is kept as a thin, additive-only compatibility shim so any
# references to the old launcher still work. It simply argv-replaces itself
# with the Bun entrypoint, which is now the source of truth. Do NOT extend
# bash here; put new behavior in the .ts. (ggeenhouse-serve.ts precedent.)
exec /home/toxic/.bun/bin/bun /home/toxic/pens/estate/stack/services/smithers-gateway.ts "$@"