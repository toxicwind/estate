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

export const UA = "Mozilla/5.0 (compatible; SovereignASTMatrix/3.1)";

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
  nvidia: {
    base: "http://127.0.0.1:8000/v1",
    key_env: "NIM_PROXY_API_KEY",
    key_env_alt: "NVIDIA_API_KEY",
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
  for (const [p, models] of Object.entries(PROVIDER_MODELS)) {
    if (models.includes(model)) return [p, model];
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
  console.error("[matrix]", ...args);
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
