#!/usr/bin/env bash
# =============================================================================
# SOVEREIGN — Launch active Web UIs into running Firefox Nightly
# Usage: ./scripts/open-web-uis.sh [--active | --all | --list | --service <id>]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOV_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export BROWSER="${BROWSER:-firefox-nightly}"
export MOZ_ENABLE_WAYLAND=1

exec bun run "$SCRIPT_DIR/open-web-uis.ts" "$@"
