![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/save-maximal-recovery?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/save-maximal-recovery?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/save-maximal-recovery?style=for-the-badge)

# save-maximal-recovery
Create recovery refs and diffs after destructive git operations — no head/tail, no git fsck

## What it does
Recovers destroyed git state after destructive operations (reset --hard, stash drop, merge -X ours) by creating recovery refs and diffs without modifying HEAD or working tree, using reflog-based stash recovery instead of slow git fsck.

## Why it matters
Provides fast, reliable recovery from accidental destructive git operations that would otherwise require time-consuming git fsck searches or be impossible to recover, especially in large repositories.

## Who it's for
Developers and DevOps engineers who perform git operations and need a safety net for recovering from accidental destructive commands like reset --hard, stash drop, or problematic -X ours merges.

## Features
- **Reflog-Based Recovery** - Uses `grep 'stash' "$OUT/reflog.txt"` instead of slow `git fsck --unreachable` (completes in <1 second)
- **Orphaned Merge Preservation** - Creates `refs/recovery/orphaned-merge` to pin destroyed merge commits as refs
- **Current HEAD Snapshots** - Captures `refs/recovery/current-HEAD` as tree snapshot
- **Stash Recovery** - Recovers every dropped stash via `refs/recovery/stash-N-<sha>` from reflog
- **-X ours Analysis** - Generates `flip-stat.txt` and `flip-full.patch` showing what -X ours rejected
- **Config Diff Tracking** - Provides `bashrc.diff` and `claude-env.diff` for ambiguous config file vs .bak archives
- **Safe Recovery Workflow** - Enables post-merge fixes without modifying current HEAD or working tree

## Quick Start
```bash
# Run recovery after destructive git session
bash /home/toxic/save-maximal.sh

# Creates ~/save-maximal-<timestamp>/ with:
# - refs/recovery/orphaned-merge — destroyed merge commit pinned as ref
# - refs/recovery/current-HEAD — current tree snapshot  
# - refs/recovery/stash-N-<sha> — every dropped stash from reflog
# - flip-stat.txt / flip-full.patch — what -X ours rejected
# - bashrc.diff, claude-env.diff — config diffs vs .bak archives

# Post-merge recovery (if -X ours merge needs fixing)
cd ~/sovereign
git merge refs/recovery/orphaned-merge --no-commit --no-ff
# resolve any conflicts (usually just DESIGN.md)
git commit -m "emergent merge: restore orphaned changes"
```

## Configuration
- **Script Location**: `/home/toxic/save-maximal.sh`
- **Output Directory**: `~/save-maximal-<timestamp>/` (timestamped recovery directory)
- **Key Rules**:
  - Replace `head -1` with `sed -n '1p'` (no head/tail allowed)
  - Use `grep 'stash' "$OUT/reflog.txt"` instead of `git fsck --unreachable` (too slow)
  - Script completes in <1 second

## Development
Modify the bash script at `/home/toxic/save-maximal.sh` to adjust recovery behavior. The script follows these principles:
- Reflog-based stash recovery for speed
- Recovery refs preservation without modifying HEAD
- -X ours conflict analysis through flip files
- Config file diff tracking against .bak backups

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Non-Destructive** - Recovers state without modifying HEAD or working tree
- **Reflog-Only** - Uses reflog instead of potentially dangerous git fsck operations
- **Read-Only Recovery** - Creates refs and diffs but doesn't alter existing repository state
- **Fast Operation** - Completes in <1 second to enable frequent use as safety net