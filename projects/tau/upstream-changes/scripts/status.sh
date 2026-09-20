#!/usr/bin/env bash
set -euo pipefail
# status.sh — where do we stand vs upstream?
UC="$(cd "$(dirname "$0")/.." && pwd)"
MIRROR=/home/toxic/scratch/oh-my-pi-upstream
ENGINE=/home/toxic/sovereign/projects/tau/engine
WORKROOT=/home/toxic/scratch/tau-merge

CUR="$(grep 'current_version' "$UC/config.yaml" | sed 's/.*"\([0-9.]*\)".*/\1/')"
echo "== tau upstream status =="
echo "engine tracks upstream: $CUR   (fork point v18.1.18)"
if [ -d "$MIRROR/.git" ]; then
  git -C "$MIRROR" fetch --quiet --tags origin 2>/dev/null || true
  LATEST="$(git -C "$MIRROR" tag --list 'v18.*' --sort=-v:refname | head -1)"
  echo "latest upstream tag:  ${LATEST#v}"
  if [ "v$CUR" != "$LATEST" ]; then
    BEHIND="$(git -C "$MIRROR" rev-list --count "v$CUR".."$LATEST" 2>/dev/null || echo '?')"
    echo "behind by: $BEHIND commits — run ./upstream-changes/scripts/upgrade.sh ${LATEST#v}"
  else
    echo "up to date."
  fi
else
  echo "mirror not cloned yet — run ingest.sh"
fi
echo ""
echo "-- merge worktrees --"
ls -d "$WORKROOT"/tau-merge-* 2>/dev/null || echo "(none)"
echo ""
echo "-- recent logs --"
ls -t "$UC/log" 2>/dev/null | head -8 || echo "(no logs yet)"
echo ""
echo "-- engine binary --"
ls -la "$ENGINE/packages/coding-agent/dist/omp" 2>/dev/null || echo "(no binary)"
