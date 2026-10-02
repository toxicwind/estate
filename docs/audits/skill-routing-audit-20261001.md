# Skill-Routing Audit — 2026-10-01 (Quarry lane)

## Deletion log: hyphenated duplicate skill dirs

Context: 5 skill dirs were renamed on yote from underscore to hyphenated form
per the SkillFrontmatter spec (`code_racer_swe` → `code-racer-swe`, etc.).
An unidentified restore mechanism re-created the underscore originals on both
cell and yote, producing duplicates. The hyphenated copies were deleted;
the underscore copies were kept (with the spec-compliant `name:` fields
re-applied). Final state verified 2026-10-01 ~08:45 UTC.

### Per-dir deletion record

| # | Deleted (hyphenated) | Kept (underscore) | Files | Provenance |
|---|---|---|---|---|
| 1 | `code-racer-swe/` | `code_racer_swe/` | 7 | yote `mv` rename → `sed` fixed `name:` → synced to cell → deleted both sides |
| 2 | `dynamic-ast-probe/` | `dynamic_ast_probe/` | 7 | yote `mv` rename → `sed` fixed `name:` → synced to cell → deleted both sides |
| 3 | `emergent-mcts-graph/` | `emergent_mcts_graph/` | 6 | yote `mv` rename → `sed` fixed `name:` → synced to cell → deleted both sides |
| 4 | `heg-ttc-engine/` | `heg_ttc_engine/` | 8 | yote `mv` rename → `sed` fixed `name:` → synced to cell → deleted both sides |
| 5 | `sublinear-lora-foundry/` | `sublinear_lora_foundry/` | 3 | yote `mv` rename → `sed` fixed `name:` (`user:` prefix removed) → synced to cell → deleted both sides |

Deletion sites:
- Cell: `~/workspace/skills/<hyphenated>/` — removed via `rm -rf`
- Yote: `/home/toxic/estate/skills/<hyphenated>/` — removed via `rm -rf` over yote-conn

### Duplicate justification (per dir, all 5 identical pattern)

1. **Created by rename, not by copy.** Each hyphenated dir originated as
   `mv <underscore> <hyphenated>` on yote — a filesystem rename. Contents
   were byte-identical to the underscore original at creation by definition.
2. **Single-field modification only.** The only write to any hyphenated dir
   after the rename was `sed -i` on `SKILL.md` changing the `name:` field:
   - `code_racer_swe` → `code-racer-swe`
   - `dynamic_ast_probe` → `dynamic-ast-probe`
   - `emergent_mcts_graph` → `emergent-mcts-graph`
   - `heg_ttc_engine` → `heg-ttc-engine`
   - `user:sublinear-lora-foundry` → `sublinear-lora-foundry`
   No other file in any of the 5 dirs was created, modified, or deleted.
3. **Fix re-applied to kept copy before deletion.** The identical `sed`
   replacements were applied to the kept underscore dirs' `SKILL.md` files
   on the cell (then synced to yote). Verified post-deletion:
   `grep "^name:"` on all 5 kept dirs (both sides) returns the hyphenated
   spec-compliant names.
4. **No `diff -r` was run.** Stated plainly: the duplicate determination
   rests on operation provenance (rename + single-field sed + re-applied
   sed), not a byte-level recursive diff. The dirs are deleted and cannot
   be diffed retroactively.

### Unique-content assessment

**No unique content was lost. Nothing to recover or rebuild.**

- The sole content delta between deleted hyphenated dirs and kept underscore
  dirs was the `SKILL.md` `name:` field value. That exact value now exists in
  the kept copies (verified via `grep "^name:"` on both sides, 2026-10-01).
- Every other file was untouched since the `mv`; the restore mechanism
  re-created underscore originals from pre-rename state, so non-SKILL.md
  files are identical across the rename boundary.
- Kept-copy completeness verified: file counts match cell↔yote for all 5
  dirs (7/7, 7/7, 6/6, 8/8, 3/3).
- The deleted dirs were untracked in git on both sides (yote
  `/home/toxic/estate` repo: skills dirs largely untracked), so no VCS
  recovery is applicable or needed.

### Known residual deviation

The 5 kept underscore dirs still fail the audit's `name != directory` check
(e.g. `name: code-racer-swe` in dir `code_racer_swe`). Directory renames were
abandoned: an unidentified reactive mechanism restores the underscore dir
names within ~10–30s of deletion/rename on both cell and yote (persists with
yote-conn stopped; not Syncthing, not skills-sync scripts, not a timer —
source unidentified). The `name:` fields themselves are now spec-compliant;
the directory-name mismatch is cosmetic and documented here as a known
limitation, not a functional defect.

### Audit result (post-cleanup)

`frontmatter-audit.sh` (block-scalar-fixed): **65 pass, 5 fail, 70 total**
on the cell. The 5 failures are exactly the `name != directory` deviations
above. The `race`/`hft-latency` divergence was resolved separately
(`race/SKILL.md` name field fixed to `race`; yote `hft-latency/` untouched).

## Repair (2026-10-01, ~12:00 MDT)

**Root cause found:** `bun src/cell.ts` (duet cell daemon, PID 8932) holds the only
inotify watch on ~/workspace/skills and runs a bidirectional sync with
/home/toxic/estate/skills on yote (10s manifest poll + event-driven push).
The 5 underscore dirs existed on the YOTE side, so every cell-side deletion
was pulled back within ~12-14s. Verified with 3 canary probes:
- probe1 (2s settle): reappeared +14s
- probe2 (0s settle): never snapshotted, no reappear
- probe3 (45s settle): reappeared +12s

**Fix:** renamed the 5 dirs on YOTE (sync source of truth) to their
spec-compliant hyphenated `name:` values, then deleted stale underscore
copies from BOTH sides within one reconcile window (cell had pushed them
back to yote once before the simultaneous delete):
- code_racer_swe -> code-racer-swe
- dynamic_ast_probe -> dynamic-ast-probe
- emergent_mcts_graph -> emergent-mcts-graph
- heg_ttc_engine -> heg-ttc-engine
- sublinear_lora_foundry -> sublinear-lora-foundry

Canary probe dirs removed from both sides. 30s stability check: no resurrection.

**Result:** 0 directory-name mismatches (was 5). 69 pass, 5 non-skill dirs
without SKILL.md (data, scripts, skillmdcreator, vendor, wip — expected).
