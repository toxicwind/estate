# The Fabric — pens connective-tissue plan (2026-11-01)

> Decision doc from the 2026-11-01 ADHD checkbox ask (all answers non-rollback).
> Concept grounded in the 2026 MDPI stigmergy review (Sensors 26(13):4227) and
> verified against the actual running estate (code + kernel, not web narrators).

## Concept: the pens are a stigmergic fabric

The pens (14 standalone product repos) are **not** a managed topology and never
were. Each pen "moves as it goes" — no controller, no shared lineage. That is
**stigmergy** (Heylighen; 2026 MDPI review): agents coordinate by modifying a
**shared environment**, and the traces left there (ports registry, manifests,
docs, audit data) steer every other pen's next action. The connective tissue is
the **shared environment**, not a rename or a forced theme.

Blended with:
- **Holarchy** — any pen can spawn scoped sub-agents/tools (nested autonomy).
- **Panarchy** — cross-scale adaptive reconfiguration, not just trace-coordination.
- **Ecosystem succession** — pens rise/fall/pivot, and the fabric accommodates.

## Decisions (non-rollback)

1. **Identity** — "the pens are a stigmergic fabric; shared-environment traces
   are the coordination." Blend stigmergy + holarchy + panarchy + succession.
2. **Registry SSOT** — `fabric.json` **minted by toolkit** from every
   `products.registry.json` + a **live MCP probe** (name, repo, port, tools,
   docs, version). Per-pen registries stay authoritative; `fabric.json` is a
   derived view (never hand-edited). Self-describing per-service manifests feed
   it.
3. **Toolkit** — **scrap the `ports.env` KEY convention** for a more
   conventional scheme (see §ports migration). toolkit's generators remain the
   mint source.
4. **Dedicated** — `dedicated-mcp` **controls the dedicated server + Cloudflare
   — the GREEN side of blue-green** (deploy/edge ops). It is NOT a read-only
   14-pen facade; `dedicated-server-ops`/`dediops` product **renames to
   `dedicated`** and integrates into the dedicated pen.
5. **Docs** — **one portal**: `docs-mcp` index feeds a rendered site; READMEs
   deep-link; docs-mcp gains a **compare tool** (audit parquet query) + **live
   state badges** (clean/dirty/velocity) + **auto-mint** per-repo wiki pages.
6. **Skills** — **azurite is the SSOT**: tested/versioned skills (test fixture
   per skill, CI-gated), skills surfaced as **MCP tools**, kappa consumes via its
   own skill MCP, **no-copy lint**, merge raw+managed into one curated tree.
7. **Delivery** — **per-service blue-green** (blue beside green, health-check,
   atomic swap), **every swap logged as an agentic-moment compare record**,
   semver-per-service + a live-version manifest, canary + recorded rollback.
8. **First move** — write this doc, build `fabric.json`, then the edge
   (dediops → `dedicated` rename + Cloudflare).

## Edge

- `mildlyawesome.com` **zone hijacked at Cloudflare** (verified 301 →
  `femboy.pp.ua`); `*.mildlyawesome.com` subdomains dead. **Blocked** — requires
  Cloudflare zone restoration by the edge owner (dedicated).
- **`effusionlabs.com` and `arlockworks.com` are the important live domains**
  (arlockworks verified 200) — preferred public surfaces while mildlyawesome is
  quarantined.

## Ports convention migration (§toolkit decision)

`ports.env` uses ad-hoc UPPER_SNAKE keys (`HERD_PORT`, `BORNITE_PORT`, …) — the
ask called this "sucks." Replace with a conventional scheme:
- A single `fabric-services` table mapping `service-name` → `port`/`tools`/`docs`
  (the fabric.json source for ports).
- `ports.env` becomes a generated view (derivation), not the hand-edited SSOT.
- Update every reader (bornite, thresher, flotilla, yote, etc.) to read the
  conventional key first, legacy alias as fallback during migration.

## Status

- 2026-11-01: ask resolved, doc written. Next: fabric.json registry SSOT build.
- Dedicated-mcp already auto-discovers 14 pens (9458489); rewire its role per §4.
- Microsoft: DO NOT treat this as a rename exercise — it is a wiring exercise.