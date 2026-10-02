# Porting Tau from Oh-My-Pi upstream plan

## Context
Create a robust execution specification and plan for porting and syncing Tau from upstream oh-my-pi (`can1357/oh-my-pi`), maintaining divergence alignment per `~/sovereign/projects/tau/docs/porting-from-oh-my-pi.md`, updating the upstream sync configuration (`upstream-changes/config.yaml`), and verifying the fork state.

## Approach
1. **Audit Upstream Reference & Sync Config**: Read and align `upstream-changes/config.yaml` with the latest upstream fork point tag and version specifications.
2. **Execute Divergence Sync & Re-apply**: Apply and verify structural divergences (builtins, authentication storage, debug modules) according to the ground-truth divergence table.
3. **Verify Upstream Sync Scripts**: Test and update `merge.sh`, `ingest.sh`, and `promote.sh` in `upstream-changes/scripts/` to ensure path correctness relative to the tau root.

## Critical files & anchors
- `projects/tau/upstream-changes/config.yaml` — fork point tag and version mappings.
- `projects/tau/upstream-changes/scripts/merge.sh` — automated sync DAG builder.
- `projects/tau/docs/porting-from-oh-my-pi.md` — ground truth divergence records.

## Verification
- Run upstream sync dry-run or verify config integrity.
- Verify divergence paths exist or match expected diff criteria against upstream tag.

## Assumptions & contingencies
- Upstream mirror at `~/scratch/oh-my-pi-upstream` is fully accessible and up to date.
- If upstream tag diverges unexpectedly, fall back to explicit ref locking in `config.yaml`.
