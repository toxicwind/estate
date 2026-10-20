# Merge Decisions — ~/estate

Repo: `/home/toxic/estate`
Merge A (-X ours re-do): `3a90ad5288`
Merge B (original pre-reset merge): `6adf64b4d3`
Resulting Commit: `60c4b98491` (tagged as `refs/recovery/maximal-merge`)

---

## Decisions

### `docs/chat-native-agents/DESIGN.md`
- **ours (3a90ad5288)**: Line 57 contained an unformatted single-line wrapping of the distilled intent classifier description.
- **theirs (6adf64b4d3)**: Original 6adf64b4d3 formatting with clean paragraph breaks for `tier2_judge()`.
- **decision**: `take-b` (take `6adf64b4d3`)
- **reason**: Retains the clean multi-line formatting of Tier 1/Tier 2 classifier docs from the pre-reset merge.

### Untracked Emergent Files (426 files merged across `e9f800defc` and `60c4b98491`)
- **ours**: Untracked/uncommitted on working tree prior to synthesis.
- **theirs**: Present in orphaned tree / working copy.
- **decision**: `union`
- **reason**: All 426 valid code, skill, and documentation files staged and committed. 59 secret/token files matching `.gitignore` patterns explicitly preserved un-tracked for security boundaries.

## 2026-10-20 — duplicate-tree consolidation (whole-repo simhash/Jaccard sweep)

- plugins/agentpluginzoo: canonical = `ranch/plugin-ecosystem/agentpluginzoo` (has origin remote).
  `estate/plugins/` was an untracked stale copy -> removed. Data CSVs kept from ranch copy.
- scripts: canonical = `estate/scripts` (tracked control-plane); `ranch/estate-scripts` was a
  local component mirror without a remote -> cherry-picked its README/package.json/.envrc into
  `estate/scripts`, then `ranch/estate-scripts` is a symlink to `../scripts`.
- gear: canonical = `ranch/gear` (active: annas-router, newer awrawr-mcp). Cherry-picked
  `vendor/dynamic_credentials.py` into `ranch/gear`, then removed tracked `estate/gear`.
- rig-ciwatch: duplicate checkout of `toxicwind/rig` (same origin); only delta is a kernel.rs
  formatting wrap + Cargo.lock -> recorded as `ci-watch-kernel.patch` in `rig` (commit b60d814),
  `ranch/rig-ciwatch` now a symlink to `rig`.
- oh-my-pi/tau-verify, fanout/openfang-join: distinct repos with different origins - NOT dupes.

## 2026-10-20 — push-completeness follow-up (unpushed state, not force-fought)

- rig (`b60d814` ci-watch-kernel.patch): committed locally but NOT pushed —
  origin is behind-1/ahead-1 with active drift. Do NOT force/rebase rig blindly;
  rides the next owner-sync (delta is a trivial formatting patch, low risk).
- gear (`1aa4a80` vendor cherry-pick): committed but `ranch/gear` has NO origin
  remote — local-only by pre-existing state. Add a remote + push when gear is
  wired to an upstream.
- Everything else touched this session (estate, ranch, ffs-diff, corral moon.yml)
  is pushed and in sync.
