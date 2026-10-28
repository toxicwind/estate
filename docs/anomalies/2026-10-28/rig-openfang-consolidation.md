# openfang/rig consolidation (D-2026-10-28 #50) — one rig, no openfang

## Symptom
toxicwind/rig (Rust agent runtime, 14-crate workspace, v0.6.9) co-existed with two separate repos: toxicwind/openfang and toxicwind/openfang-join (both near-empty scaffolds: README + moon.yml). Rig's own history was messy: 52 commits (snapshot fog, temp CI probes, 2 merges, 5 OpenFang→Rig rename commits). No single rig SSOT.

## Root cause
OpenFang was a distinct fleet-agent identity concept (openfang-join CLI on :25196, ~/.openfang/agents) that never fully merged into rig; rig history never consolidated.

## Fix
Reconstructed rig main from scratch as a clean 2-commit orphan history: root daa98d5 (tree byte-identical to prior origin 230ae62, verified), then fold commit 7457156 (openfang-join → docs/legacy/rig-join-reference.ts + READMEs; legacy refs fixed to pens paths). Force-pushed with-lease; remote now only `main`. Retired 6 stale remote branches (backup/main-20260914 + 5 dependabot/cargo/*). Archived (not deleted, per archive-before-delete) both openfang repos as read-only. Then cut over estate-scripts ghost → ~/.rig config home and agent personas estate-scripts→rig; committed 1ce84c5 and pushed forward.
Commits: daa98d5, 7457156, 1ce84c5. Pushed to origin/main.

## Contract test
`git ls-remote origin refs/heads/main` → only main; HEAD == local 1ce84c5. `bun parse` of docs/legacy/rig-join-reference.ts → OK (17.23KB transpiled).
