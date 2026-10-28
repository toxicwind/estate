#!/usr/bin/env bash
# estate/scripts/secret-scan.sh — FAST hardcoded-key check for the estate.
#
# Why: `gitleaks detect` with default config + --log-opts=--all walks the whole
# 325K-file / 63-submodule estate INCLUDING git history — it crawls for minutes
# and flags upstream test fixtures. This script is scoped and fast:
#
#   - scoped --source to a repo dir (default: run from the repo root you're in)
#   - --no-git (working-tree files only; the global pre-commit/pre-push hooks in
#     ops/git-hooks/ already gate every commit/push on staged secrets)
#   - the scoped estate config (config/gitleaks/gitleaks.toml) ignores
#     vendored/upstream/test-fixture bulk so results are coherent-author only.
#
# Usage:
#   secret-scan                          # scan current dir (working tree)
#   secret-scan /path/to/repo            # scan a specific repo
#   secret-scan --staged                 # scan the staged index only
set -uo pipefail

# Canonical gate config (proven; used by the global hooks in ops/git-hooks/).
CFG="/home/toxic/pens/estate/ops/git-hooks/gitleaks.toml"
[ -f "$CFG" ] || { echo "config not found: $CFG" >&2; exit 2; }

SRC="."
STAGED=0
for a in "$@"; do
  case "$a" in
    --staged) STAGED=1 ;;
    *) SRC="$a" ;;
  esac
done

if [ "$STAGED" -eq 1 ]; then
  gitleaks detect --config "$CFG" --staged --no-banner
else
  gitleaks detect --config "$CFG" --source "$SRC" --no-git --no-banner
fi
rc=$?
echo "[secret-scan] exit=$rc"
exit $rc