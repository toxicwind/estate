# Estate dual-truth (D-2026-10-28 #48) — /home/toxic/estate vs pens/estate

## Symptom
Daemons kept coming back down even after edits landed in /home/toxic/estate. pitchfork supervisor loads pens/estate/pitchfork.toml (watch_base_dir=/home/toxic/pens/estate), while AGENTS.md pointed agents at /home/toxic/estate as "the estate" (control plane / deploy plane). /home/toxic/estate and /home/toxic/pens/estate were two real git clones of toxicwind/estate.git with diverged histories (1477-line diff on pitchfork.toml), different branches (wip/kappa/estate-cutover-20261027 vs main), and no propagation between them. estate/qdrant run from estate landed on the estate clone's CWD; pens/estate had its own qdrant_data; state.toml claimed estate/qdrant "running" while no process existed.

## Root cause
Two truths: /home/toxic/estate (legacy pre-reorg SSOT clone) and /home/toxic/pens/estate (what pitchfork actually loads). edits/commits landed in estate; supervisor never saw them. The estate clone's post-commit hook tried `sync-estate-ns.sh` but that script was not on PATH → silent no-op. daemons stayed on stale config → down.

## Fix
Folded estate-only live files into pens/estate (bridge/morphe.py, agents/*, config/tau WIP, docs/anomalies), gitignored qdrant runtime data (was tracked with 112 live collection blobs), untracked qdrant_data/storage/snapshots, deleted /home/toxic/estate (now must-not-exist per hardened bin-contract-audit lease), pointed every daemon stanza at pens/estate paths.
Commit: be04bb0d74 (estate), ad6c45b01c (fold), 364b68ddf9 (repoint scripts). Pushed to origin/main.

## Contract test
`pitchfork status estate/qdrant` → running on 25133/25134, healthz 200, collection test_freeinference served. `ls -la /home/toxic/estate` → absent. bin-contract-audit → lease ok: /home/toxic/estate absent.
