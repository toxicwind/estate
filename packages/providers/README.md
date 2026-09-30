# @sovereign/providers

Master provider catalog for the sovereign estate. Single source of truth for:

- **Provider definitions** — base URL, key env var, and the endpoint-shape
  adapter that reads each provider's `/models` listing.
- **Live discovery** — fetch `/models` across all known endpoint shapes
  (OpenAI, Google v1beta native, Mistral native, static, declared-none).
- **Alias map** — friendly names → canonical model ids (UX layer).
- **Curated seeds** — cold-start data only; inert after first discovery.
- **Auto-quarantine** — serve-time 404 or vanished-from-live-listing across
  2 consecutive successful refreshes → quarantined, never served, always
  observable. Re-listing re-admits automatically.

## Why this exists

Every consumer used to hand-maintain its own provider→models list
(`PROVIDER_MODELS` in the router, hardcoded tables in herd's Go, model lists
in Python research scripts). Live discovery could only *add* — nothing ever
removed a dead id. Result: 4 of 6 groq ids 404'd in production until a human
noticed. This package makes the **live listing the source of truth** and
demotes curation to cold-start seeds.

## Consumers

| Consumer | How it consumes |
|---|---|
| `tools/sovereign-router/sovereign-router-ts` | imports `@sovereign/providers` directly (same repo, bun workspace) |
| `projects/tau-extensions/omp-model-router` | imports `@sovereign/providers` directly |
| herd (Go, `stockyard/herd`) | `generated/providers.go` — generated, checked in, never hand-edited |
| Python research scripts | `generated/providers.json` — canonical data artifact |

## Layout

```
src/
  types.ts      core types (ProviderDef, adapters, quarantine, persisted state)
  adapters.ts   one parser per /models wire shape (openai, google-v1beta, mistral, static, none)
  discovery.ts  fetch + parse with timeout; failures never cached, never acted on
  catalog.ts    ModelCatalog — serving sets, miss counters, quarantine, persistence
  data.ts       THE source of truth: provider defs, seeds, aliases, dead ids
  codegen.ts    emits generated/providers.json + generated/providers.go
scripts/build.ts  `bun run build` — regenerates generated/
generated/
  providers.json  canonical data artifact (Python consumers)
  providers.go    drop-in Go data file for herd (package astmatrix)
tests/          adapter shapes, prune/quarantine paths, artifact sync
```

## Serving contract

1. **Cold start**: seeds serve until the first successful discovery.
2. **After discovery**: the live listing owns membership. Seeds go inert.
3. **Well-formed empty listing** = zero models. Never fall back to stale data.
4. **Failed refresh** changes nothing (stale-serve); miss counters move only
   on *successful* refreshes.
5. **Missing once** keeps serving; missing **twice** in a row → quarantine
   (`vanished-from-live-listing`).
6. **Serve-time 404** → immediate quarantine (`serve-404`).
7. **Re-listing** re-admits automatically (except the permanent dead tier).
8. **Dead ids** (`DEAD_MODEL_IDS`, EOL notices) are never served, never
   re-admitted.

## Adding a provider

1. Add a `ProviderDef` to `src/data.ts` (pick the adapter matching its
   `/models` shape; add `seeds` for cold start).
2. `bun run build` — regenerates `generated/`.
3. `bun test` — the sync test fails if you forgot step 2.

## Adding an endpoint shape

New odd provider = new adapter in `src/adapters.ts` (+ fixture tests in
`tests/adapters.test.ts`). Provider-specific branches never leak into
routing or catalog logic.

## Persistence

`ModelCatalog.saveToFile()` writes atomically (temp + fsync + rename) and
`loadFromFile()` understands both the v2 shape and the legacy router
`.state/live-models.json` v1 shape (`{ live, meta }`).
