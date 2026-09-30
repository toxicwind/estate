p = "/home/toxic/sovereign/bin/daemon-lint"
src = open(p).read()

old = '''#   (2) node/bun daemon dirs (dir containing package.json): REJECT if there is
#       no committed lockfile (package-lock.json / bun.lock / bun.lockb).'''
new = '''#   (2) node/bun daemon dirs (dir containing package.json): REJECT if there is
#       no committed lockfile in the dir or any parent up to the workspace/git
#       root (package-lock.json / pnpm-lock.yaml / bun.lock / bun.lockb /
#       yarn.lock) -- workspaces keep one lockfile at the root.'''
assert old in src, "header block not found"
src = src.replace(old, new)

old = '''# --- (2) lockfile policy -----------------------------------------------------
if [[ -f "$DIR/package.json" ]]; then
  LOCK=""
  for f in package-lock.json bun.lock bun.lockb; do
    [[ -f "$DIR/$f" ]] && { LOCK="$f"; break; }
  done
  [[ -n "$LOCK" ]] || fail "node/bun dir $DIR has package.json but no lockfile (package-lock.json / bun.lock / bun.lockb) -- commit one (P5)"
  if git -C "$DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$DIR" ls-files --error-unmatch "$LOCK" >/dev/null 2>&1 \\
      || fail "lockfile $DIR/$LOCK exists but is NOT committed -- git add it (P5)"
  fi
fi'''
new = '''# --- (2) lockfile policy -----------------------------------------------------
# Workspace-aware: pnpm/npm/bun/yarn workspaces keep a single lockfile at the
# workspace root, so a daemon dir that is a workspace member satisfies the
# policy through the root lockfile. Walk up from the daemon dir to the git
# work-tree root (or filesystem root) looking for a recognized lockfile.
if [[ -f "$DIR/package.json" ]]; then
  LOCK=""; LOCKDIR=""
  SEARCH="$DIR"
  while [[ -n "$SEARCH" && "$SEARCH" != "/" ]]; do
    for f in package-lock.json pnpm-lock.yaml bun.lock bun.lockb yarn.lock; do
      if [[ -f "$SEARCH/$f" ]]; then LOCK="$f"; LOCKDIR="$SEARCH"; break 2; fi
    done
    if git -C "$SEARCH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      TOP="$(git -C "$SEARCH" rev-parse --show-toplevel)"
      [[ "$SEARCH" == "$TOP" ]] && break
    fi
    SEARCH="$(dirname "$SEARCH")"
  done
  [[ -n "$LOCK" ]] || fail "node/bun dir $DIR has package.json but no lockfile in it or any parent (package-lock.json / pnpm-lock.yaml / bun.lock / bun.lockb / yarn.lock) -- commit one (P5)"
  if git -C "$LOCKDIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$LOCKDIR" ls-files --error-unmatch "$LOCK" >/dev/null 2>&1 \\
      || fail "lockfile $LOCKDIR/$LOCK exists but is NOT committed -- git add it (P5)"
  fi
fi'''
assert old in src, "policy block not found"
src = src.replace(old, new)
open(p, "w").write(src)
print("patched")
