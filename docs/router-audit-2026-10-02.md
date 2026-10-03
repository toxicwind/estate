# Router Audit — 2026-10-02 / 2026-10-03

**Ordered by:** Chris. **Coordinated by:** the mesh-migration crew (Ember's crew).
**Scope:** what each router/proxy actually does (AST-verified), where they overlap, and the
executed consolidation into `ranch/mesh/`.

> This report covers the audit AND the executed migration. Chris's directive evolved during
> the operation: audit-only → full migration → "audit phase OVER, execute now" → consolidate
> into the *existing* `ranch/mesh/` (it already existed as the sovereign mesh; creating a new
> one would have collided) → no lane ownership, no approval gates, merge duplicates by hand
> with hashline, lose zero code.

---

## 1. Per-router findings

### 1.1 herd — Go inference backplane — `:25100` (DOWN at audit time)

- **Language:** Go (`module github.com/mostlygeek/herd`, go 1.27.1). Binary builds from
  `./cmd/herd-plane` (never `go build .` at root).
- **What it does (AST evidence):** `internal/server/server.go:198` `func New(cfg config.Config, …)`,
  `:480` `func (s *Server) ServeHTTP(…)`, `:123` registers `"/v1/chat/completions"` (ast-grep
  verified). Herd is a Go inference backplane (llama-swap fork): it manages local LLM engine
  processes (llama-server backends on auto-assigned ports from `startPort: 25001`, config
  `herd.yaml`) and fronts them with a single OpenAI-compatible HTTP API, plus auth, model
  profiles, MCP tool aggregation, benchmarking, and peer/fleet features. It is the estate's
  **local-inference layer** behind the mesh routers.
- **Live state:** DOWN. Nothing on `:25100` (`ss` empty, `/health` unreachable, no herd
  processes). The pitchfork daemon died ~18:40 MDT 2026-10-02; the binary is intact and the
  launcher (`estate/stack/services/herd.sh`) now points at the new path. **Needs a pitchfork
  restart — flagged as an ops follow-up, not done in this pass.**
- **Home:** `ranch/mesh/router/herd/` (moved via `git mv`, 1097 files, history preserved).
  `go build ./cmd/herd-plane` OK; `go test -short ./internal/...` — 26 packages OK.

### 1.2 flock proxy (Rust) — preserved, NOT live

- **Language:** Rust (axum/tokio), edition 2021, v0.6.6 (nim-proxy fork).
- **What it does (AST evidence):** rate-limit-aware OpenAI-compatible cloud-provider proxy
  (NIM/OpenRouter/Groq/Cerebras) with per-key pacing, key pools, circuit breakers, health/Elo
  routing, SQLite state. Code default port `:8000` (`src/lib.rs:557`, `env_or("PORT","8000")`);
  serve path exists (`src/lib.rs:793` `TcpListener::bind`, `:795` `axum::serve`).
- **Live state:** DEAD. Zero listening sockets (full `ss -ltnp` sweep); no pitchfork stanza
  references it. `cargo check` passes; 8 pre-existing `cargo check --tests` errors (test code
  drifted from the lib API before the move — test-rot, for the proxy lane).
- **Port verdict:** `ranch/cuttinggate/CONTRACT.md` declares cuttinggate the TypeScript port of
  this proxy ("flock TS router — port contract"). Operationally the TS port has won:
  cuttinggate is live on `:25200`, the Rust proxy runs nowhere. The Rust tree is preserved
  in `ranch/mesh/proxy/flock-proxy/` — per Chris, not junk, not scrapped.

### 1.3 cuttinggate — TypeScript canonical router — `:25200` LIVE

- **Language:** TypeScript, Bun 1.4.3+, Elysia.
- **What it does (AST evidence):** `src/server.ts:180` `app.listen({ port: config.port, … })`;
  `src/config.ts:21` `port: Num.default(25194)` overridden to **`:25200`** by `CUTTINGGATE_PORT`
  in its pitchfork stanza. The estate's canonical OpenAI-wire router: fronts herd `:25100`
  (local GGUFs) and cloud providers, with auto-quarantine of dead model slugs, per-provider
  breakers, and a winner ledger. Its README: "The canonical router… Replacing :25104
  (sovereign-router-ts)".
- **Live state:** HEALTHY on `:25200`, pitchfork-supervised, restarted from the new path
  after the move (PID 80415, `/health` → `{"ok":true}`, `/v1/models` serving live data).
  With flock `:25193` down, cuttinggate has effectively absorbed the cloud-router role
  (`config/upstreams.yaml` moved cloud routes out of `herd.yaml` into cuttinggate).
- **Tests:** `bun test` 46/46 pass. `bun run build` (`tsc --noEmit`) fails with **74
  pre-existing type errors** (missing `src/shared.ts` that CONTRACT.md declares, `src/auth/`
  breakage, vendored `src/strategy/`) — verified byte-identical pre-move, not a regression.
  Port-lane backlog.
- **Home:** `ranch/mesh/proxy/cuttinggate/`.

### 1.4 sovereign-router — TypeScript router — `:25104` RETIRED (down)

- **Language:** TypeScript/Bun.
- **What it does (AST evidence):** OpenAI-compatible multi-provider LLM router —
  `/v1/chat/completions`, hybrid/hedged routing (`routeHybrid`), Elo health matrix, bench
  priors, `/mesh*` federation via `handleMeshRequest`. `Bun.serve({ port: PORT, hostname:
  "127.0.0.1" })` at `router.ts:182-184`; port from `SOVEREIGN_ROUTER_PORT || SOVEREIGN_PORT`
  (required — `router_config.ts:51-59` throws if unset). Docs say `:25104`;
  `estate/config/ports.env:80` says `:25104` retired ("merged into flock (:25193)") — the
  ports.env claim matches reality, and the router docs now carry a retired banner.
- **Live state:** DOWN. Nothing on `:25104`; its pitchfork manifest is `retired-20261002`.
- **Tests:** `bun run check` bundles 19 modules; `bun test` 114/114 pass (3 relative imports
  broke in the cross-repo move — fixed forward via hashline).
- **Home:** `ranch/mesh/router/sovereign-router/` (imported from `estate/tools/`).

### 1.5 keypool — key-management sidecar — `:25109` (down)

- **Language:** TypeScript/Bun.
- **What it does (AST evidence):** API-key pool daemon — key health probing, selection,
  failover, racing. `src/index.ts:12` `DEFAULT_PORT = 25109`; `Bun.serve` at `:70`. Bun port
  of the older `herd-keypool.py`.
- **Relation to routers:** called by `ranch/roundup/scripts/probe-keypool.py:13`
  (`KEYPOOL_BASE = "http://127.0.0.1:25109"`) and `estate/skills/scripts/health-audit.ts:62`
  (`:25109/health`). NOT called by sovereign-router (zero refs) or cuttinggate (which folded
  its own in-process keypool module — `proxy/cuttinggate/src/keypool.ts` references `:25109`
  only as "a separate keypool service").
- **Live state:** DOWN. Nothing on `:25109`.
- **Tests:** `bun run build` OK; `bun test` 21/21 pass (`bun run typecheck` has pre-existing
  errors, unchanged by the move).
- **Home:** `ranch/mesh/keypool/` (imported from `estate/services/`).

### 1.6 roost → `mesh/catalog` — provider catalog SSOT (TypeScript library, no port)

- **Language:** TypeScript (bun). The master provider catalog: provider definitions, live
  `/models` discovery adapters, alias map, curated seeds, auto-quarantine. `src/index.ts`
  exports `ModelCatalog`, `ADAPTERS`/`adapterFor`, `discover`, and codegen
  (`buildProvidersGo/Json/Rust/TauYaml`, `emitAll`).
- **Readers (AST evidence):** `flock/ts/src/providers/catalog.ts:20` imports
  `{ PROVIDER_DEFs } from "@ranch/roost"`; `flock/ts/astmatrix/src/providers.ts:16-21`
  imports `DEAD_MODEL_IDS, MODEL_ALIASES, PROVIDER_DEFS`; Go/Rust consumers use the
  generated artifacts (`generated/providers.go/.json/.rs`, `tau-models.yml`).
- **Live state:** no server — it's a library + generated artifacts. No pitchfork stanza,
  no port.
- **Tests:** `bun run build` exit 0; `bun test` 70/70 pass.
- **Home:** `ranch/mesh/catalog/` (moved via `git mv` from `flock/roost`, 25 files R100).

### 1.7 tack — VERIFIED merged into roost

The "Tack/Roost consolidation — complete" claim (ranch commit `84eb701`) checks out: no
separate tack tree exists anywhere (`ffs` + `git ls-files`); `git log --follow` on the
catalog traces back through `5d75050 flock: rename Tack to Roost`. Tack survives as
roost's provider-seed lineage inside `mesh/catalog/`.

### 1.8 Preserved router variants (were nested under `herd/mesh/`, now first-class)

The herd tree carried a diverged mesh snapshot (~555 files) holding the only copies of
several router attempts. All preserved — nothing of value left behind:

| Variant | What it is | Home |
|---|---|---|
| `sovereign-mcp-gateway` | Whole MCP trust-boundary service (`:25120`); 23/23 bun tests pass | `mesh/router/sovereign-mcp-gateway/` |
| `sovereign-ast-router` | TS/Bun port of the AST router (9Router/ULTIMATE_JULY_2026 lineage) | `mesh/router/flock-router/` |
| `flock-py` extras | v2 Python reference router (`router.py`, `router_config.py`, `router_strategy.py`, …) | `mesh/router/flock-py/` |
| `free_zed_gateway` extras | free-provider gateway (3-source lineage) | `mesh/router/free_zed_gateway/` |
| estate CloudRouter (`package flock`) | circuit breakers, Elo selection, health DB, token-bucket rate limit (Go) | `mesh/gateway/` |
| `flock-pkg` v1 | v1 synthesis + `i.py` command auto-fixer | `mesh/research/sovereign-ast-router-v1/` |

505 redundant snapshot files were dropped only after per-file verification (byte-identical
twins elsewhere in the ranch, or older upstream revisions). Husk deletion was justified by
sweeps: `ffs grep "mesh/router/herd/mesh"` over 71,069 files → 0 live references;
ast-grep over Go files → 0 matches.

---

## 2. Overlap matrix

| Pair | Relationship | Verdict |
|---|---|---|
| cuttinggate ↔ flock-proxy (Rust) | TS port per CONTRACT.md | Port won operationally (live :25200); Rust preserved, not live |
| cuttinggate ↔ sovereign-router | Successor | cuttinggate replaced `:25104` ("Replacing :25104"); old router retired, preserved |
| cuttinggate ↔ herd | Edge router ↔ inference backplane | Complementary layers, not duplicates |
| cuttinggate ↔ flock `:25193` | Cloud-router role | flock down; cuttinggate absorbed the role |
| keypool ↔ cuttinggate in-process keypool | Standalone service vs folded module | Distinct generations; standalone preserved |
| keypool ↔ `herd-keypool.py` | Bun port of Python predecessor | Distinct generations; both kept |
| catalog ↔ everything | Data layer (SSOT library) | No overlap — consumed by routers, duplicates nothing |
| Variants (flock-py, flock-router, free_zed_gateway, sovereign-mcp-gateway, ast-router) | Distinct attempts | Each unique; preserved in own homes |

**No true duplication requiring a merge was found** — every component does a distinct job or
is a distinct generation. Per Chris ("this is NOT a scrap operation"), everything was kept
and organized by role.

---

## 3. Verdict: roles and organization (not survival)

```
ranch/mesh/
  README.md            # one-pager: layers, ports, data flow (ss+curl verified)
  router/
    herd/              # Go inference backplane :25100 (DOWN — needs pitchfork restart)
    sovereign-router/  # TS router :25104 (retired, preserved)
    sovereign-mcp-gateway/ # MCP trust boundary :25120
    flock-py/          # v2 Python reference router
    flock-router/      # TS/Bun AST router
    free_zed_gateway/  # free-provider gateway variant
  proxy/
    flock-proxy/       # Rust cloud proxy (preserved, not live)
    cuttinggate/       # TS canonical router :25200 (LIVE)
  catalog/             # roost provider SSOT (TS library, no port)
  keypool/             # key sidecar :25109 (down)
  gateway/             # mcpproxy docs + estate CloudRouter (Go)
  browserless/  secretsmith/  gemini-mcp/  bin/  pitchfork.d/  research/
```

**Data flow (live):** clients → cuttinggate `:25200` → herd `:25100` (local GGUFs) + cloud
providers (via cuttinggate upstreams). Catalog feeds provider data to routers at build/codegen
time. Keypool `:25109` serves keys to roundup/health-audit (standalone; cuttinggate carries
its own in-process pool).

---

## 4. Migration record (all pushed, remote-verified)

**ranch** (`toxicwind/ranch`, origin/main `7b4d536`):
- `57ac1b8` mesh: move flock/proxy → mesh/proxy/flock-proxy
- `9a9a55d` mesh: move flock/roost → mesh/catalog
- `f6410f9` mesh: import sovereign-router from estate/tools (+ cuttinggate renames)
- `5a46db0` mesh: import keypool from estate/services
- `2738644` mesh: move herd → mesh/router/herd
- `283f32f` / `b9de0c5` / `aff7d72` / `6c9e7dd` variant preservation + snapshot removal
- `14b6fef` / `38c2892` / `401acad` ref fixes (catalog consumers, flock scripts, READMEs)
- `7b4d536` mesh README one-pager

**estate** (`toxicwind/estate`, origin/main `55cb68c764`):
- `8b25849` / `fbed6a9` remove `tools/sovereign-router`, `services/keypool` (moved to ranch)
- `e4a383cad8` ref fixes: `stack/services/herd.sh` → new binary path; pitchfork keypool +
  cuttinggate stanzas; `projects.toml` cuttinggate manifest (was about to silently drop
  cuttinggate from future composes); `config/tau` herd/router sources
- `55cb68c764` de-symlink (below)

**Symlinks:** REPOINTED `estate/herd` → `ranch/mesh/router/herd` (tracked, was dangling).
REMOVED (dangling, zero consumers): `estate/openfang`, `/home/toxic/.fleet-bus`,
`/home/toxic/tau/tau`, `/home/toxic/.tmp/tack`, `/home/toxic/smithers`.
KEPT + documented: `/home/toxic/ranch`, `/home/toxic/projects`, `/home/toxic/workspace/skills`,
`estate/{mesh,models,qed,shell,yote,tau-skills,shingle-workspace,.shared,cell-mirror}`,
dots. `/home/toxic/sovereign → estate` deliberately KEPT — 188 live refs in the skills-hub
submodule resolve through it; removing it breaks them (separate job).

**Notable catches during ref-fix:** flock-proxy `include_str!` pointed at the old catalog
path (was a compile break — fixed); `flock/ts/astmatrix` `@ranch/roost` dep repointed;
astmatrix serve-404 default moved off retired `:25104` → `:25200`.

---

## 5. Open items (not done in this pass)

1. **herd DOWN** — pitchfork restart needed (`herd.sh` launcher fixed and verified; binary
   intact at `mesh/router/herd/herd`). Ops follow-up.
2. **cuttinggate 74 pre-existing tsc errors** — port-lane backlog (missing `src/shared.ts`
   that CONTRACT.md declares).
3. **flock-proxy test-rot** — 8 pre-existing `cargo check --tests` errors.
4. **`docs/estate-map.*` regen** — Sable's lane (generated file, stale router rows).
5. **`sovereign/pitchfork.toml` `[daemons.mcp-gateway]`** — points at a path that never
   existed; code now lives at `ranch/mesh/router/sovereign-mcp-gateway/`. Repoint or retire
   the stanza (submodule repo — separate commit).

*Crew: Bramble (herd), Tinder (proxy), Sedge (catalog), Vole (cross-repo), Pipit (variants),
Kestrel (refs/symlinks/README), Marquee (presentability). Commit SHAs above; every fix in
real files, committed, pushed, remote-verified. No `git reset` anywhere in the operation.*
