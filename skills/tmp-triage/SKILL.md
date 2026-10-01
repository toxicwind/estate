---
name: tmp-triage
description: >
  Classify /tmp (or any scratch dir) by provenance before a repo sweep: disposable junk versus meaningful work needing a repo home. Triggers on: tmp triage, scratch cleanup.
---

# tmp-triage

Classify a `/tmp` (or any scratch dir) by provenance before a repo sweep:
which entries are disposable junk, which are meaningful work needing a repo
home, which are secret-shaped (report shape only, never touch), which are
live runtime state, and which need human eyes.

## When to use

- Before deleting anything from a shared `/tmp` during a repo sweep.
- When inheriting a box and needing a provenance inventory fast.
- As the pre-pass for orphan→repo integration: MEANINGFUL is the feed list.

## The tool

`bin/tmp-classify.py` — stdlib-only Python 3, no dependencies. Copy it to the
target box and run it there (verdicts are box-local; never apply one box's
scan to another).

```
tmp-classify.py [--root /tmp] [--json] [--delete-disposable] [--min-age-min 30]
```

- Default is **dry run**: prints a classified inventory, changes nothing.
- `--delete-disposable` removes DISPOSABLE entries only. Never touches
  SECRET / IN_USE / UNKNOWN, and never touches anything younger than
  `--min-age-min` (default 30 minutes; 0 disables).
- `--json` emits machine-readable output (summary + per-entry list).
- Exit code 2 means secrets were found (reported, nothing deleted).

## Classes

| Class | Meaning | Action |
|---|---|---|
| DISPOSABLE | transfer fragments, caches, empty files, tool dumps, logs, locks/pids | delete after review |
| MEANINGFUL | scripts, docs, configs, source, data | feed to repo integration with path + provenance note |
| SECRET | secret-shaped name or content | **never delete, never commit, never inspect values** — report names only |
| IN_USE | sockets, fifos, tmux/X11 runtime state | leave alone |
| UNKNOWN | directories, special files, unmatched | inspect by hand |

## Workflow

1. **Scan**: `tmp-classify.py --root /tmp` (dry run). Read the whole report.
2. **Secrets**: note every SECRET path by name only. If a MEANINGFUL file
   must be integrated, scrub credential-shaped content first — that decision
   belongs to the owning crew, never to the sweeper.
3. **In-use check**: for DISPOSABLE candidates, confirm no open handles
   (`fuser`) and no active crew worktree/dir claims them (check fleet +
   knowledgebase §2 before touching shared trees).
4. **Delete**: `tmp-classify.py --root /tmp --delete-disposable --min-age-min 15`.
5. **Feed**: post the MEANINGFUL list (paths + one-line provenance) to the
   integration crew; keep a dated copy of the report as evidence.

## Rules reference

`references/classification-rules.md` documents every rule, its rationale,
and known blind spots.

## Provenance

Built 2026-09-20 by Ledger (Bedrock) during the repo-sweep finisher run.
Battle-tested on yote `/tmp`: 290 entries → 90 disposable deleted,
18 skipped as too young, 0 false-positive deletions, secrets untouched.