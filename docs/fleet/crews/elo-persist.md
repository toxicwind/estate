---
crew: 'elo-persist'
scope: 'durable Elo persistence for sovereign-router: elo_state table in HealthDB + write-through setElo() so live-learned Elo survives daemon restarts; bench priors remain fallback only; restore-on-startup, hot-reload-safe, fail-open on corrupt DB'
owner: 'elo-persist, Ember crew'
status: 'DONE (2026-09-21; corrective 1af9d6cd on origin/main: map-only prior seeding (fallback priors never create elo_state rows), persistedEloProviders set (hot-reload immune incl. equality edge), fail-open on corrupt DB; restart-verified live 2x 2026-09-21, /admin/reload no-clobber, live traffic write-through matched DB; tests 29/29 green)'
order: 77
registered: '2026-09-21'
updated: '2026-09-29'
---

# elo-persist

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
