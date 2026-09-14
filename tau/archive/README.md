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

- `from-sovereign-pi/` — files unique to `toxicwind/sovereign-pi` main
  (private repo, archived 2026-09-14 as `toxicwind/sovereign-pi-archive`).
  96 files, mostly `packages/ai/src/providers/data/*.json` provider data,
  `packages/ai/src/models.ts`, tokenizer tools and caches under
  `crates/pi-natives/tools/`. (264 other sovereign-pi orphans were already
  covered by the from-tau/from-oh-my-pi archives above.)

What was NOT archived (deliberately):
- `.pi/sessions/*.jsonl` (3 files): private agent session logs.
  `sovereign-projects` is public; session logs stay in the private
  `sovereign-pi-archive` repo.
- sovereign-pi's 28 branches + 30 tags: stale upstream oh-my-pi PR
  branches (v0.0.3-era lineage) and upstream release tags, preserved in
  `sovereign-pi-archive`, not merged as files.

## Wave 2 — sovereign-family + omp-extensions (2026-09-14)

Same method as wave 1: every file of each source repo's main branch was
compared by blob SHA against the full `sovereign-projects` tree (including
the wave-1 archives above); only blobs appearing nowhere were archived.
All five source repos were left untouched — nothing deleted, no branches
or tags modified.

- `from-sovereign-swap/` — 311 files unique to `toxicwind/sovereign-swap`
  main (public Go service). `internal/` (150), `ui/` (69), `evals/` (25),
  `docs/` (24), `docker/` (19), plus `cmd/`, `.github/`, `patches/`.
- `from-omp-extensions/` — 17 files unique to `toxicwind/omp-extensions`
  main (public oh-my-pi plugin repo): `packages/` (omp-kafka and others),
  `AGENTS.md`, `README.md`, root `package.json`.
- `from-sovereign-zed/` — 1,059 files unique to `toxicwind/sovereign-zed`
  main (public Zed editor fork). `crates/` (906), `docs/` (39),
  `.github/` (33), `tooling/` (20), `assets/` (16); includes 264 symlinks
  (mode 120000, targets preserved as blobs) and dev-only
  `crates/collab/.env.toml`, which holds placeholder values only
  (`"the-blob-store-access-key"`, `"devkey"`, localhost URLs) — no real
  secrets.
- `sovereign-scripts` (24 files) and `sovereign-skills` (10 files): fully
  redundant — every blob already present in `sovereign-projects`; nothing
  archived.

What was NOT archived (deliberately):
- Branch-unique content (blobs on non-main branches absent from both that
  repo's main and `sovereign-projects`): `sovereign-swap` has 8 non-main
  branches (`astmatrix-v2-preserved`, `claude/ui-svelte-build-bundle-optimize-0bms50`,
  `coderabbitai/chat/2dcab2b`, `coderabbitai/utg/{6cf1317,25b27cb,799eedb}`,
  `inflight-enhancements-912`, `plan-001-sse-bridge`) with 26–109 unique
  blobs each, plus 184 tags (`v0.0.1`–`v239`); `sovereign-zed` branch
  `toxic-fix-grep-ignore` has 396 unique blobs; `omp-extensions` has 3
  branches (`feat/initial-omp-kafka`, `feat/omp-edit-committer`,
  `fix/add-kafkajs-dep`) with 1–12 unique blobs each. All preserved in
  their source repos, not merged as files.
- `sovereign-scripts` / `sovereign-skills`: no orphans, nothing to merge.
