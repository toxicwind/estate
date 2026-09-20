#!/usr/bin/env bash
set -euo pipefail
# merge.sh [target-version] — 3-way merge of upstream into our fork, in a worktree.
# The engine is not a git child of upstream, so we synthesize the DAG:
#   1. worktree at fork_point_tag (v18.1.18)          = BASE
#   2. overlay our engine tree, commit                = SOVEREIGN (our delta)
#   3. git merge target tag                           = UPSTREAM delta, 3-way
# Git auto-merges files only one side touched; conflicts = both sides touched.
# Nothing touches the live engine. Result stays in the worktree for review.
#
# Usage: ./upstream-changes/scripts/merge.sh [18.2.6]

UC="$(cd "$(dirname "$0")/.." && pwd)"
MIRROR=/home/toxic/scratch/oh-my-pi-upstream
ENGINE=/home/toxic/sovereign/projects/tau/engine
WORKROOT=/home/toxic/scratch/tau-merge
BASE_TAG=v18.1.18
LOGDIR="$UC/log"; mkdir -p "$LOGDIR"

[ -d "$MIRROR/.git" ] || { echo "Run ingest.sh first (no mirror clone)"; exit 1; }
git -C "$MIRROR" fetch --quiet --tags origin 2>&1 | tail -1 || true

if [ -n "${1:-}" ]; then TARGET="v${1#v}"; else TARGET="$(git -C "$MIRROR" tag --list 'v18.*' --sort=-v:refname | head -1)"; fi
git -C "$MIRROR" rev-parse --verify --quiet "$TARGET" >/dev/null || { echo "ERROR: $TARGET not in mirror"; exit 1; }

WT="$WORKROOT/tau-merge-${TARGET#v}"
STAMP="$(date +%Y-%m-%d)"
LOG="$LOGDIR/merge-$STAMP-${TARGET#v}.md"
rm -rf "$WT"; mkdir -p "$WORKROOT"

echo "Setting up merge worktree at $WT ..."
git -C "$MIRROR" worktree add --detach --force "$WT" "$BASE_TAG" >/dev/null 2>&1
cd "$WT"
git rev-parse --git-dir >/dev/null || { echo "ERROR: worktree git broken at $WT"; exit 1; }
git checkout -qB "sov-merge-${TARGET#v}"

echo "Overlaying engine tree (sovereign delta)..."
rsync -a --delete \
  --exclude='.git' --exclude='node_modules/' --exclude='dist/' --exclude='build/' \
  --exclude='vendor/' --exclude='runs/' --exclude='.omp/' --exclude='.nanocoder/' \
  "$ENGINE/" ./
git add -A
git -c user.name=tau-merge -c user.email=tau-merge@local commit -qm "sovereign delta on $BASE_TAG" || true

echo "Merging upstream $TARGET (3-way)..."
set +e
git merge --no-commit --no-ff "$TARGET" >/tmp/tau-merge-out.txt 2>&1
MERGE_RC=$?
set -e

CONFLICTS="$(git diff --name-only --diff-filter=U | sort)"
CONF_COUNT="$(echo "$CONFLICTS" | grep -c . || true)"
CLEAN="$(git diff --name-only --diff-filter=ACMRT | sort)"
CLEAN_COUNT="$(echo "$CLEAN" | grep -c . || true)"

{
echo "# Merge $STAMP — $BASE_TAG + sovereign delta + $TARGET"
echo ""
echo "- Worktree: $WT (branch sov-merge-${TARGET#v})"
echo "- Merge exit: $MERGE_RC (0=clean, 1=conflicts)"
echo "- Clean-merged files: $CLEAN_COUNT"
echo "- Conflicted files: $CONF_COUNT"
echo ""
echo "## Conflicted files (both sides touched — human review)"
echo '```'
echo "$CONFLICTS"
echo '```'
echo ""
echo "## keep_tau policy hits among conflicts"
while IFS= read -r pat; do
  [ -n "$pat" ] || continue
  hits="$(echo "$CONFLICTS" | grep -E "^${pat//\*/.*}$" || true)"
  [ -n "$hits" ] && { echo "policy $pat:"; echo "$hits"; }
done < <(python3 -c "
import re
keep=False
for line in open('$UC/config.yaml'):
    if 'keep_tau:' in line: keep=True; continue
    if keep:
        m=re.match(r'\s*-\s*\"(.*)\"', line)
        if m: print(m.group(1))
        elif line.strip() and not line.startswith(' '): break
")
echo ""
echo "Next: review conflicts in $WT, resolve, then ./upstream-changes/scripts/promote.sh ${TARGET#v}"
} | tee "$LOG"

echo ""
echo "=== merge done: $CLEAN_COUNT clean, $CONF_COUNT conflicts ==="
echo "Worktree: $WT"
echo "Log: $LOG"
