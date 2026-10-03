/**
 * Canonical provider data — the single source of truth for the estate.
 *
 * Reconciled 2026-09-30 from:
 * - tools/sovereign-router/sovereign-router-ts/router_config.ts
 *   (PROVIDERS, PROVIDER_MODELS, CODING, DEAD_MODEL_IDS)
 * - projects/range/ranch/stockyard/herd/internal/astmatrix/providers.go
 *   (defaultProviders, codingAlias)
 *
 * Reconciliation notes (newer audit wins on conflict):
 * - openrouter seeds: TS 2026-09-21 sweep (4 verified) ∪ herd 2026-07-28
 *   list minus openai/gpt-oss-20b:free (delisted 2026-09-21 → deadIds).
 * - nvidia seeds: TS 12 (superset of herd's minus meta/llama-3.3-70b-instruct,
 *   EOL 2026-08-26 → deadIds). Herd gains nemotron-3-nano-omni-30b-a3b-reasoning.
 * - groq seeds: identical in both (6); the 4 verified-dead 2026-09-30 stay
 *   in seeds but are filtered by deadIds everywhere (cold start included).
 * - herd seeds: the canonical stable role names. The TS router
 *   overlays its runtime LOCAL_ROLES (best-models.json) at catalog build;
 *   herd serves these names directly.
 * - mistral: baseUrl WITHOUT the /v1 segment; the mistral adapter appends
 *   /v1/models via the default modelsPath. (The old `${base}/models`
 *   composition would have produced /v1/models correctly only by accident
 *   of the hardcoded base; the package composes it explicitly.)
 * - google: configured against the v1beta/openai compat endpoint, so the
 *   adapter is "openai". The native "google-v1beta" adapter exists for
 *   providers that stop using /openai.
 * - kimi-auto: static ["kimi-auto"] — the shim's virtual model is the whole
 *   list (adapter "none" would wrongly demote the seed after one refresh).
 * - nim-local / kimi-auto are TS-router-local concepts (local proxy + shim);
 *   marked routerLocal: true — herd and other consumers skip them by flag,
 *   no name denylist.
 * - keyEnvAlt for nvidia is NVIDIA_API_KEYS (TS multi-key pool, the live
 *   semantic). Herd previously used NVIDIA_NIM_API_KEY as its alt.
 * - aliases: union of TS CODING + herd codingAlias, restricted to pairs
 *   whose provider is one of the 9 core defs. Excluded: strategy
 *   directives (auto/fcm/free → null, router-local), runtime-dynamic
 *   local-role aliases (router-local overlays), aliases pointing at
 *   deadIds (nim-llama-3.3-70b, gpt-oss-20b — removed by the TS 2026-09-21
 *   sweep), and extended-registry aliases (opencode, xai-*, mimo-auto,
 *   perplexity-sonar, together-llama-3.3 — they belong to herd's registry
 *   layer, which stays in registry.go).
 * - Conflict resolutions (newer TS audit wins): nemotron-nano and
 *   nim-nemotron-nano point at the nvidia reasoning model, not the
 *   openrouter :free form.
 *
 * CONTRACT:
 * - `seeds` are cold-start data only (served pre-discovery, inert after).
 * - Membership of the live set is owned by discovery, never by this file.
 * - `deadIds` is the permanent EOL tier. Everything else prunes via
 *   quarantine (serve-404 or vanished-from-live-listing x2).
 */
import type { ModelAlias, ProviderDef } from "./types.ts";

export const PROVIDER_DEFS: ProviderDef[] = [
  {
    name: "herd",
    displayName: "herd (local)",
    baseUrl: "http://127.0.0.1:25100/v1",
    keyEnv: "HERD_API_KEY",
    auth: "none",
    adapter: "openai",
    seeds: ["local-fast", "local-quality", "local-longctx"],
  },
  {
    name: "nim-local",
    displayName: "NIM proxy (local)",
    baseUrl: "http://127.0.0.1:8000/v1",
    keyEnv: "NIM_PROXY_API_KEY",
    auth: "bearer",
    adapter: "openai",
    seeds: [],
    routerLocal: true,
  },
  {
    name: "kimi-auto",
    displayName: "kimi-auto shim",
    baseUrl: "http://127.0.0.1:25105/v1",
    keyEnv: "KIMI_AUTO_SHIM_KEY",
    auth: "none",
    adapter: "static",
    staticModels: ["kimi-auto"],
    seeds: ["kimi-auto"],
    routerLocal: true,
  },
  {
    name: "openrouter",
    baseUrl: "https://openrouter.ai/api/v1",
    keyEnv: "OPENROUTER_API_KEY",
    auth: "bearer",
    adapter: "openai",
    seeds: [
      "poolside/laguna-xs-2.1:free",
      "google/gemma-4-31b-it:free",
      "nvidia/nemotron-3-super-120b-a12b:free",
      "inclusionai/ling-3.0-flash-fin:free",
      "google/gemma-4-26b-a4b-it:free",
      "nvidia/nemotron-3-nano-30b-a3b:free",
      "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
      "nvidia/nemotron-nano-12b-v2-vl:free",
      "nvidia/nemotron-nano-9b-v2:free",
      "nvidia/nemotron-3-ultra-550b-a55b:free",
      "poolside/laguna-s-2.1:free",
      "cohere/north-mini-code:free",
      "inclusionai/ling-3.0-flash:free",
    ],
  },
  {
    name: "nvidia",
    baseUrl: "https://integrate.api.nvidia.com/v1",
    keyEnv: "NVIDIA_API_KEY",
    keyEnvAlt: "NVIDIA_API_KEYS",
    auth: "bearer",
    adapter: "openai",
    seeds: [
      "nvidia/nemotron-3-super-120b-a12b",
      "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
      "nvidia/nemotron-3-nano-30b-a3b",
      "meta/llama-3.1-70b-instruct",
      "qwen/qwen3.5-397b-a17b",
      "qwen/qwen3.5-122b-a10b",
      "deepseek-ai/deepseek-v4-flash",
      "deepseek-ai/deepseek-v4-pro",
      "mistralai/mistral-large-3-675b-instruct-2512",
      "google/gemma-4-31b-it",
      "z-ai/glm-5.2",
      "thinkingmachines/inkling",
    ],
  },
  {
    name: "groq",
    baseUrl: "https://api.groq.com/openai/v1",
    keyEnv: "GROQ_API_KEY",
    auth: "bearer",
    adapter: "openai",
    seeds: [
      "llama-3.3-70b-versatile",
      "qwen/qwen3-32b",
      "qwen/qwen3.6-27b",
      "openai/gpt-oss-120b",
      "openai/gpt-oss-20b",
      "meta-llama/llama-4-scout-17b-16e-instruct",
    ],
  },
  {
    name: "cerebras",
    baseUrl: "https://api.cerebras.ai/v1",
    keyEnv: "CEREBRAS_API_KEY",
    auth: "bearer",
    adapter: "openai",
    seeds: [],
  },
  {
    name: "google",
    baseUrl: "https://generativelanguage.googleapis.com/v1beta/openai",
    keyEnv: "GOOGLE_API_KEY",
    auth: "bearer",
    adapter: "openai",
    seeds: [
      "models/gemini-2.5-flash",
      "models/gemini-2.5-flash-lite",
      "models/gemini-2.0-flash",
      "models/gemma-4-31b-it",
    ],
  },
  {
    name: "mistral",
    baseUrl: "https://api.mistral.ai",
    keyEnv: "MISTRAL_API_KEY",
    auth: "bearer",
    adapter: "mistral",
    seeds: [
      "mistral-small-latest",
      "codestral-latest",
      "mistral-large-latest",
      "mistral-medium-latest",
    ],
  },
];

/**
 * MODEL_ALIASES — friendly alias → [provider, model] (UX layer).
 *
 * Union of sovereign-router-ts CODING and herd codingAlias (see header for
 * the exclusion rules). Strategy directives and runtime-dynamic local-role
 * aliases stay router-local overlays.
 */
export const MODEL_ALIASES: Record<string, ModelAlias> = {
  ling: ["openrouter", "inclusionai/ling-3.0-flash-fin:free"],
  "ling-flash": ["openrouter", "inclusionai/ling-3.0-flash:free"],
  "laguna-xs": ["openrouter", "poolside/laguna-xs-2.1:free"],
  "laguna-s": ["openrouter", "poolside/laguna-s-2.1:free"],
  "gemma4-31b": ["openrouter", "google/gemma-4-31b-it:free"],
  "gemma4-26b": ["openrouter", "google/gemma-4-26b-a4b-it:free"],
  "nemotron-super": ["openrouter", "nvidia/nemotron-3-super-120b-a12b:free"],
  "nemotron-nano": ["nvidia", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"],
  "nemotron-ultra": ["openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"],
  "nemotron-omni": [
    "openrouter",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
  ],
  "north-mini": ["openrouter", "cohere/north-mini-code:free"],
  "nim-nemotron-super": ["nvidia", "nvidia/nemotron-3-super-120b-a12b"],
  "nim-nemotron-omni": [
    "nvidia",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
  ],
  "nim-nemotron-nano": [
    "nvidia",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
  ],
  "nim-llama-3.1-70b": ["nvidia", "meta/llama-3.1-70b-instruct"],
  "nim-qwen3.5-397b": ["nvidia", "qwen/qwen3.5-397b-a17b"],
  "nim-qwen3.5-122b": ["nvidia", "qwen/qwen3.5-122b-a10b"],
  "nim-deepseek-v4-flash": ["nvidia", "deepseek-ai/deepseek-v4-flash"],
  "nim-deepseek-v4-pro": ["nvidia", "deepseek-ai/deepseek-v4-pro"],
  "nim-mistral-large-3": [
    "nvidia",
    "mistralai/mistral-large-3-675b-instruct-2512",
  ],
  "nim-gemma4-31b": ["nvidia", "google/gemma-4-31b-it"],
  "nim-glm5.2": ["nvidia", "z-ai/glm-5.2"],
  "nim-inkling": ["nvidia", "thinkingmachines/inkling"],
  "gemini-2.5-flash": ["google", "models/gemini-2.5-flash"],
  "gemini-2.5-flash-lite": ["google", "models/gemini-2.5-flash-lite"],
  "gemini-2.0-flash": ["google", "models/gemini-2.0-flash"],
  "gemma4-31b-google": ["google", "models/gemma-4-31b-it"],
  "mistral-small": ["mistral", "mistral-small-latest"],
  codestral: ["mistral", "codestral-latest"],
  "mistral-large": ["mistral", "mistral-large-latest"],
  "mistral-medium": ["mistral", "mistral-medium-latest"],
  "groq-llama-3.3-70b": ["groq", "llama-3.3-70b-versatile"],
  "groq-qwen3-32b": ["groq", "qwen/qwen3-32b"],
  "groq-qwen3.6-27b": ["groq", "qwen/qwen3.6-27b"],
  "groq-gpt-oss-120b": ["groq", "openai/gpt-oss-120b"],
  "groq-gpt-oss-20b": ["groq", "openai/gpt-oss-20b"],
  "groq-llama-4-scout": ["groq", "meta-llama/llama-4-scout-17b-16e-instruct"],
};

/**
 * DEAD_MODEL_IDS — permanent EOL tier. Never served, never re-admitted.
 *
 * - NVIDIA 410-retired (EOL dates from the retirement notices, 2026-09-21).
 * - OpenRouter-delisted (verified against the public /models list 2026-09-21).
 * - Groq 404-verified (live re-verification 2026-09-30).
 */
export const DEAD_MODEL_IDS: string[] = [
  // NVIDIA-retired (410).
  "moonshotai/kimi-k2-instruct", // EOL 2026-05-12
  "meta/llama-3.1-8b-instruct", // EOL 2026-08-26
  "meta-llama/llama-3.1-8b-instruct", // EOL 2026-08-26 (openrouter form)
  "meta/llama-3.3-70b-instruct", // EOL 2026-08-26
  "meta-llama/llama-3.3-70b-instruct", // EOL 2026-08-26 (openrouter form)
  "meta-llama/llama-3.3-70b-instruct:free", // EOL 2026-08-26 (:free form)
  // OpenRouter-delisted (2026-09-21).
  "tencent/hy3:free",
  "poolside/laguna-m.1:free",
  "nvidia/nemotron-3-nano-30b-a3b:free",
  "qwen/qwen3-coder:free",
  "nousresearch/hermes-3-llama-3.1-405b:free",
  "openai/gpt-oss-20b:free",
  // Groq 404-verified (2026-09-30).
  "llama-3.3-70b-versatile",
  "qwen/qwen3-32b",
  "qwen/qwen3.6-27b",
  "meta-llama/llama-4-scout-17b-16e-instruct",
];
