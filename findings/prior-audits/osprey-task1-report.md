# Task 1/6: Dots TypeScript port generalized to all OpenRouter models

Date: 2026-10-13. Lane: Osprey (emergent). Commit: `c917869e` on toxicwind/tau main (pushed, remote ref verified).

## What was built

New module `packages/ai/src/providers/openrouter-coercion.ts` — the
SovereignDotsClient coercions generalized to **any OpenRouter-routed model**,
gated on `compat.isOpenRouterHost` (catalog-resolved), never on model ID:

- `normalizeOpenRouterMessages` — assistant `content` null/undefined → `""`
- `applyOpenRouterStrictToolSchemas` — `strict:true` + `additionalProperties:false`, deep-copied
- `applyOpenRouterRequestShaping` — temperature 0.1 default, `provider.require_parameters:true` + `allow_fallbacks:false` fill-in

Wiring: chat-completions `buildParams` (message normalization, `all_strict`
tools for OpenRouter hosts, shaping with Dots-scoped reasoning cap);
Responses path (provider-only). `OpenRouterRouting` gains
`require_parameters` / `allow_fallbacks`.

## Two corrections proven by live measurement (dots-3-note-preview:free)

1. **stop + require_parameters is unroutable.** Custom `stop` sequences with
   `provider.require_parameters:true` → OpenRouter 404 "no endpoints found"
   (each works alone; bisected across 15 probes). The original Python
   client's full payload would 404 on the very model it was built for.
   Provider constraints win; stop is skipped when require_parameters is set.
2. **Reasoning cap stays Dots-scoped.** Re-adding a reasoning object breaks
   deliberate pipeline decisions (adaptive efforts must go 1:1 on the wire;
   issue #827 forced-toolChoice stripping for Kimi). Opt-in per call site.

## Verification

- 18 new unit tests (`openrouter-coercion.test.ts`); full targeted run:
  160 pass, 2 fail — both failures confirmed pre-existing on the pristine
  tree (git stash comparison).
- `bun run check:types` clean; oxlint + oxfmt clean.
- Live OpenRouter: dots-3-note-preview:free → 200, 535ms,
  finish=tool_calls, structured tool args, null-content replay turn
  normalized, no ghost output. Paid models (gpt-oss-20b, qwen3-32b) → 402
  insufficient credits (key has no credits; top-up is User's call).
- Binary rebuild + install to ~/.local/bin/tau: see build log.

## Files

- `packages/ai/src/providers/openrouter-coercion.ts` (new)
- `packages/ai/test/openrouter-coercion.test.ts` (new, 18 tests)
- `packages/ai/src/providers/openai-completions.ts` (wiring)
- `packages/ai/src/providers/openai-responses.ts` (provider-only shaping)
- `packages/catalog/src/types.ts` (OpenRouterRouting fields)
- `packages/ai/test/openai-responses-openrouter.test.ts`, `openai-responses-cache-affinity.test.ts` (contract updates)
