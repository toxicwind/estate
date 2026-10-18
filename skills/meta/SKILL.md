---
name: meta
description: Coordinate the ranch's 214 component repos as one workspace. Use whenever work touches 2+ component repos, when checking what state every repo is in, or instead of any hand-rolled cd-loop over ranch dirs. Replaces git-submodule churn (detached HEADs, orphan gitlinks, stale pointers) with peers + one manifest.
---

# meta

One command answers "what is the state of the estate" or "do X everywhere" —
never a `for d in */; do cd $d; done` loop.

<critical>
- Run from `ranch/` — the manifest is `ranch/.meta.yaml` (214 repos, generated, never hand-edit).
- `meta context` FIRST: the state of every repo before you touch anything.
- Prefer `meta git update` over `git submodule update --init` — always.
- Snapshot before batch changes: `meta git snapshot create <name>`.
- Target repos with `--include-only agon,hodos` — never grep-filter output.
- Agents can call meta via `meta-mcp` (MCP server, 29 tools) — no shell needed.
</critical>

## When to reach for meta

- "What's dirty across the estate?" → `meta context`
- "Pull/clone everything" → `meta git update`
- "Run bun test in every repo" → `meta exec -- bun test`
- "Commit the same message in all dirty repos" → `meta git commit -m "..."`
- "Before a risky batch change" → `meta git snapshot create pre-change`
- One repo only? Don't. Plain `git -C <repo>` is faster.

## The command surface

| You want | Run |
|---|---|
| Workspace summary (per-repo branch, dirty, ahead/behind) | `meta context` |
| Per-repo status, all 214 | `meta git status` |
| Clone missing + pull existing | `meta git update` |
| Any command everywhere | `meta exec -- <cmd>` |
| Same command, subset | `meta exec -- <cmd> --include-only agon,hodos` |
| Commit everywhere dirty | `meta git commit -m "msg"` |
| Snapshot / rollback | `meta git snapshot create\|restore <name>` |

## Worked examples

```bash
cd /home/toxic/estate/ranch

# What needs attention right now?
meta context
# → per-repo table: branch | clean/dirty (↑N ahead)

# Sync the whole estate (clones any repo you're missing)
meta git update

# Run the typecheck sweep across every TS repo, fast
meta exec --parallel -- bun run typecheck

# Only the Greek-named routing repos
meta exec -- git pull --include-only hodos,pylae,keryx

# Safe batch rename across components
meta git snapshot create pre-rename
meta exec -- 'sed -i s/oldName/newName/g ...'
meta git commit -m "rename sweep"
```

## Failure shapes you own

WRONG: `cd agon && git pull` … `cd hodos && git pull` …
RIGHT: `meta git update` — the loop misses uncloned repos; meta clones them.

WRONG: hand-editing `.meta.yaml` to add a repo.
RIGHT: add it to `.gitmodules`, then `bun toolkit/gen-meta-manifest.ts` — the
manifest is generated; hand edits are silently lost on regen.

WRONG: `meta exec -- git push` on a detached-HEAD worktree without checking
`meta context` first.
RIGHT: `meta context` → fix dirty/detached repos → then batch push.

## Not your job

Snapshot storage layout, plugin stdin/stdout protocol, SSH multiplexing setup,
the 10-crate Rust workspace. If `meta <verb>` answers it, stop reading.
