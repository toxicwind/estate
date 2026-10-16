# AGGREGATE - cycle 2 winner (SYNTH)

repo_hash=40469387b7 run_id=20261016T030439Z-27f514 cycle=2
inputs: EXHUMER_REPORT_C2.md, CARTO_MAP_C2.md, OPERATOR_PROOFPLAN_C2.md, SURGEON_CLUSTERS_C2.md
snapshot: ?PE:pe_78b1e680b4774e5a? base=main@24fe5bb anchor=tag pre-cluster (2d9b5cb)

## Scoring
| cluster | proofability | locality | non-regression |
|---|---|---|---|
| A guardrail | 5 | 5 | 5 |
| B deferred layer | 4 | 4 | 5 |
| C governance | 5 | 5 | 5 |

Tie-break A vs C: A has a behavioral proof with loud failure modes (OPERATOR-recommended
proof swap for guardrail clusters) and mitigates EXHUMER R1/R2 risk class; C is docs-only.

## WINNER: CLUSTER A - GUARDRAIL (overwrite tests/smoke_test.sh, keep mode 0755)

Verbatim content:
    #!/usr/bin/env bash
    set -euo pipefail
    [ -f README.md ]  || { echo "FAIL: README.md missing" >&2; exit 1; }
    [ -f .gitignore ] || { echo "FAIL: .gitignore missing" >&2; exit 1; }
    if git ls-files | grep -q "\.estate/"; then echo "FAIL: .estate/ tracked" >&2; exit 1; fi
    echo SMOKE_OK
    exit 0

Commit: git add -A && git -c user.name=estate-forge -c user.email=forge@awrawr-pc commit -m "cluster-a guardrail smoke"

## Proof gate
- proof_cmd: bash tests/smoke_test.sh   (expect SMOKE_OK, exit 0)
- proof excerpt: first 20 lines captured as OUTPUT_CHUNK artifact
- rollback (git only): git reset --hard pre-cluster && git clean -fd   (never -x)
- checkpoint: one append to state.json.actions[]
