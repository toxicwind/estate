p = "/home/toxic/sovereign/bin/daemon-lint"
lines = open(p, encoding="utf-8").read().split("\n")

# header: file lines 9-10 (0-indexed 8..9)
assert "node/bun daemon dirs" in lines[8], lines[8]
assert "no committed lockfile" in lines[9], lines[9]
lines[8:10] = [
    "#   (2) node/bun daemon dirs (dir containing package.json): REJECT if there is",
    "#       no committed lockfile in the dir or any parent up to the workspace/git",
    "#       root (package-lock.json / pnpm-lock.yaml / bun.lock / bun.lockb /",
    "#       yarn.lock) \u2014 workspaces keep one lockfile at the root.",
]

# policy block: file lines 84-95 (0-indexed 83..94)
assert lines[83].startswith("# --- (2) lockfile policy"), lines[83]
assert lines[94] == "fi", repr(lines[94])
new_block = '''# --- (2) lockfile policy -----------------------------------------------------
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
  [[ -n "$LOCK" ]] || fail "node/bun dir $DIR has package.json but no lockfile in it or any parent (package-lock.json / pnpm-lock.yaml / bun.lock / bun.lockb / yarn.lock) \\u2014 commit one (P5)"
  if git -C "$LOCKDIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$LOCKDIR" ls-files --error-unmatch "$LOCK" >/dev/null 2>&1 \\
      || fail "lockfile $LOCKDIR/$LOCK exists but is NOT committed \\u2014 git add it (P5)"
  fi
fi'''.replace("\\u2014", "—")
lines[83:95] = new_block.split("\n")

open(p, "w", encoding="utf-8").write("\n".join(lines))
print("patched ok")
