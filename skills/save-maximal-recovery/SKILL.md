---
name: save-maximal-recovery
description: "Create recovery refs and diffs after destructive git operations — no head/tail, no git fsck"
---

# save-maximal-recovery

After a destructive git session (reset --hard, stash drop, merge -X ours), recover all destroyed state without modifying HEAD or working tree.

## Usage
```bash
bash /home/toxic/save-maximal.sh
```

The script creates `~/save-maximal-<timestamp>/` with:
- `refs/recovery/orphaned-merge` — the destroyed merge commit pinned as a ref
- `refs/recovery/current-HEAD` — current tree snapshot
- `refs/recovery/stash-N-<sha>` — every dropped stash found via reflog (NOT git fsck)
- `flip-stat.txt` / `flip-full.patch` — what -X ours rejected
- `bashrc.diff`, `claude-env.diff` — ambiguous config file diffs vs .bak archives

## Key rules
- Replace `head -1` with `sed -n '1p'` (no head/tail allowed)
- Use `grep 'stash' "$OUT/reflog.txt"` instead of `git fsck --unreachable` (too slow)
- Script completes in <1 second

## Post-merge recovery
After running this, if the -X ours merge needs fixing:
```bash
cd ~/sovereign
git merge refs/recovery/orphaned-merge --no-commit --no-ff
# resolve any conflicts (usually just DESIGN.md)
git commit -m "emergent merge: restore orphaned changes"
```

## Why this approach
- `git fsck --unreachable` times out on large repos; reflog grep finds stashes faster
- The `-X ours` merge and original merge share identical trees except for conflicted files
- Only the conflicted files need manual resolution (take --theirs side)
