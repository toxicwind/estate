// Provider defaults.
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export const NIM_BASE_URL = "https://integrate.api.nvidia.com/v1";

/** Primary env var name for the NVIDIA NIM API key. */
export const NIM_NIM_API_KEY_ENV = "NVIDIA_NIM_API_KEY";

/** Fallback env var name for backward compatibility. */
export const NIM_API_KEY_ENV = "NVIDIA_API_KEY";

/** Pi agent-dir override (same name as tau). */
export const PI_CODING_AGENT_DIR_ENV = "PI_CODING_AGENT_DIR";

/** `/login nvidia-nim` first, then built-in `/login nvidia` (same NVIDIA key). */
export const NIM_AUTH_JSON_PROVIDERS = ["nvidia-nim", "nvidia"] as const;

export type NimAuthJsonProvider = (typeof NIM_AUTH_JSON_PROVIDERS)[number];

/**
 * Resolves the primary API key env var name.
 * Prefers a non-empty `NVIDIA_NIM_API_KEY`; empty string does not beat the fallback.
 */
export function getPrimaryNimApiKeyEnv(
  env: NodeJS.ProcessEnv = process.env,
): string {
  const primary = env.NVIDIA_NIM_API_KEY;
  if (typeof primary === "string" && primary.trim() !== "") {
    return NIM_NIM_API_KEY_ENV;
  }
  return NIM_API_KEY_ENV;
}

/** Literal key from env, resolved at call time (not import time). */
export function resolveNimApiKeyFromEnv(
  env: NodeJS.ProcessEnv = process.env,
): string | undefined {
  return resolveNimApiKeyFromEnvDetailed(env)?.key;
}

/** Same as `resolveNimApiKeyFromEnv` plus which variable won. */
export function resolveNimApiKeyFromEnvDetailed(
  env: NodeJS.ProcessEnv = process.env,
): { key: string; envName: string } | undefined {
  const primary = env.NVIDIA_NIM_API_KEY?.trim();
  if (primary) return { key: primary, envName: NIM_NIM_API_KEY_ENV };
  const fallback = env.NVIDIA_API_KEY?.trim();
  if (fallback) return { key: fallback, envName: NIM_API_KEY_ENV };
  return undefined;
}

export function expandNimHomePath(path: string, home: string = homedir()): string {
  if (path === "~") return home;
  if (path.startsWith("~/") || path.startsWith("~\\")) {
    return join(home, path.slice(2));
  }
  return path;
}

/** Default Pi auth.json: `~/.pi/agent/auth.json` or `$PI_CODING_AGENT_DIR/auth.json`. */
export function getDefaultNimAuthJsonPath(
  env: NodeJS.ProcessEnv = process.env,
  home: string = homedir(),
): string {
  const override = env[PI_CODING_AGENT_DIR_ENV]?.trim();
  if (override) {
    return join(expandNimHomePath(override, home), "auth.json");
  }
  return join(home, ".pi", "agent", "auth.json");
}

function credentialsMapFromAuthFile(parsed: unknown): Record<string, unknown> {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
  const obj = parsed as Record<string, unknown>;
  const nested = obj.providers;
  if (nested && typeof nested === "object" && !Array.isArray(nested)) {
    return nested as Record<string, unknown>;
  }
  return obj;
}

function literalKeyFromCredential(cred: unknown): string | undefined {
  if (!cred || typeof cred !== "object" || Array.isArray(cred)) return undefined;
  const c = cred as Record<string, unknown>;
  const type = c.type;
  if (typeof type === "string" && type !== "api_key" && type !== "api-key") {
    return undefined;
  }
  for (const field of ["key", "apiKey", "api_key"]) {
    const value = c[field];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return undefined;
}

function expandAuthJsonKeyRef(
  value: string,
  env: NodeJS.ProcessEnv,
): string | undefined {
  if (/^\$[A-Za-z_][A-Za-z0-9_]*$/.test(value)) {
    const resolved = env[value.slice(1)]?.trim();
    return resolved || undefined;
  }
  return value;
}

export function readNimApiKeyFromAuthJson(
  authPath: string,
  env: NodeJS.ProcessEnv = process.env,
): { key: string; provider: NimAuthJsonProvider } | undefined {
  try {
    if (!existsSync(authPath)) return undefined;
    const parsed: unknown = JSON.parse(readFileSync(authPath, "utf8"));
    const creds = credentialsMapFromAuthFile(parsed);
    for (const provider of NIM_AUTH_JSON_PROVIDERS) {
      const raw = literalKeyFromCredential(creds[provider]);
      if (!raw) continue;
      const key = expandAuthJsonKeyRef(raw, env);
      if (key) return { key, provider };
    }
    return undefined;
  } catch {
    return undefined;
  }
}

export type NimCatalogKeyResolution =
  | { key: string; source: "environment"; envName: string }
  | { key: string; source: "auth.json"; provider: NimAuthJsonProvider }
  | { key?: undefined; source: "none" };

/**
 * Catalog fetch credential: env (same rules as request-time resolve), then
 * `auth.json` `nvidia-nim` (`/login nvidia-nim`), then `nvidia`.
 */
export function resolveNimCatalogApiKey(opts?: {
  env?: NodeJS.ProcessEnv;
  authPath?: string;
  home?: string;
}): NimCatalogKeyResolution {
  const env = opts?.env ?? process.env;
  const fromEnv = resolveNimApiKeyFromEnvDetailed(env);
  if (fromEnv) {
    return { key: fromEnv.key, source: "environment", envName: fromEnv.envName };
  }
  const authPath = opts?.authPath ?? getDefaultNimAuthJsonPath(env, opts?.home);
  const stored = readNimApiKeyFromAuthJson(authPath, env);
  if (stored) {
    return { key: stored.key, source: "auth.json", provider: stored.provider };
  }
  return { source: "none" };
}

export function describeNimCatalogKeySource(
  resolution: NimCatalogKeyResolution,
): string {
  if (resolution.source === "environment") {
    return `environment (${resolution.envName})`;
  }
  if (resolution.source === "auth.json") {
    return `auth.json ${resolution.provider}`;
  }
  return "none — set NVIDIA_NIM_API_KEY / NVIDIA_API_KEY or /login nvidia-nim";
}

/**
 * Pi interpolates `$ENV_VAR` at request time. Call this at register time so an
 * empty `NVIDIA_NIM_API_KEY` does not lock the provider onto a blank env var.
 */
export function getNimApiKeyRef(env: NodeJS.ProcessEnv = process.env): string {
  return `$${getPrimaryNimApiKeyEnv(env)}`;
}

export type NimLoginInteraction = {
  prompt: (opts: { type: string; message: string }) => Promise<string>;
};

/** `/login nvidia-nim` — stores the key under this provider in auth.json. */
export async function nvidiaNimApiKeyLogin(
  interaction: NimLoginInteraction,
): Promise<{ type: "api_key"; key: string }> {
  const key = await interaction.prompt({
    type: "secret",
    message: "NVIDIA NIM API key (nvapi-...)",
  });
  const trimmed = key?.trim();
  if (!trimmed) throw new Error("NVIDIA NIM login cancelled");
  return { type: "api_key", key: trimmed };
}

/** Request-time credential: env wins, then `/login` stored key. */
export async function resolveNimProviderAuth(input?: {
  credential?: { key?: string };
}): Promise<{ auth: { apiKey: string }; source: string } | undefined> {
  const envKey = resolveNimApiKeyFromEnv();
  if (envKey) return { auth: { apiKey: envKey }, source: "environment" };
  if (input?.credential?.key) {
    return { auth: { apiKey: input.credential.key }, source: "stored API key" };
  }
  return undefined;
}

/**
 * pi resolves `$ENV_VAR` at request time. `NVIDIA_API_KEY` is also the key used
 * by pi's built-in `nvidia` provider and `/login` (stored in ~/.pi/agent/auth.json
 * under `"nvidia"`). Prefer `NVIDIA_NIM_API_KEY` when set; otherwise fall back.
 *
 * Prefer `getNimApiKeyRef()` at register time — this snapshot is import-time only.
 */
export const NIM_API_KEY_REF = `$${getPrimaryNimApiKeyEnv()}`;
