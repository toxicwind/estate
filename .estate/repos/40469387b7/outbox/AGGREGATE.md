# AGGREGATE - cycle 1 winner (SYNTH)

repo_hash=40469387b7 run_id=20261016T030439Z-27f514 cycle=1
inputs: EXHUMER_REPORT.md, CARTO_MAP.md, OPERATOR_PROOFPLAN.md, SURGEON_CLUSTERS.md
snapshot: ?PE:pe_ce21ca2b8454b434? (dirty=NOT_A_GIT_REPO)

## Scoring
| cluster | proofability | locality | non-regression |
|---|---|---|---|
| A | 5 | 5 | 5 |
| B | 4 | 4 | 4 |
| C | 2 | 5 | 4 |

## WINNER: CLUSTER A - minimal scaffold (+ baseline sentinel rollback anchor)

Apply order (one coordinator mutation sequence):

1. Baseline sentinel (rollback anchor):
   - git init -b main (fallback: git init && git checkout -b main)
   - git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit --allow-empty -m baseline-cycle1
   - git tag pre-cluster
2. Files:
   - README.md: `# estate`, blank line, then exactly:
     Chronos Forge cycle-1 scaffold repository.
     It holds the minimal smoke-checkable layout for this repo.
     It is the baseline every later cycle mutates.
   - .gitignore (3 lines): `.estate/`, `__pycache__/`, `*.pyc`
   - tests/smoke_test.sh (mode 0755): `#!/usr/bin/env bash`, `set -euo pipefail`, `echo SMOKE_OK`, `exit 0`
3. Commit: git add -A && git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit -m "cluster-a minimal scaffold"

## Proof gate
- proof_cmd: git status -sb   (expect `## main` header, clean tree, no staged/modified entries)
- proof excerpt: first 20 lines captured as OUTPUT_CHUNK artifact
- rollback (git only): git reset --hard pre-cluster && git clean -fd   (.estate/ survives: ignored, not untracked)
- checkpoint: one append to state.json.actions[] with cycle/cluster/changed/proof_cmd/proof_pe/head/utc
