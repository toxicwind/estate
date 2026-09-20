# freeproxy full restore — maximal, non-monkey-patch plan

Date: 2026-09-14. Owner lane: herd (llama-swap fork) inside `toxicwind/sovereign-projects` monorepo (`sovereign/herd/`).

## What was trying to happen

A first-class **free-inference subsystem** inside herd: `internal/freeproxy` — a modular
provider registry (Pollinations, OVHcloud, OpenRouter, Cloudflare AI Gateway) with
per-provider rate limiting and a shared response cache, dispatched from the server's
model-routing path so `POST :25100/v1/chat/completions` serves free/cheap models with
zero client config. Plus a Bun tester (`tools/pollinations-proxy/tester.ts`) and a
410-line hotfix plan (`docs/plans/free-pollinations-herd-hotfix-plan.md`, 2026-09-02).

## What actually exists (ground truth, verified 2026-09-14)

- **Complete freeproxy implementation, 803 lines**, in `sovereign-merge-stash-20260914/herd/internal/freeproxy/`:
  `provider.go` (Provider/RateLimiter/Cache interfaces), `registry.go` (multi-provider
  router, first-provider-wins model map), `pollinations.go` (226 lines, gen+text fallback,
  `POLLINATIONS_API_KEY` env support), `cloudflare.go`, `openrouter.go`, `ovh.go`,
  `cache_global.go` (disk cache at `$HOME/cache/freeproxy`).
- **Server integration seam** in the stash tree (`internal/server/server.go`):
  `freeproxy.NewRegistry(...)` built at startup, dispatch
  `case s.freeproxy != nil && s.freeproxy.Handles(data.ModelID)` → `ProviderFor(...).Proxy(...)`.
- **NOT in live `sovereign/herd/`**: no `internal/freeproxy` at all.
- **Live `config/llama-swap.yaml`** has a `peers.pollinations-free` block whose comments
  claim "herd injects dummy Bearer via patched peer.go when apiKey is empty" — **false**:
  live `internal/router/peer.go:171-174` has no such injection. Dead config lying in the file.
- **Reality changed 2026-09-14**: Pollinations killed the anonymous tier (now 401s; needs a
  real key from enter.pollinations.ai/keys). Live config already pivoted: `openrouter-kimi`
  peer serves real Kimi models via `OPENROUTER_API_KEY` (commit `d9371089de`).
- The stash tree diverges from live in **many** files (astmatrix, bench, perf, process, router,
  server — 16 stash-only dirs/files). It is a whole divergent branch, **not** a clean
  freeproxy diff. Restore must be **surgical extraction**, not a merge of the tree.

## The monkey-patch version (explicitly rejected)

Config-only `peers:` hack + P1 auth-strip patch in `peer.go` + dummy bearer. That is what
the 2026-09-02 plan proposed and what the dead config block still pretends exists.
We do not do this.

## The maximal restore

### Phase 0 — Surgical extraction (no tree merge)
1. Diff stash vs live for exactly: `internal/freeproxy/*`, `internal/server/server.go`
   (freeproxy seams only), `internal/router/peer.go` + `peer_test.go` (freeproxy-related
   hunks only), `internal/config/peer.go` (if touched for freeproxy).
2. Extract those hunks into a feature branch off live main. Everything else in the stash
   tree (astmatrix/bench/perf/process drift) is out of scope — separate lanes.

### Phase 1 — freeproxy as a first-class subsystem
1. Land `internal/freeproxy` in live herd as a real package: proper doc comments, no
   "borrows tau providers concept" / "ponytail" graffiti, exported API cleaned up.
2. **Config-driven, not hardcoded.** Stash hardcodes the provider list in `NewRegistry`.
   Add a `freeproxy:` section to herd's config schema (YAML):
   ```yaml
   freeproxy:
     enabled: true
     cacheDir: ${HOME}/cache/freeproxy
     providers:
       pollinations: { enabled: true, apiKey: ${env.POLLINATIONS_API_KEY}, rateLimitPerSec: 0.066 }
       cloudflareGateway: { enabled: false, accountId: ..., token: ${env.CLOUDFLARE_AI_TOKEN} }
       openrouter: { enabled: true, apiKey: ${env.OPENROUTER_API_KEY}, onlyFree: true }
       ovh: { enabled: false }  # 403 as of 2026-09-02, keep as explicit off
   ```
   Registry is built from config. Missing key + enabled provider = fail-fast at startup
   with a clear message, never a silent 401 at request time.
3. **Server integration done properly**: land the dispatch seam with explicit precedence,
   documented in `internal/router/design.md`:
   `local GGUF models → freeproxy (config order) → peers → 404`. Precedence is a config
   value, not an accident of if/else ordering.
4. **Model namespacing**: freeproxy serves exact upstream IDs today (`openai`, `kimi-k3`…).
   Add the `modelAliases` mechanism the old plan parked (P4) as a real feature:
   `pollinations/openai → openai` upstream rewrite, so a future local `openai` alias can
   never collide. Ship with exact IDs exposed, aliasing available and tested.

### Phase 2 — Adapt to the post-free-tier reality
1. **Pollinations provider**: anonymous path is dead — remove the dummy-bearer workaround
   entirely (it now guarantees 401s). Require `POLLINATIONS_API_KEY`; Health() probes
   `/v1/models` with the key at startup and marks the provider down cleanly if invalid.
2. **Reconcile peers vs freeproxy — one owner.** Delete the dead `peers.pollinations-free`
   block and its lying comments from `config/llama-swap.yaml`. Move Kimi routing into
   freeproxy's OpenRouter provider (`onlyFree: true` + explicit model list incl.
   `moonshotai/kimi-k3`) and retire the `openrouter-kimi` peer, OR keep the peer and
   disable OpenRouter inside freeproxy. Decide once, document once. No two owners.
3. OVH stays `enabled: false` with the 403 documented — no retry-burn.

### Phase 3 — Tests (no weakened assertions)
1. Per-provider unit tests with `httptest` upstreams: auth injection, 401/429 handling,
   gen→text fallback (Pollinations), rate limiter pacing, cache hit/miss, registry
   precedence (first-provider-wins), disabled-provider exclusion.
2. Server dispatch test: model routed to freeproxy vs local vs peers vs 404.
3. Config test: missing key + enabled provider fails fast at load.
4. `go vet ./...` + full `go test ./...` green.

### Phase 4 — Tester refresh
`tools/pollinations-proxy/tester.ts` exists (340 lines) but encodes the dead anonymous
assumption. Update probes: T1 becomes keyed-direct, keep T2 (wrong model → 401) as
documentation, T4–T6 via herd expecting 200 with real key, T8 rate-limit probe updated
for keyed limits. Rename to `tools/freeproxy/tester.ts` — it tests the subsystem now,
not one provider.

### Phase 5 — Deploy
1. `go build` in `sovereign/herd`, binary to the path `stack/services/llama-swap.sh` uses.
2. Config edit (`config/llama-swap.yaml`): replace dead peer block with `freeproxy:` section.
   Validate: `llama-swap --config config/llama-swap.yaml --check`.
3. `pitchfork restart herd`; `curl :25100/health`; `GET :25100/v1/models` shows freeproxy models.
4. Live inference + streaming smoke; one `omp bench` call against a freeproxy model, no 402.
5. Commit + push to `toxicwind/sovereign-projects` main (monorepo; herd is a subtree —
   no worker-to-worker overlap, own the `sovereign/herd` + `sovereign/config` paths).

### Phase 6 — Docs
- `sovereign/herd/internal/freeproxy/README.md`: architecture, config reference, provider
  status matrix (Pollinations keyed 2026-09-14, OVH 403, OpenRouter free-tier key-dependent,
  CF gateway parked).
- Update `docs/plans/free-pollinations-herd-hotfix-plan.md` header: superseded by this
  restore; anonymous tier dead.

## Exit criteria
- [ ] `internal/freeproxy` in live herd, config-driven, documented
- [ ] Dead `peers.pollinations-free` block + false comments removed from `config/llama-swap.yaml`
- [ ] One owner for Kimi/free routing (freeproxy or peers, not both)
- [ ] `go vet` + `go test ./...` green, new tests asserting real behavior
- [ ] `:25100/v1/models` lists freeproxy models; inference + streaming 200 live
- [ ] Tester green; commit pushed to sovereign-projects main
- [ ] No `pitchfork.toml`/`mise.toml` hand edits (generation latch holds — no new daemon)

## Open questions for Chris
1. Do we have a real `POLLINATIONS_API_KEY` (enter.pollinations.ai/keys), or should the
   Pollinations provider ship `enabled: false` until you provision one?
2. Kimi routing: freeproxy's OpenRouter provider absorbs the `openrouter-kimi` peer, yes?
