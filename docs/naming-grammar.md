# Sovereign Model Naming Grammar (canonical, 2026-09-20)

Chris: "the naming conventions we are using in config is confusing as fuck."
This document is the fix. Every model/provider ID in the estate MUST be
parseable into these layers. If it isn't, it's a bug — run the validator.

## The six layers

```
<lane>/<source>/<identity>-<variant> [policy-alias?] [metadata→model-health.json]
```

| # | Layer | What it is | Examples |
|---|-------|-----------|----------|
| 1 | **Lane** (execution source) | WHERE it runs. Tau provider name. Closed set: `herd`, `sovereign` | `herd/…`, `sovereign/free` |
| 2 | **Source** (who serves it) | Local: the fork/builder. Cloud: the API provider (peer name) | `beellama`, `mradermacher`, `jackrong`, `mistral`, `moonshot`, `gemini`, `openrouter-free`, `flock-direct`, `toolcall-local` |
| 3 | **Identity** (upstream model) | The model family, no provider prefix | `exaone-4.0-1.2b`, `qwen3.5-9b-deepseek-v4-flash`, `gemma-4-12b`, `qwen-flash`, `ministral-8b-latest`, `kimi-k2.6` |
| 4 | **Variant** (quant+ctx+build) | Quantization, context window, build flags | `iq4xs-32k`, `q4km-64k`, `da-128k`, `uncensored`, `i1` |
| 5 | **Policy alias** (DEPRECATED) | Generic words kept ONLY as compat aliases | `fast`, `tiny`, `small`, `medium`, `code`, `long`, `uncensored` |
| 6 | **Metadata** (never in the ID) | Health, RPM, TTFT, pricing | Lives in `/home/toxic/sovereign/data/model-health.json` ONLY |

## Canonical patterns

**Local model block:** `{builder}/{identity}-{variant}`
- `beellama/exaone-4-0-1-2b-iq4xs`
- `jackrong/qwen3.5-9b-deepseek-v4-flash-da-q4km`

**Short alias (preferred for clients):** `{identity}-{variant}`, no builder prefix
- `qwen-flash-da-128k` → `jackrong/qwen3.5-9b-deepseek-v4-flash-da-q4km`
- `exaone-1.2b-iq4xs-32k` → `beellama/exaone-4-0-1-2b-iq4xs`

**Peer (cloud) model:** `{peer}/{upstream-id-verbatim}`
- `mistral/ministral-8b-latest`, `moonshot/kimi-k2.6`, `flock-direct/nvidia/nemotron-3.5-lightning-30b-a3b`
- The upstream ID is sent VERBATIM to the provider proxy — never shortened.

**Tau client ref:** `{lane}/{model-or-alias}`
- `herd/qwen-flash-da-128k`, `herd/beellama/exaone-4-0-1-2b-iq4xs`, `sovereign/free`

## Rules

1. **No generic words as canonical IDs.** `fast`, `tiny`, `small`, `medium`,
   `large`, `code`, `quality` describe nothing. The 7 surviving generic aliases
   (`fast`, `tiny`, `small`, `medium`, `code`, `long`, `uncensored`) are
   grandfathered as DEPRECATED compat aliases — they keep working, new code
   MUST NOT use them, and the validator fails on any NEW generic alias.
   (`large` and `quality` were quarantined 2026-09-20 — they 500'd.)
2. **Double source qualification is inherent for peers, forbidden elsewhere.**
   `mistral/mistral-medium-latest` looks redundant but the upstream API ID
   really is `mistral-medium-latest` — the proxy needs it verbatim. What is
   forbidden: inventing a THIRD level (tau refs are `herd/mistral/…`, never
   deeper) or adding a redundant prefix to a local model that already carries
   its builder.
3. **One alias → one model, always.** Alias collisions fail validation.
   An alias MUST NOT equal another model's block name (shadowing).
4. **Aliases are additive.** Removing an alias breaks unknown consumers
   (2026-09-20: `null-g-proxy` and `fast_race.py` consume the `fast` alias).
   Deprecate in docs, never delete silently.
5. **Every consumer ref must resolve to a HEALTHY model.** Tau `modelRoles`,
   router profiles, matrix vars, fifo priorities — all validated against the
   live `/v1/models` catalog and `model-health.json`. (2026-09-20: the
   `backup` router profile pointed at `herd/pollinations-free/openai`, a model
   that no longer exists — caught by this rule.)
6. **Stale refs are bugs.** Quarantined/removed models MUST NOT appear in
   matrix vars, evict_costs, scheduler, roles, or profiles. llama-swap
   fail-closes on dangling matrix refs (keeps serving the OLD config).
7. **Duplicate upstream claims must be explicit variants.** Three builds of
   `qwen3.5-9b-deepseek-v4-flash` exist (`mradermacher` i1 q4_k_m/q4_k_s,
   `jackrong` da q4km) — they differ by builder+quant+ctx and the MODEL-MAX
   winner is marked. Same upstream + same variant + different name = bug.
8. **Peer names say what they are.** `openrouter-ling` vs `openrouter-free`
   are two different OpenRouter registrations (parked Ling routes vs free
   tier) — documented, not renamed (renaming a peer changes live IDs).

## Deprecated alias registry (keep working, do not use in new code)

| Alias | Resolves to | Why deprecated |
|-------|-------------|----------------|
| `fast` | `beellama/exaone-4-0-1-2b-iq4xs` | "Fast" only because it's 1.2B; collides with router profile name `fast` → different model |
| `tiny` | `beellama/exaone-4-0-1-2b-iq4xs` | Same as above; also a tau role name (separate namespace) |
| `small` | `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m` | Says nothing (9B) |
| `medium` | `gemma-4-12b-unified` | Says nothing (12B) |
| `code` | `gemma-4-12b-unified` | Claims code specialization on a general model |
| `long` | `beellama/qwen-flash-256k` | Honest (256k ctx) but vague; prefer `qwen-flash-256k` |
| `uncensored` | `gemma-4-12b-uncensored` | Honest; prefer `gemma-uncensored` |

## Canonical alias additions (2026-09-20)

| New alias | Model | Replaces (deprecated) |
|-----------|-------|----------------------|
| `exaone-1.2b-iq4xs-32k` | `beellama/exaone-4-0-1-2b-iq4xs` | `fast`, `tiny` |
| `qwen3.5-9b-i1-q4km-64k` | `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m` | `small` |

(`medium`/`code` already have descriptive `gemma-4-12b`; `long`/`uncensored`
already have descriptive short aliases.)
