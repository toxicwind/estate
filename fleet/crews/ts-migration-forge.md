---
crew: 'ts-migration (Forge)'
scope: 'Production Python daemons -> Bun/TS maximal + monorepo (bun workspaces + turbo.json). Tier 0: keypool, model-guard, squawk-ws, awrawr-mcp. Tier 1: exporter, stash-guard, brand. Python stays only for ML/torch glue + throwaway probes'
owner: 'Forge (Ember''s pack, ts-migration lane)'
status: 'PHASE 1 DONE (2026-09-21): workspaces+turbo+scaffold on main 7a61ad6be9; template binary proven (health 200, fail-fast). Phase 2: KEYPOOL TS PORT DONE 2026-09-21 (971ccc5b63, 8eceaa0f4b): services/keypool/ full port, 17 parity tests pass, sidecar differential vs :25109 verified; KEYPOOL PRODUCTION CUTOVER DONE 2026-10-02: TS keypool live on :25109, 7/7 pools healthy, 464-model proxy identical to shadow; pitchfork.d/keypool.toml points to bun TS with Python fallback. COMPOSER REPAIRED 2026-10-02: registry fixed for ranch flatten, all fragments synced (0 drift), 81 daemons/32 projects, task-launch given own project. BROWSER-ISOLATION ACCEPTED 2026-10-02: keeper CDP :9223 live (Chrome 148), cookie jar isolated from Chris Chromium, Xvnc :99 re-homed to estate namespace. Commits 6a88ebeb87 (estate) + 6a4640f (ranch) local-only, push blocked on dead GitHub creds (Chris call). BROWSER-ISOLATION DONE 2026-09-21: agent-display (Xvnc :99) + agent-viewer (noVNC :6080) live, keeper on DISPLAY=:99, c776f7cd25 — Forge joined pack 2026-09-21, chat forge-ts-migration'
order: 69
registered: '2026-09-21'
updated: '2026-10-02'
---

# ts-migration (Forge)

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
