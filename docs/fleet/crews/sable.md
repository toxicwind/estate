---
crew: 'sable'
scope: 'estate staleness hunter: docs audit DONE, now finding+fixing live drift (fleet-onboard, tau plugins, honest doc paths)'
owner: 'Sable'
status: 'RUNNING (2026-10-02) — staleness hunter'
order: 1000000012
registered: '2026-10-02'
updated: '2026-10-02'
---

# sable

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun ranch/ops/bin/kb-rollup.ts`.

## Docs staleness audit (2026-10-02) -- DONE

Audited estate docs for stale /home/toxic/estate paths, dead links, outdated claims.
Committed (local-only; GitHub creds dead 2026-10-02, pushes blocked pending Chris):

- sovereign-projects c037d68dd3: 12 docs fixed; estate-map regenerated; dupe KB deleted
- ranch e1b1551: estate-map.ts, range/README, barn/chute, mesh/bin
- trailboss 5faaf45, mcpproxy-go a2936363, rsync-mcp 5b79242, secretsmith b5b4632, tau 76447a0, chat-coord 2b3f4de

Findings for other lanes: KB refs projects/ops/bin/kb-rollup.ts (vesper/Forge);
tau plugin sources point at dead stockyard paths (taurun).
