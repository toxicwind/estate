import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import {
  describeNimCatalogKeySource,
  resolveNimCatalogApiKey,
  type NimCatalogKeyResolution,
} from "../config/defaults.ts";

export const NIM_CACHE_PATH = join(homedir(), ".pi", "nvidia-nim-cache.json");
export const NIM_BASE_URL = "https://integrate.api.nvidia.com/v1";
export const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

export interface NimCacheFile {
  fetchedAt: string;
  models: Array<{ id: string; owned_by?: string }>;
}

export type NimFetchFn = (
  url: string,
  init?: { headers?: Record<string, string>; signal?: AbortSignal },
) => Promise<{ ok: boolean; status: number; json: () => Promise<unknown> }>;

export interface NimCacheOptions {
  cachePath?: string;
  authPath?: string;
  env?: NodeJS.ProcessEnv;
  home?: string;
  fetchFn?: NimFetchFn;
  now?: number;
}

export interface LastCatalogRefresh {
  ok: boolean;
  fetched: boolean;
  skippedFreshCache: boolean;
  error?: string;
  keySource: string;
  liveCount: number;
}

const MISSING_KEY_ERROR =
  "NVIDIA API key required (NVIDIA_NIM_API_KEY, NVIDIA_API_KEY, or /login nvidia-nim in ~/.pi/agent/auth.json)";

let lastCatalogRefresh: LastCatalogRefresh = {
  ok: false,
  fetched: false,
  skippedFreshCache: false,
  keySource: describeNimCatalogKeySource({ source: "none" }),
  liveCount: 0,
};

export function getLastCatalogRefresh(): LastCatalogRefresh {
  return { ...lastCatalogRefresh };
}

export function resetLastCatalogRefresh(): void {
  lastCatalogRefresh = {
    ok: false,
    fetched: false,
    skippedFreshCache: false,
    keySource: describeNimCatalogKeySource({ source: "none" }),
    liveCount: 0,
  };
}

export function readCache(cachePath = NIM_CACHE_PATH): NimCacheFile | null {
  try {
    if (!existsSync(cachePath)) return null;
    return JSON.parse(readFileSync(cachePath, "utf8")) as NimCacheFile;
  } catch {
    return null;
  }
}

export function writeCache(data: NimCacheFile, cachePath = NIM_CACHE_PATH): void {
  const dir = dirname(cachePath);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  writeFileSync(cachePath, JSON.stringify(data, null, 2), "utf8");
}

export function isCacheFresh(cache: NimCacheFile | null, now = Date.now()): boolean {
  if (!cache?.fetchedAt) return false;
  const age = now - Date.parse(cache.fetchedAt);
  return Number.isFinite(age) && age >= 0 && age < CACHE_TTL_MS;
}

export async function fetchNimModelIds(
  apiKey?: string,
  options?: NimCacheOptions,
): Promise<string[]> {
  const explicit = apiKey?.trim();
  const key = explicit || resolveNimCatalogApiKey(options).key;
  if (!key) {
    throw new Error(MISSING_KEY_ERROR);
  }
  const fetchFn = options?.fetchFn ?? globalThis.fetch;
  const res = await fetchFn(`${NIM_BASE_URL}/models`, {
    headers: { Authorization: `Bearer ${key}` },
    signal: AbortSignal.timeout(15_000),
  });
  if (!res.ok) {
    const hint =
      res.status === 401 || res.status === 403
        ? " — key rejected; check /login nvidia-nim or NVIDIA_* env"
        : "";
    throw new Error(`NIM /models returned HTTP ${res.status}${hint}`);
  }
  const body = (await res.json()) as { data?: Array<{ id: string }> };
  return (body.data ?? []).map((m) => m.id).filter(Boolean);
}

export async function refreshCacheIfStale(
  force = false,
  options?: NimCacheOptions,
): Promise<NimCacheFile | null> {
  const cachePath = options?.cachePath ?? NIM_CACHE_PATH;
  const existing = readCache(cachePath);
  const resolution = resolveNimCatalogApiKey(options);
  const keySource = describeNimCatalogKeySource(resolution);

  if (!force && isCacheFresh(existing, options?.now)) {
    lastCatalogRefresh = {
      ok: true,
      fetched: false,
      skippedFreshCache: true,
      keySource,
      liveCount: existing?.models.length ?? 0,
    };
    return existing;
  }

  if (!resolution.key) {
    lastCatalogRefresh = {
      ok: false,
      fetched: false,
      skippedFreshCache: false,
      error: MISSING_KEY_ERROR,
      keySource,
      liveCount: existing?.models.length ?? 0,
    };
    return existing;
  }

  try {
    const ids = await fetchNimModelIds(resolution.key, options);
    const next: NimCacheFile = {
      fetchedAt: new Date(options?.now ?? Date.now()).toISOString(),
      models: ids.map((id) => ({ id })),
    };
    writeCache(next, cachePath);
    lastCatalogRefresh = {
      ok: true,
      fetched: true,
      skippedFreshCache: false,
      keySource,
      liveCount: next.models.length,
    };
    return next;
  } catch (err) {
    lastCatalogRefresh = {
      ok: false,
      fetched: false,
      skippedFreshCache: false,
      error: err instanceof Error ? err.message : String(err),
      keySource,
      liveCount: existing?.models.length ?? 0,
    };
    return existing;
  }
}

export function formatNimModelsHeader(input: {
  registeredCount: number;
  curatedCount: number;
  liveStubCount: number;
  apiListedCount: number | null;
  cacheFetchedAt?: string | null;
  keySource: string;
  lastFetchError?: string | null;
}): string[] {
  const cached = input.apiListedCount != null;
  const apiListed = cached ? input.apiListedCount : 0;
  const cacheNote = !cached
    ? "not cached — run /nim-refresh"
    : input.cacheFetchedAt
      ? `cached ${input.cacheFetchedAt}`
      : "cached";
  const usingLoginKey = /\bauth\.json\b/i.test(input.keySource);

  const lines = [
    `Registered: ${input.registeredCount} chat models (${input.curatedCount} curated, ${input.liveStubCount} live)`,
    `Live API listed: ${apiListed} (${cacheNote})`,
    `Using login key? ${usingLoginKey ? "yes" : "no"} (${input.keySource})`,
  ];
  if (input.lastFetchError) {
    lines.push(`Last catalog fetch: failed — ${input.lastFetchError}`);
  }
  if (apiListed === 0) {
    lines.push(
      "Live [live] stubs only appear after a successful GET /v1/models.",
      "If you only see curated models: /login is not enough on npm @diegovisk/pi-nvidia-nim@1.1.0 — install THIS repo path, /reload, then /nim-refresh.",
      "/model must show nvidia-nim/... (built-in nvidia is a different, smaller catalog).",
    );
  }
  return lines;
}

/** Resolve key source for UI without exposing the secret. */
export function currentCatalogKeySource(options?: NimCacheOptions): string {
  return describeNimCatalogKeySource(resolveNimCatalogApiKey(options));
}

export type { NimCatalogKeyResolution };
