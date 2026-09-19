# stash-guard

Autonomous WIP flight-recorder + drop-proof stash vault for the sovereign/tau
monorepo (and, in `--deep` mode, every git repo on the box).

## What it does, every `--interval` seconds (default 90)

1. **Snapshots dirty worktrees** — non-destructively. `git stash create`
   builds a commit of tracked modifications *without touching the worktree*;
   untracked files are snapshotted via plumbing (`hash-object`/`mktree`/
   `commit-tree`) honoring `.stashguardignore` + built-in excludes
   (`builds/`, `bench-*/`, `.broken-git-backup/`, `*.pcap`, …).
   Refs: `refs/guard/wt/<worktree-slug>/<YYYYMMDD-HHMMSS>[-untracked]`
2. **Vaults stash entries** — every live `stash@{n}` is pinned at
   `refs/guard/stash/<sha12>`. `git stash drop` / `git stash clear` can no
   longer lose work; the pinned ref survives.
3. **Pushes guard refs** to the `archive` remote
   (`toxicwind/local-work-archive`), with `--prune` so retention applies
   remotely too.
4. **Flight-recorder log** — every snapshot/vault/push lands in
   `~/.local/state/stash-guard/events.db` (SQLite, append-only).

Retention: last `--keep` (default 24) snapshots per worktree; older refs pruned.

## Safety

Never touches worktree files, index, HEAD, or branches. Only creates git
objects + `refs/guard/*` refs. The only mutating mode is
`restore --apply --to <worktree>`, which is explicit.

## Usage

```bash
# one-shot scan (safe to run any time)
python3 tools/stash-guard/stash-guard.py --once

# daemon (as run by pitchfork)
python3 tools/stash-guard/stash-guard.py --repo /home/toxic/sovereign \
    --deep --interval 90 \
    --extra-repos /home/toxic/sovereign/projects/tau-extensions,/home/toxic/sovereign/projects/tau-occupied-20260916

# inspect
python3 tools/stash-guard/stash-guard.py list
python3 tools/stash-guard/stash-guard.py restore refs/guard/stash/abc123def456
python3 tools/stash-guard/stash-guard.py restore refs/guard/stash/abc123def456 --apply --to /home/toxic/sovereign
```

## pitchfork

`[daemons.stash-guard]` in the repo-root `pitchfork.toml`, also listed in
`[groups.all]`. `boot_start = true`, `retry = true`.
