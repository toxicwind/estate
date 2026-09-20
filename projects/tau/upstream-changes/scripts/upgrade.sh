#!/usr/bin/env bash
set -euo pipefail
# upgrade.sh [target-version] — the one-command version update.
# Runs ingest (airlock analysis) + merge (3-way in worktree), then STOPS.
# Promotion to the live engine is a separate explicit step: promote.sh <ver>
# Usage: ./upstream-changes/scripts/upgrade.sh [18.2.6]
UC="$(cd "$(dirname "$0")/.." && pwd)"
"$UC/scripts/ingest.sh" "$@"
echo ""
echo "================ ingest done ================"
echo ""
"$UC/scripts/merge.sh" "$@"
echo ""
echo "================ merge done ================"
echo "Review the worktree, resolve conflicts, then:"
echo "  $UC/scripts/promote.sh <version>"
