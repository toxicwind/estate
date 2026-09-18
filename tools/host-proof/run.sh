#!/usr/bin/env bash
# host-proof runner -- universal entrypoint.
# Uses the Bun proof bundle when bun is present, otherwise falls back to the
# zero-dependency bash audit. Read-only in both paths.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
export OUT="${OUT:-$HOME/host-proof-$(hostname)-$$-$(date -u +%Y%m%dT%H%M%SZ)}"
if command -v bun >/dev/null 2>&1; then
  exec bun "$HERE/proof-bundle.bun.js"
else
  echo ">> bun not present -- falling back to bash audit (stdout only, no proof bundle)" >&2
  exec bash "$HERE/host-audit.sh" "$@"
fi
