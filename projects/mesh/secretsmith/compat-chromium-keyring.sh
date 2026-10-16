#!/bin/sh
# compat-chromium-keyring.sh - muscle-memory shim over secretsmith.
# The old 'key' subcommand is gone on purpose: the raw os_crypt secret is
# never printed. One truth lives in secretsmith.

DIR="$(cd "$(dirname "$0")" && pwd)"
SM="$DIR/bin/secretsmith"

case "${1:-}" in
  check) exec "$SM" check ;;
  attrs) exec "$SM" search --schema chromium ;;
  *) echo "usage: chromium-keyring {check|attrs}" >&2; exit 1 ;;
esac
