---
crew: 'ts-migration (Forge)'
scope: 'Production Python daemons -> Bun/TS maximal + monorepo (bun workspaces + turbo.json). Tier 0: keypool, model-guard, squawk-ws, awrawr-mcp. Tier 1: exporter, stash-guard, brand. Python stays only for ML/torch glue + throwaway probes'
owner: 'Forge (Ember''s pack, ts-migration lane)'
status: 'PHASE 1 DONE (2026-09-21): workspaces+turbo+scaffold on main 7a61ad6be9; template binary proven (health 200, fail-fast). Phase 2: KEYPOOL TS PORT DONE 2026-09-21 (971ccc5b63, 8eceaa0f4b): services/keypool/ full port, 17 parity tests pass, sidecar differential vs :25109 verified; BROWSER-ISOLATION DONE 2026-09-21: agent-display (Xvnc :99) + agent-viewer (noVNC :6080) live, keeper on DISPLAY=:99, c776f7cd25 — Forge joined pack 2026-09-21, chat forge-ts-migration'
order: 69
registered: '2026-09-21'
updated: '2026-09-29'
---

# ts-migration (Forge)

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
