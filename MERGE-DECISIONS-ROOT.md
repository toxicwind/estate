# Master Merge Decisions — Root Summary

Generated: 2026-09-22
Root Repo: `/home/toxic/sovereign`

---

## Repos Summary

| Repo Path | Merge A | Merge B | Result SHA | Decision Mode | MERGE-DECISIONS Path |
|-----------|---------|---------|------------|---------------|----------------------|
| `~/sovereign` | `3a90ad5288` | `6adf64b4d3` | `60c4b98491` | Reasoned take-b + union | `~/sovereign/MERGE-DECISIONS.md` |
| `projects/shell/ii` | `HEAD` | `refs/recovery/*` | `HEAD` | Submodule clean | `projects/shell/ii/MERGE-DECISIONS.md` |
| `projects/outlier-toolkit` | `HEAD` | `refs/recovery/*` | `HEAD` | Submodule clean | `projects/outlier-toolkit/MERGE-DECISIONS.md` |
| `projects/tau/engine/crates/beellama.cpp` | `HEAD` | `refs/recovery/*` | `HEAD` | Inherited | `beellama.cpp/MERGE-DECISIONS.md` |
| `projects/tau/engine/crates/ik_llama.cpp` | `HEAD` | `refs/recovery/*` | `HEAD` | Inherited | `ik_llama.cpp/MERGE-DECISIONS.md` |

---

## Verifiers

1. `test -f ~/tool-optimization.md && wc -l ~/tool-optimization.md` -> PASS
2. `test -f ~/machine-diagnosis.md && wc -l ~/machine-diagnosis.md` -> PASS
3. `test -f ~/repair-report.md && wc -l ~/repair-report.md` -> PASS
4. `test -f ~/sovereign/MERGE-DECISIONS.md` -> PASS
5. `git -C ~/sovereign show-ref --verify refs/recovery/maximal-merge` -> PASS
