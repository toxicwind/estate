# stash-guard

<div align="right">

[![License: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-monorepo-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

Autonomous WIP flight-recorder + drop-proof stash vault for the
sovereign/tau monorepo (and, in `--deep` mode, every git repo on the box).
`git stash drop` and `git stash clear` can no longer lose work — every live
stash entry is pinned at a guard ref that survives.

```mermaid
flowchart LR
    wt[dirty worktree] -->|git stash create · non-destructive| snap[refs/guard/wt/<slug>/<ts>]
    stash[stash@{n}] -->|pin| vault[refs/guard/stash/<sha12>]
    untracked[untracked files] -->|plumbing snapshot| snap
    vault & snap --> push[push guard refs → archive remote]
    push --> log[events.db · flight recorder]
```

## Features

- **Snapshots dirty worktrees** — non-destructively. `git stash create`
  builds a commit of tracked modifications *without touching the worktree*;
  untracked files are snapshotted via plumbing (`hash-object`/`mktree`/
  `commit-tree`) honoring `.stashguardignore` + built-in excludes
  (`builds/`, `bench-*/`, `.broken-git-backup/`, `*.pcap`, …).
- **Vaults stash entries** — every live `stash@{n}` pinned at
  `refs/guard/stash/<sha12>`; drops and clears can't lose work.
- **Pushes guard refs** to the `archive` remote
  (`toxicwind/local-work-archive`), with `--prune` so retention applies
  remotely too.
- **Flight-recorder log** — every snapshot/vault/push lands in
  `~/.local/state/stash-guard/events.db` (SQLite, append-only).

Retention: last `--keep` (default 24) snapshots per worktree; older refs pruned.

## Quick start

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
```

## Architecture

Refs: `refs/guard/wt/<worktree-slug>/<YYYYMMDD-HHMMSS>[-untracked]` for
snapshots, `refs/guard/stash/<sha12>` for vaulted stashes. Only git objects
+ `refs/guard/*` refs are created — the daemon never touches worktree
files, index, HEAD, or branches.

## Config

| flag | default | purpose |
| --- | --- | --- |
| `--interval` | `90` s | snapshot cadence |
| `--keep` | `24` | snapshots retained per worktree |
| `--deep` | off | cover every git repo on the box |
| `--extra-repos` | — | additional repos to guard |

Pitchfork: `[daemons.stash-guard]` in the repo-root `pitchfork.toml`, also
in `[groups.all]`. `boot_start = true`, `retry = true`.

## Safety

The only mutating mode is `restore --apply --to <worktree>`, which is
explicit. Everything else is create-only.

## Dev / contributing

Keep the create-only invariant: a guard that can mutate the worktree it
protects is a liability. Extend excludes via `.stashguardignore` per repo.

## License & security

MIT — see [LICENSE](https://github.com/toxicwind/sovereign-projects#license).

- Guard refs hold copies of your uncommitted work — including anything
  sensitive in the tree. The `archive` remote must be as trusted as the
  source repos.
- `restore --apply` overwrites worktree files: it is deliberately
  explicit-only.
