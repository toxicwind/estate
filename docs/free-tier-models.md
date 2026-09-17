# Free-Tier Model Routing — Ground Truth (2026-09-14)

How free models actually work across our providers, verified live. No marketing claims, only probed results.

## The short version

- **Only OpenRouter has a `:free` convention.** 19 `:free` models in its 445-model catalog right now. **Zero Kimi/Moonshot `:free` models** — the Kimi free lineup rotated off ~11 days ago.
- **Opencode uses a `-free` suffix** (e.g. `mimo-v2.5-free`) on its Zen API, but Zen 403s from our egress, so it's unverified from here.
- **Nobody else has a free-tier model convention**: Groq, Cerebras, DeepSeek, Mistral, Gemini, NVIDIA NIM, Anthropic, HuggingFace — zero free IDs.
- **Pollinations is no longer free keyless.** `gen.pollinations.ai` requires an API key (401 without); the old `image.pollinations.ai` went paid (402). Free Seed tier exists via registration at `auth.pollinations.ai`.
- **Our OpenRouter key is NOT free-tier** (`is_free_tier: false`, $0.004 used, zero credits). `:free` models that serve on other keys 404 for ours. Paid models 402. This matches our own 2026-09-02 deep dive exactly.

## Per-provider probe results (2026-09-14)

| Provider | /models endpoint | Status | Models | Free IDs |
|---|---|---|---|---|
| OpenRouter | openrouter.ai/api/v1/models | 200 | 445 | 19 × `:free` (no Kimi) |
| DeepSeek | api.deepseek.com/v1/models | 200 | 2 | 0 |
| Mistral | api.mistral.ai/v1/models | 200 | 46 | 0 |
| Gemini | generativelanguage.googleapis.com/v1beta/models | 200 | 50 | 0 |
| NVIDIA NIM | integrate.api.nvidia.com/v1/models | 200 | 81 | 0 |
| Groq | api.groq.com/openai/v1/models | 403 (Cloudflare 1010, egress) | — | — |
| Cerebras | api.cerebras.ai/v1/models | 403 (Cloudflare 1010, egress) | — | — |
| Anthropic | api.anthropic.com/v1/models | **401 invalid x-api-key — key dead** | — | — |
| Opencode Zen | opencode.ai/zen/v1/models | 403 (Cloudflare 1010, egress) | — | `-free` suffix per docs, unverified |
| HuggingFace | inference /models | NXDOMAIN — no served-inference /models | — | — |
| Scout | 127.0.0.1:25100/v1/models | 200 | 98 | = herd itself; `:free` IDs are our own peer config |

OpenRouter's current 19 `:free` IDs: `cohere/north-mini-code:free`, `dots-studio/dots-3-note-preview:free`, `google/gemma-4-26b-a4b-it:free`, `google/gemma-4-31b-it:free`, `inclusionai/ling-3.0-flash-{fin,sante,vl}:free`, `liquid/lfm-2.5-2.6b:free`, `nex-agi/nex-n2.5-{mini,pro}:free`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `nvidia/nemotron-3-ultra-550b-a55b:free`, `nvidia/nemotron-3.5-content-safety:free`, `nvidia/nemotron-3.5-lightning:free`, `poolside/laguna-{s,xs}-2.1:free`, `thinkingmachines/inkling{,-small}:free`.

## Kimi routing status (kimi-auto)

- `kimi-auto` is Kimi-only by design (Chris's order). It returns an honest **503** when no Kimi model is healthy — no silent `gpt-oss-20b` fallback.
- 7 Kimi `:free` IDs are wired in the `openrouter-kimi` herd peer (additive, nothing removed). They auto-activate if OpenRouter re-enables Kimi free — zero code changes needed.
- **To route Kimi today**: top up OpenRouter credits at `openrouter.ai/settings/credits`, or provide `MOONSHOT_API_KEY`/`KIMI_API_KEY`. There is no Kimi/Moonshot key in `.secrets` at all.
- Related: the dead `pollinations-free` herd peer stays in place (Chris: don't remove things).

## Key health flags

- **Anthropic key is dead** (401 invalid x-api-key) — needs rotation.
- Groq/Cerebras/Opencode 403s are Cloudflare error 1010 from our egress, not necessarily bad keys.
- Pollinations free tier: only exact upstream model IDs ever worked no-auth (e.g. `openai`, not `openai/gpt-oss-20b`); herd had an auth-stripping bug (client dummy Bearer <redacted> upstream when `apiKey==""`). See `docs/plans/free-pollinations-herd-hotfix-plan.md` (2026-09-02 deep dive).

## Artifacts

- Probe report: `/home/toxic/wt-freeprobe-20260914/free-models-report.json`
- Probe script (re-runnable, prints key names only, never values): `/home/toxic/wt-freeprobe-20260914/probe_free_models.py`
- Free-convention fuzzing: in progress (see below).

## 2026-09-17 Ling re-probe (Herd/Mesh lane)

- `inclusionai/ling-3.0-flash-fin:free` through OpenRouter on OUR key: **HTTP 200, cost 0**
  (cost_details upstream all 0) via provider Novita. This contradicts the 2026-09-14 finding
  that our key 404s on `:free` — key/route state changed; `:free` now serves at zero cost
  even though `is_free_tier: false` on the key (usage $0.004).
- Speed: one run delivered 250 completion tokens in 1,204 ms (~207 tok/s end-to-end).
  Cold TTFT ~3,084 ms on one correct run (17*23=391 correct).
- **Reliability: FAIL.** 4 of 5 subsequent probes returned HTTP 200 with EMPTY content
  (finish_reason "stop", zero content deltas, ~850-900 ms). The free Novita route is
  severely intermittent — empty completions, no error signal.
- **Routing verdict: NOT wired into the live free pool.** The live
  `sovereign-router-ts` `free` strategy races `freeCandidates()` from `router_config.ts`,
  which has no Ling entry; mesh `config.yml` line 65 declares
  `default: openrouter/inclusionai/ling-3.0-flash-fin:free:high` but NOTHING parses
  `:free:high` — declared intent only, not active routing policy. Deliberately not added:
  an empty-completion route would poison the `free` strategy (first "valid" response wins).
- Acceptance gate for wiring: free + zero-cost + **5/5 non-empty correct** over the
  correctness battery (17*23, YES/NO, hatch-42, cat->tac) + TTFT < 2 s warm.

## 2026-09-17 Ling benchmark correction + wired into live free pool (~04:30 MDT)

- The earlier 0/8 benchmark was a BUG IN THE PROBE: it used the invalid model ID
  `openrouter/inclusionai/ling-3.0-flash-fin:free` (double prefix). OpenRouter returns
  HTTP 400 on that ID. Correct ID: `inclusionai/ling-3.0-flash-fin:free`.
- Corrected streaming benchmark: 2 rounds x 4 fixtures (17*23, YES/NO, hatch-42,
  reverse-tac) = **8/8 non-empty and correct**, all via Novita at zero cost.
  TTFT: 830/1812/969/913 ms (round 1), 1927/1273/1283/810 ms (round 2). Warm TTFT < 2 s.
  Evidence: `tools/ling_bench_20260917.json`.
- Acceptance gate met (free + 5/5 non-empty correct + warm TTFT < 2 s), so Ling was
  wired into the live pool: `inclusionai/ling-3.0-flash-fin:free` added to the
  `openrouter` array in `projects/mesh/router/sovereign-router-ts/router_config.ts`
  (it is enumerated by `freeCandidates()` in `router_strategy.ts`, which picks up
  every configured ID containing `:free`).
- Router restarted via pitchfork 04:25 MDT; `/health` 200. `freeCandidates()` verified
  live: **14 candidates, Ling present** (`["openrouter","inclusionai/ling-3.0-flash-fin:free"]`).
- Historical note: earlier probes the same day showed 4/5 empty completions on the
  Novita route — severely intermittent. The empty-response hazard remains: if Ling
  flakes again, `routeAstRace()` prefers AST-shaped content and otherwise keeps the
  first successful result, so an empty response should not win as valid — but watch it.
- mesh `config.yml` `default: openrouter/inclusionai/ling-3.0-flash-fin:free:high`
  is still declared intent only (no `:high` parser) — the live policy is
  `freeCandidates()`, which now includes Ling.
