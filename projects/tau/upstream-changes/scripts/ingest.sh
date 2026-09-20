#!/usr/bin/env bash
set -euo pipefail
# ingest.sh [target-version] — the airlock.
# Fetches upstream into the mirror clone, computes the PURE upstream delta
# (fork_point_tag..target), and classifies every changed file against the
# sovereign delta: upstream-only (safe), overlap (will need 3-way merge).
# Nothing touches the engine tree.
#
# Usage: ./upstream-changes/scripts/ingest.sh [18.2.6]
#   no arg -> latest v18.* tag in the mirror.

UC="$(cd "$(dirname "$0")/.." && pwd)"
MIRROR=/home/toxic/scratch/oh-my-pi-upstream
ENGINE=/home/toxic/sovereign/projects/tau/engine
BASE_TAG=v18.1.18
LOGDIR="$UC/log"; PATCHDIR="$UC/patches"
mkdir -p "$LOGDIR" "$PATCHDIR"

# --- mirror clone (airlock) ---
if [ ! -d "$MIRROR/.git" ]; then
  echo "Cloning upstream mirror..."
  git clone --quiet https://github.com/can1357/oh-my-pi.git "$MIRROR"
fi
git -C "$MIRROR" fetch --quiet --tags origin 2>&1 | tail -2 || true

# --- resolve target ---
if [ -n "${1:-}" ]; then
  TARGET="v${1#v}"
else
  TARGET="$(git -C "$MIRROR" tag --list 'v18.*' --sort=-v:refname | head -1)"
fi
if ! git -C "$MIRROR" rev-parse --verify --quiet "$TARGET" >/dev/null; then
  echo "ERROR: target $TARGET not found in mirror" >&2; exit 1
fi
STAMP="$(date +%Y-%m-%d)"
LOG="$LOGDIR/ingestion-$STAMP-${TARGET#v}.md"
{
echo "# Ingestion $STAMP — target $TARGET"
echo "Base: $BASE_TAG (verified fork point) -> Target: $TARGET"
echo ""
echo "## Upstream delta ($BASE_TAG..$TARGET)"
git -C "$MIRROR" diff --stat "$BASE_TAG".."$TARGET" | tail -3
echo ""
UP_FILES="$(git -C "$MIRROR" diff --name-only "$BASE_TAG".."$TARGET" | sort)"
UP_COUNT="$(echo "$UP_FILES" | grep -c . || true)"
echo "Upstream changed files: $UP_COUNT"
echo ""
echo "## Sovereign delta (engine vs $BASE_TAG tree)"
SOV_TMP="$(mktemp -d)"
export SOV_TMP ENGINE
git -C "$MIRROR" archive "$BASE_TAG" | tar -x -C "$SOV_TMP"
SOV_FILES="$(diff -rq "$SOV_TMP" "$ENGINE" 2>/dev/null | python3 -c "
import sys, os
base = os.environ.get('SOV_TMP',''); eng = os.environ.get('ENGINE','')
skip = ('node_modules','/.git/','/dist/','/vendor/','/runs/','/.omp/','/.nanocoder/')
for line in sys.stdin:
    line = line.rstrip('\n')
    p = None
    if line.startswith('Files ') and ' differ' in line:
        # Files <tmp>/rel and <eng>/rel differ
        a = line[6:].split(' and ')[0]
        p = os.path.relpath(a, base)
    elif line.startswith('Only in '):
        d, f = line[8:].split(': ', 1)
        d = d.strip()
        if d == eng or d.startswith(eng + '/'):
            p = os.path.relpath(os.path.join(d, f.strip()), eng)
        elif d == base or d.startswith(base + '/'):
            p = os.path.relpath(os.path.join(d, f.strip()), base)
    if p and not any(s in '/' + p + '/' for s in skip):
        print(p)
" | sort -u || true)"
SOV_COUNT="$(echo "$SOV_FILES" | grep -c . || true)"
echo "Sovereign-delta files: $SOV_COUNT"
echo ""
echo "## Classification"
OVERLAP="$(comm -12 <(echo "$UP_FILES") <(echo "$SOV_FILES"))"
OV_COUNT="$(echo "$OVERLAP" | grep -c . || true)"
UP_ONLY_COUNT=$((UP_COUNT - OV_COUNT))
echo "- upstream-only (clean apply expected): $UP_ONLY_COUNT"
echo "- overlap (both sides touched — 3-way merge will decide): $OV_COUNT"
echo ""
echo "### Overlap files (sovereign edits that upstream also touched)"
echo '```'
echo "$OVERLAP"
echo '```'
echo ""
echo "Next: ./upstream-changes/scripts/merge.sh ${TARGET#v}   (3-way merge in a worktree)"
} | tee "$LOG"
rm -rf "$SOV_TMP"
git -C "$MIRROR" format-patch --stdout "$BASE_TAG".."$TARGET" > "$PATCHDIR/$STAMP-upstream-${TARGET#v}.patch" 2>/dev/null || true
echo "Log: $LOG"
