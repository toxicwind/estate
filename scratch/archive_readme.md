# Archive of consolidated Tau-family repositories

On 2026-09-14 the Tau-family repositories were consolidated into
`toxicwind/sovereign-projects`, whose `tau/engine/` is the canonical,
newest Tau working tree (HEAD 2026-09-12, per `tau/README-FORK.md`).

This directory preserves every file from the retired repositories whose
content did **not** exist anywhere in `sovereign-projects` (compared by
blob SHA across the full recursive tree), so nothing was lost in the
consolidation. Files are grouped by source repo, keeping their original
relative paths:

- `from-tau/` — files unique to `toxicwind/tau` (standalone snapshot,
  HEAD 2026-09-11). Mostly the pre-KDL `packages/ai/src/registry/*.ts`
  provider definitions (superseded by the KDL compat-rule migration in
  `tau/engine/packages/catalog/src/compat/rules/`) and tokenizer cache
  binaries under `crates/pi-natives/tools/cache/`.
- `from-oh-my-pi/` — files unique to `toxicwind/oh-my-pi` (pre-rename
  snapshot, HEAD 2026-09-03), same categories plus a few legacy
  top-level files (`lib/lens-orchestrator.js`, old workflows).

What was NOT archived (deliberately):
- Files identical to content already in `sovereign-projects` (4,728 for
  tau, 3,639+ for oh-my-pi) — already preserved.
- Same-path files whose content differed — the `tau/engine/` version is
  newer and wins (linear lineage: oh-my-pi -> tau -> engine).
- `toxicwind/tau`'s two `copilot/fix-1934561-*` branches: 1 trivial
  commit ahead of main, behind main, no file changes vs main.
- `toxicwind/sovereign-pi` was NOT deleted: it carries 28 feature
  branches and 20 tags beyond main.

Verification: every archived file's blob SHA was matched against the
full `sovereign-projects` tree before archiving; the manifest above is
the complete orphan set. Original repositories were deleted only after
this commit landed.
