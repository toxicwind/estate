# upstream-changes — Version-aware upstream merge system for the tau engine

> **Keep tau work isolated from upstream churn.** Upstream (`can1357/oh-my-pi`)
> moves fast (18.1.18 → 18.2.x); our engine is a fork, not a git child of it.
> This folder is the **airlock**: every upstream version lands here first,
> gets 3-way merged against our sovereign delta in a worktree, and only then
> — after checks pass — is promoted to the live engine.

## The situation

- **Fork point (verified):** upstream tag `v18.1.18` — see `../MIRROR-DIFF-vs-upstream.md` §2
- **Sovereign delta:** 398 changed paths (+8,878/−4,669) — our customizations on top
- **Tracked version:** `config.yaml` → `primary_upstream.current_version`
- **Mirror:** `/home/toxic/scratch/oh-my-pi-upstream` (persistent upstream clone)

## Layout

```
upstream-changes/
  README.md                # this file
  config.yaml              # upstream, fork point, tracked version, policy
  scripts/
    status.sh              # where do we stand vs upstream?
    ingest.sh [ver]        # fetch + pure upstream delta + sovereign-overlap analysis
    merge.sh [ver]         # 3-way merge in a worktree (synthetic git DAG)
    promote.sh <ver>       # verify worktree -> adopt into live engine
    upgrade.sh [ver]       # ingest + merge in one command (stops before promote)
    archive-20260920/      # the old earendil-works/pi-era scripts (retired)
  log/                     # per-run decision logs
  patches/                 # upstream patch bundles (record)
```

## Workflow — version update in 2 commands

```bash
# 1. What changed upstream? (nothing touches the engine)
./upstream-changes/scripts/upgrade.sh 18.2.6
# -> ingest: fetches upstream, diffs v18.1.18..v18.2.6, classifies every file
#    as upstream-only (safe) vs overlap (both sides touched)
# -> merge: builds a synthetic DAG (base=v18.1.18, +sovereign delta, merge v18.2.6)
#    in /home/toxic/scratch/tau-merge/tau-merge-18.2.6 and reports conflicts

# 2. Review conflicts in the worktree, resolve them, then promote:
./upstream-changes/scripts/promote.sh 18.2.6
# -> conflict check, bun install, tsc, tests, binary build, smoke test,
#    engine backup, rsync in, version bump in config.yaml
```

No arg = latest `v18.*` tag upstream.

## How the 3-way merge works (merge.sh)

The engine is not a git child of upstream, so git can't merge directly.
We synthesize the DAG inside the mirror clone:

1. worktree at `v18.1.18` (the verified fork point) = BASE
2. rsync the live engine tree over it (minus generated dirs), commit = SOVEREIGN
3. `git merge v<target>` = true 3-way merge of the upstream delta

Git auto-merges everything only one side touched. Conflicts = files both
sides touched — those need human review, and `keep_tau` policy paths
(sovereign-owned files) are flagged specially in the log.

## Rules

- **No direct merge into the live engine.** Always via worktree + promote.sh.
- **promote.sh never runs with unresolved conflicts** — it exits.
- **promote.sh never touches the engine until checks pass** — backup first.
- **Every run writes a log** in `log/` — what changed, conflicts, decisions.
- **config.yaml `current_version`** is the tracked version; bump on promote.

## Old scripts

`scripts/archive-20260920/` holds the previous generation (ingest/promote/status
from 2026-09-16), which hardcoded the retired `earendil-works/pi` remote and
assumed the engine was a git child of upstream. Retired, kept for reference.
