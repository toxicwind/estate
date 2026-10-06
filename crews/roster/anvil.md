---
crew: 'anvil'
scope: 'ASTMatrix Go->TypeScript live conversion: flock/ts/astmatrix Bun sidecar (strategies, racing, ELO, circuits, rate limiting, health DB, UI), imports @ranch/roost directly'
owner: 'Ember'
status: 'DONE (2026-09-30) -- commits d7201ad4840c + db9118fac806'
order: 37
registered: '2026-09-30'
updated: '2026-09-30'
---

# anvil

Per-crew ownership record. Edit the frontmatter above; the section 2 table in
docs/fleet-knowledgebase.md is generated from these files -- do not edit it by hand.

## 2026-09-30 -- ASTMatrix TS port (DONE)

- Live-converted herd/internal/astmatrix (3,912 lines Go) to Bun/TypeScript at
  flock/ts/astmatrix/ -- @flock/astmatrix.
- Provider data comes live from @ranch/roost (flock/roost); the generated Go
  artifact providers_generated.go was NOT ported (direct import instead).
- Live-catalog contract: ranch-roost/live-catalog/v1 (file reader + serve-404 reporting).
- Sidecar default port 25214 (25194 taken by ralph-dashboard); env-overridable.
- Verified: 61/61 bun:test, tsc --noEmit clean, /health + /v1/models + /ui smoke.
- Go herd/internal/astmatrix intentionally untouched -- removal only after the
  sidecar is deployed/supervised and the herd delegate swap is verified.
- Note: commit db9118f also swept Sable's staged README-rollout files (content
  identical, message mine) -- owned in fleet, no force-push.
