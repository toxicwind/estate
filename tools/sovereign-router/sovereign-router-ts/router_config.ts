import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";

// ---------------------------------------------------------------------------
// Secrets + local stack env (mise loads these; standalone bun needs them too)
// ---------------------------------------------------------------------------
export function loadEnvFile(path: string): void {
  if (!existsSync(path)) return;
  try {
    for (let line of readFileSync(path, "utf8").split("\n")) {
      line = line.trim();
      if (!line || line.startsWith("#")) continue;
      if (line.startsWith("export ")) line = line.slice(7);
      const eq = line.indexOf("=");
      if (eq < 1) continue;
      const k = line.slice(0, eq).trim();
      let v = line
        .slice(eq + 1)
        .trim()
        .replace(/^['"]|['"]$/g, "");
      if (k && v && !process.env[k]) process.env[k] = v;
    }
  } catch (e) {
    console.error(`[matrix] loadEnvFile ${path}:`, e);
  }
}

loadEnvFile(`${homedir()}/.secrets`);

loadEnvFile("/home/toxic/.secrets");

loadEnvFile("/home/toxic/sovereign/config/ports.env");

loadEnvFile("/home/toxic/sovereign/.env.local");

// Port SSOT: process-compose injects SOVEREIGN_PORT=${SOVEREIGN_ROUTER_PORT}
export const _portRaw =
  process.env.SOVEREIGN_PORT || process.env.SOVEREIGN_ROUTER_PORT || "";

if (!_portRaw) {
  throw new Error(
    "SOVEREIGN_ROUTER_PORT or SOVEREIGN_PORT required (config/ports.env)",
  );
}

export const PORT = parseInt(_portRaw, 10);

export const DB_PATH =
  process.env.SOVEREIGN_DB || "/home/toxic/sovereign/data/sovereign_router.db";

export const MAX_PARALLEL = 4;

export const STICKY_TTL = 1800;

export const FIFO_MAX = 64;

export const STRATEGY = process.env.SOVEREIGN_STRATEGY || "hybrid";

export const UA = "Mozilla/5.0 (compatible; Sovereign-Router/3.1)";

// ---------------------------------------------------------------------------
// LLAMA_SWAP_V1 (must come before PROVIDERS that uses it)
// ---------------------------------------------------------------------------
export const LLAMA_SWAP_V1 =
  process.env.LLM_BASE_URL ||
  process.env.LLAMA_SWAP_V1 ||
  "http://127.0.0.1:25100/v1";

export function loadLocalRoleModels(): {
  fast: string;
  quality: string;
  longctx: string;
} {
  const defaults = {
    fast: "beellama/exaone-4-0-1-2b-iq4xs",
    quality: "beellama/qwen-flash-64k",
    longctx: "beellama/qwen-flash-256k",
  };
  try {
    const p = "/home/toxic/sovereign/.state/best-models.json";
    if (!existsSync(p)) return defaults;
    const j = JSON.parse(readFileSync(p, "utf8"));
    return {
      fast: j?.roles?.fast?.id || j?.recommended?.preload || defaults.fast,
      quality:
        j?.roles?.quality?.id ||
        j?.recommended?.default_chat ||
        defaults.quality,
      longctx:
        j?.roles?.longctx?.id ||
        j?.recommended?.long_context ||
        defaults.longctx,
    };
  } catch {
    return defaults;
  }
}

export const LOCAL_ROLES = loadLocalRoleModels();

// ---------------------------------------------------------------------------
// Providers (must come before Catalog that depends on LOCAL_ROLES)
// ---------------------------------------------------------------------------
export const PROVIDERS: Record<
  string,
  { base: string; key_env: string; key_env_alt?: string; no_auth?: boolean }
> = {
  // Local SSOT — always first-class for sovereign GPU path
  "llama-swap": {
    base: LLAMA_SWAP_V1,
    key_env: "LLAMA_SWAP_API_KEY",
    no_auth: true,
  },
  openrouter: {
    base: "https://openrouter.ai/api/v1",
    key_env: "OPENROUTER_API_KEY",
  },
  // NVIDIA direct (the :8000 key-proxy is retired — multi-key rotation and
  // per-key rate limiting now live in the router itself, see router_matrix).
  nvidia: {
    base: "https://integrate.api.nvidia.com/v1",
    key_env: "NVIDIA_API_KEY",
    key_env_alt: "NVIDIA_API_KEYS",
  },
  groq: { base: "https://api.groq.com/openai/v1", key_env: "GROQ_API_KEY" },
  cerebras: {
    base: "https://api.cerebras.ai/v1",
    key_env: "CEREBRAS_API_KEY",
  },
  google: {
    base: "https://generativelanguage.googleapis.com/v1beta/openai",
    key_env: "GOOGLE_API_KEY",
  },
  mistral: { base: "https://api.mistral.ai/v1", key_env: "MISTRAL_API_KEY" },
};

// ---------------------------------------------------------------------------
// Catalog (depends on LOCAL_ROLES, must come after loadLocalRoleModels)
// ---------------------------------------------------------------------------
export const PROVIDER_MODELS: Record<string, string[]> = {
  "llama-swap": [LOCAL_ROLES.fast, LOCAL_ROLES.quality, LOCAL_ROLES.longctx],
  openrouter: [
    "tencent/hy3:free",
    "poolside/laguna-m.1:free",
    "poolside/laguna-xs-2.1:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "openai/gpt-oss-20b:free",
    "inclusionai/ling-3.0-flash-fin:free",
  ],
  nvidia: [
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/nemotron-3-nano-30b-a3b",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.3-70b-instruct",
    "qwen/qwen3.5-397b-a17b",
    "qwen/qwen3.5-122b-a10b",
    "deepseek-ai/deepseek-v4-flash",
    "deepseek-ai/deepseek-v4-pro",
    "mistralai/mistral-large-3-675b-instruct-2512",
    "google/gemma-4-31b-it",
    "z-ai/glm-5.2",
    "thinkingmachines/inkling",
  ],
  groq: [
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
  ],
  cerebras: [],
  google: [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.0-flash",
    "models/gemma-4-31b-it",
  ],
  mistral: [
    "mistral-small-latest",
    "codestral-latest",
    "mistral-large-latest",
    "mistral-medium-latest",
  ],
};

// ---------------------------------------------------------------------------
// Live per-model metadata (populated at runtime by router_live_models.ts):
// provider -> model id -> raw provider /models object (pricing, context
// length, architecture...). IDs stay in LIVE_MODELS for routing; metadata
// enriches /v1/models so clients see live data, not just id strings.
export const LIVE_MODEL_META: Record<string, Record<string, unknown>> = {};

// NVIDIA multi-key pool (absorbed from the retired :8000 key-proxy):
// comma-separated nvapi-* keys, each with its own 40rpm token bucket
// (see Matrix.nextNvidiaKey in router_matrix.ts).
export function nvidiaKeys(): string[] {
  const pool = (process.env.NVIDIA_API_KEYS || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  if (pool.length) return pool;
  const single = process.env.NVIDIA_API_KEY || "";
  return single ? [single] : [];
}

// ---------------------------------------------------------------------------
// Live model catalog (populated at runtime by router_live_models.ts)
// ---------------------------------------------------------------------------
// Curated PROVIDER_MODELS above is the stable base (aliases, :free suffix
// conventions). LIVE_MODELS is filled from each provider's GET /models
// endpoint using that provider's own API key, so the router serves every
// model each key is entitled to - not just the hardcoded subset.
// catalogModelsFor() = curated union live, curated first.
export const LIVE_MODELS: Record<string, string[]> = {};

export function catalogModelsFor(p: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const m of [...(PROVIDER_MODELS[p] || []), ...(LIVE_MODELS[p] || [])]) {
    if (typeof m === "string" && m && !seen.has(m)) {
      seen.add(m);
      out.push(m);
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Live-metadata free eligibility (Chris 2026-09-17: routing must consume the
// live /models metadata, not a divergent static list).
//
// modelFree(p, mid) is the single source of truth for "this model costs us
// nothing on this key":
//   1. Live metadata wins: OpenRouter-style /models carries pricing; prompt +
//      completion priced "0" means zero-cost on our key. A provider-set
//      boolean "free" flag in the live object is honored too.
//   2. Deterministic fallback: providers whose /models carry no pricing
//      metadata (nvidia/groq/google/mistral) keep the ":free" suffix
//      convention, exactly as before. Curated ":free" ids with no live
//      metadata entry at all (delisted, fetch failure) also keep the suffix
//      rule, so the pool never silently empties on a bad refresh.
export function modelFree(p: string, mid: string): boolean {
  const meta = (LIVE_MODEL_META[p] || {})[mid] as
    | Record<string, unknown>
    | undefined;
  const pricing = meta?.["pricing"] as Record<string, unknown> | undefined;
  if (pricing && typeof pricing === "object") {
    const zero = (v: unknown) => v === "0" || v === 0;
    return zero(pricing["prompt"]) && zero(pricing["completion"]);
  }
  if (typeof meta?.["free"] === "boolean") return meta["free"] as boolean;
  return mid.includes(":free");
}

export const CODING: Record<string, [string, string] | null> = {
  auto: null,
  fcm: null,
  // free: route through the `free` strategy (local + all :free cloud models)
  free: null,
  // Local-first ranked roles (llama-swap exclusive matrix)
  fast: ["llama-swap", LOCAL_ROLES.fast],
  "local-fast": ["llama-swap", LOCAL_ROLES.fast],
  quality: ["llama-swap", LOCAL_ROLES.quality],
  "local-quality": ["llama-swap", LOCAL_ROLES.quality],
  longctx: ["llama-swap", LOCAL_ROLES.longctx],
  "local-longctx": ["llama-swap", LOCAL_ROLES.longctx],
  "local-auto": ["llama-swap", LOCAL_ROLES.quality],
  hy3: ["openrouter", "tencent/hy3:free"],
  "laguna-m1": ["openrouter", "poolside/laguna-m.1:free"],
  "laguna-xs": ["openrouter", "poolside/laguna-xs-2.1:free"],
  "gemma4-31b": ["openrouter", "google/gemma-4-31b-it:free"],
  "nemotron-super": ["openrouter", "nvidia/nemotron-3-super-120b-a12b:free"],
  "nemotron-nano": ["openrouter", "nvidia/nemotron-3-nano-30b-a3b:free"],
  "qwen3-coder": ["openrouter", "qwen/qwen3-coder:free"],
  "llama-3.3-70b-free": [
    "openrouter",
    "meta-llama/llama-3.3-70b-instruct:free",
  ],
  "hermes-3-405b": ["openrouter", "nousresearch/hermes-3-llama-3.1-405b:free"],
  "gpt-oss-20b": ["openrouter", "openai/gpt-oss-20b:free"],
  "nim-nemotron-super": ["nvidia", "nvidia/nemotron-3-super-120b-a12b"],
  "nim-nemotron-nano": ["nvidia", "nvidia/nemotron-3-nano-30b-a3b"],
  "nim-llama-3.1-70b": ["nvidia", "meta/llama-3.1-70b-instruct"],
  "nim-llama-3.3-70b": ["nvidia", "meta/llama-3.3-70b-instruct"],
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

export const AST_RE =
  /(def |class |import |from |function |const |let |var |#include|package |fn |pub |struct |impl |async |await |\.ts|\.py|\.rs|\.js|AST|tree-sitter|syntax|```)/i;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
export function getKey(p: string): string {
  // NVIDIA serves from the multi-key pool; first key is the default.
  if (p === "nvidia") return nvidiaKeys()[0] || "";
  const conf = PROVIDERS[p];
  if (!conf) return "";
  if (conf.no_auth) return "not-required-for-local";
  return (
    process.env[conf.key_env] ||
    (conf.key_env_alt ? process.env[conf.key_env_alt] : "") ||
    ""
  );
}

export function keyOk(p: string): boolean {
  if (p === "llama-swap" || PROVIDERS[p]?.no_auth) return true;
  if (p === "nvidia") return nvidiaKeys().length > 0;
  const conf = PROVIDERS[p];
  if (!conf) return false;
  return Boolean(
    process.env[conf.key_env] ||
    (conf.key_env_alt ? process.env[conf.key_env_alt] : ""),
  );
}

export function firstModelFor(p: string): string {
  if (p === "llama-swap") return LOCAL_ROLES.quality;
  return PROVIDER_MODELS[p]?.[0] || "";
}

export function isLocalSwapModelId(model: string): boolean {
  if (!model || model === "auto" || model === "fcm") return false;
  if (model in CODING && CODING[model]?.[0] === "llama-swap") return true;
  if (
    model === LOCAL_ROLES.fast ||
    model === LOCAL_ROLES.quality ||
    model === LOCAL_ROLES.longctx
  ) {
    return true;
  }
  // sovereign naming prefixes / known local ids
  return /^(beellama|mradermacher|jackrong|turboquant|ik_llama|ik_turboquant|holo|qwen\/|gemma-4|exaone)/i.test(
    model,
  );
}

export function resolveModel(model: string): [string, string] {
  if (model in CODING && CODING[model] != null) return CODING[model]!;
  // Prefer llama-swap for any local GGUF id so hybrid never sends GPU models to Gemini
  if (isLocalSwapModelId(model)) return ["llama-swap", model];
  if (model === "auto" || model === "fcm") {
    // local-first auto: quality role on swap
    return ["llama-swap", LOCAL_ROLES.quality];
  }
  for (const p of Object.keys(PROVIDERS)) {
    if (catalogModelsFor(p).includes(model)) return [p, model];
  }
  if (keyOk("openrouter")) return ["openrouter", model];
  if (keyOk("nvidia")) return ["nvidia", model];
  return ["llama-swap", LOCAL_ROLES.quality];
}

export function isAst(text: string): boolean {
  return Boolean(
    text && (AST_RE.test(text.slice(0, 5000)) || text.includes("```")),
  );
}

export function isExplicit(model: string): boolean {
  return (
    (model in CODING && CODING[model] != null) || isLocalSwapModelId(model)
  );
}

export function log(...args: unknown[]) {
  console.error("[router]", ...args);
}

export function json(
  data: unknown,
  status = 200,
  headers: Record<string, string> = {},
) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}
