#!/usr/bin/env bash
set -euo pipefail
# promote.sh <target-version> — verify the merge worktree, then adopt it as the engine.
# Steps: no unresolved conflicts -> bun install -> tsc -> tests -> build binary ->
# smoke test -> backup engine -> rsync in -> bump config version -> commit.
# Any failure stops before the engine is touched.
#
# Usage: ./upstream-changes/scripts/promote.sh 18.2.6

UC="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE=/home/toxic/sovereign/projects/tau/engine
WORKROOT=/home/toxic/scratch/tau-merge
TARGET="${1:?Usage: $0 <target-version, e.g. 18.2.6>}"
TARGET="v${TARGET#v}"
WT="$WORKROOT/tau-merge-${TARGET#v}"
LOGDIR="$UC/log"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/promote-$(date +%Y-%m-%d)-${TARGET#v}.md"

[ -e "$WT/.git" ] || { echo "ERROR: no merge worktree at $WT — run merge.sh first"; exit 1; }
cd "$WT"

echo "=== 1. conflict check ==="
LEFT="$(git diff --name-only --diff-filter=U)"
if [ -n "$LEFT" ]; then echo "ERROR: unresolved conflicts:"; echo "$LEFT"; exit 1; fi
git commit -qm "merge upstream $TARGET into sovereign delta" || true
echo "clean."

echo "=== 2. bun install ==="
bun install --frozen-lockfile 2>&1 | tail -2

echo "=== 3. check:types (all packages — upstream's own type gate) ==="
# Upstream CI runs per-package `check:types` (tsgo --noEmit), NOT root tsc -b
# and NOT tsc on a single package. Match their gate exactly.
TSC_FAIL=0
for pkg in "$WT"/packages/*/; do
  name=$(basename "$pkg")
  if grep -q '"check:types"' "$pkg/package.json" 2>/dev/null; then
    if out=$(bun --cwd "$pkg" run check:types 2>&1); then
      echo "  ok: $name"
    else
      echo "  FAIL: $name"
      echo "$out" | grep -E 'error TS' | head -5
      TSC_FAIL=1
    fi
  fi
done
[ "$TSC_FAIL" -eq 0 ] || { echo "typecheck failed — not promoting"; exit 1; }
echo "check:types clean."

echo "=== 4. tests (ai package) ==="
bun --cwd "$WT/packages/ai" test 2>&1 | tail -5

echo "=== 5. build binary ==="
bun --cwd "$WT/packages/coding-agent" run scripts/build-binary.ts 2>&1 | tail -3
[ -x "$WT/packages/coding-agent/dist/omp" ] || { echo "ERROR: binary not built"; exit 1; }

echo "=== 6. smoke test ==="
"$WT/packages/coding-agent/dist/omp" --version
echo "$WT/packages/coding-agent/dist/omp" | grep -q . || true

{
echo "# Promote $(date +%Y-%m-%d) — $TARGET"
echo "- Worktree: $WT"
echo "- Checks: conflicts=0, tsc, tests, binary build, smoke test — all passed"
} | tee "$LOG"

echo "=== 7. adopt: backup engine, rsync merged tree in ==="
BACKUP="/home/toxic/sovereign/projects/tau/engine.bak-$(date +%Y%m%d-%H%M%S)"
cp -a "$ENGINE" "$BACKUP"
echo "Engine backed up to $BACKUP"
rsync -a --delete \
  --exclude='.git' --exclude='node_modules/' --exclude='dist/' \
  --exclude='vendor/' --exclude='runs/' --exclude='.omp/' --exclude='.nanocoder/' \
  "$WT/" "$ENGINE/"
# ship the freshly built binary too
cp "$WT/packages/coding-agent/dist/omp" "$ENGINE/packages/coding-agent/dist/omp"

echo "=== 8. bump tracked version ==="
python3 - "$UC/config.yaml" "${TARGET#v}" <<'PYEOF'
import sys, re
cfg, ver = sys.argv[1], sys.argv[2]
s = open(cfg).read()
s = re.sub(r'(current_version:\s*")[^"]*(")', r'\g<1>' + ver + r'\g<2>', s)
open(cfg, 'w').write(s)
print("config current_version ->", ver)
PYEOF

echo "=== 9. commit ==="
git -C /home/toxic/sovereign/projects/tau add -A 2>/dev/null || true
echo "Review: git -C /home/toxic/sovereign/projects/tau status --short | head"
echo "Then:  git -C /home/toxic/sovereign/projects/tau commit -m 'chore(upstream): merge $TARGET (3-way, sovereign delta preserved)'"
echo "Promote complete. Log: $LOG"
