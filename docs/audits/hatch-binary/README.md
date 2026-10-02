# Hatch binary decompose — index

Modular docs from the `/opt/hatch/bin/hatch` runtime binary investigation.
Each module covers one subsystem; all cross-linked. Re-extract after runtime
updates — strings change with new builds.

## Modules

- [Model tiers](model-tiers.md) — `avocado-pro-max`, `avocadolow`/`avocadomedium`
  tier labels, voice tiers, and what we know about the "pro" route.
- [Model routes](../avocado-model-family-2026-09-30.md) — full ipnext/avocado
  route/version map, knobs, quality notes.
- [Route findings](../avocado-model-routes-2026-09-30.md) — live route
  verification, dormant candidates, the override mechanism.

## Method

`strings` on the runtime binary + Hatch DB (`agent.agents.model` GROUP BY) +
live session observation. Findings are quoted verbatim; unknowns are labeled
as unknowns.
