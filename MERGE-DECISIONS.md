# Merge Decisions — ~/sovereign

Repo: `/home/toxic/sovereign`
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
