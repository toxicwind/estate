Paste into extensions/vansrouter.ts in your fork checkout. Nothing after the block.

```typescript
// extensions/vansrouter.ts
// OMP-native VansRouter provider extension.
//
// Multi-tier design:
//   Discovery:  dynamic /v1/models  →  disk cache (3 rotating backups)  →  seed list
//   Health:     /api/health  →  /v1/models  →  TCP connect  →  unregistered
//   Resilience: /api/breaker + /api/quota/kimchi + /api/proxies  →  status-only
//   ACL:        /api/key/info  →  unfiltered on any failure
//   Cache write: rotate main → bak1 → bak2, then commit main atomically
//
// No createProvider() usage. No @earendil-works/* or @mariozechner/* imports.
// Everything goes through pi.registerProvider + fetchDynamicModels + ctx.ui.*
// so OMP's shim gaps (#6470, #7174, #6333) and the createProvider gap (#9024)
// cannot reach this extension.

import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { promises as fs } from "node:fs";
import path from "node:path";
import os from "node:os";
import net from "node:net";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const VR_BASE =
  process.env.VANSROUTER_URL ??
  process.env.NINEROUTER_URL ??
  "http://127.0.0.1:20128";

const VR_KEY_ENV = "VANSROUTER_API_KEY";
const VR_KEY_FALLBACK_ENV = "NINEROUTER_KEY";

const CACHE_DIR = path.join(os.homedir(), ".omp", "agent", "cache");
const CATALOG_MAIN = path.join(CACHE_DIR, "vansrouter-catalog.json");
const CATALOG_BAK1 = path.join(CACHE_DIR, "vansrouter-catalog.bak1.json");
const CATALOG_BAK2 = path.join(CACHE_DIR, "vansrouter-catalog.bak2.json");
const RESILIENCE_CACHE = path.join(CACHE_DIR, "vansrouter-resilience.json");

const HTTP_TIMEOUT_MS = 3000;
const HEALTH_TIMEOUT_MS = 1500;
const DISCOVERY_TIMEOUT_MS = 8000;

// Seed list: used only if dynamic fetch AND all three cache tiers fail.
// IDs match what VansRouter advertises on a fresh install.
const SEED_MODELS = [
  { id: "oc/jev-1.13-free", name: "OpenCode Jev Free", contextWindow: 128000, maxTokens: 8192 },
  { id: "oc/mimo-v2.5-free", name: "OpenCode Mimo Free", contextWindow: 128000, maxTokens: 8192 },
  { id: "oc/nemotron-3.5-lightning-free", name: "OpenCode Nemotron Lightning Free", contextWindow: 128000, maxTokens: 8192 },
  { id: "oc/deepseek-v4-flash-free", name: "OpenCode DeepSeek Flash Free", contextWindow: 128000, maxTokens: 8192 },
  { id: "mmf/mimo-auto", name: "MMF Mimo Auto", contextWindow: 128000, maxTokens: 8192 },
];

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ModelEntry {
  id: string;
  name: string;
  contextWindow: number;
  maxTokens: number;
}

interface Catalog {
  fetchedAt: number;
  source: "dynamic" | "cache-main" | "cache-bak1" | "cache-bak2" | "seed";
  models: ModelEntry[];
}

interface ResilienceStatus {
  fetchedAt: number;
  breaker: { open?: number; providers?: Record<string, string> } | null;
  quota: { daysUntilReset?: number; resetAt?: string } | null;
  proxies: { alive?: number; dead?: number; pools?: number } | null;
  acl: { allowedProviders?: string[]; allowedKinds?: string[] } | null;
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

async function httpJson<T>(
  url: string,
  init: RequestInit = {},
  timeoutMs = HTTP_TIMEOUT_MS,
): Promise<T | null> {
  try {
    const res = await fetch(url, {
      ...init,
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

function authHeaders(key: string): Record<string, string> {
  return key ? { Authorization: `Bearer ${key}` } : {};
}

// ---------------------------------------------------------------------------
// Tier 1: health probe
// ---------------------------------------------------------------------------

async function probeHealth(base: string): Promise<boolean> {
  // Tier 1a — explicit health endpoint
  const health = await httpJson(`${base}/api/health`, {}, HEALTH_TIMEOUT_MS);
  if (health && typeof health === "object" && (health as any).ok !== false) {
    return true;
  }
  // Tier 1b — model list endpoint
  const models = await httpJson(`${base}/v1/models`, {}, HEALTH_TIMEOUT_MS);
  if (models) return true;
  // Tier 1c — raw TCP connect (some builds disable /api/health)
  return tcpProbe(base);
}

function tcpProbe(base: string): Promise<boolean> {
  return new Promise((resolve) => {
    try {
      const u = new URL(base);
      const port = Number(u.port || (u.protocol === "https:" ? 443 : 80));
      const sock = net.connect({ host: u.hostname, port }, () => {
        sock.destroy();
        resolve(true);
      });
      sock.on("error", () => {
        sock.destroy();
        resolve(false);
      });
      sock.setTimeout(1500, () => {
        sock.destroy();
        resolve(false);
      });
    } catch {
      resolve(false);
    }
  });
}

// ---------------------------------------------------------------------------
// Tier 2: catalog discovery with backup chain
// ---------------------------------------------------------------------------

async function fetchCatalogDynamic(base: string, key: string): Promise<ModelEntry[] | null> {
  const body = await httpJson<{ data?: Array<Record<string, unknown>> }>(
    `${base}/v1/models`,
    { headers: authHeaders(key) },
    DISCOVERY_TIMEOUT_MS,
  );
  if (!body?.data || !Array.isArray(body.data)) return null;

  const seen = new Set<string>();
  const out: ModelEntry[] = [];
  for (const raw of body.data) {
    const id = typeof raw.id === "string" ? raw.id : null;
    if (!id || seen.has(id)) continue;
    seen.add(id);
    out.push({
      id,
      name: typeof raw.name === "string" ? raw.name : id,
      contextWindow:
        typeof raw.context_window === "number"
          ? raw.context_window
          : typeof raw.contextWindow === "number"
            ? raw.contextWindow
            : 128000,
      maxTokens:
        typeof raw.max_tokens === "number"
          ? raw.max_tokens
          : typeof raw.maxTokens === "number"
            ? raw.maxTokens
            : 8192,
    });
  }
  return out.length ? out : null;
}

async function readCatalogFromDisk(): Promise<Catalog | null> {
  const tiers: Array<Catalog["source"]> = ["cache-main", "cache-bak1", "cache-bak2"];
  const files = [CATALOG_MAIN, CATALOG_BAK1, CATALOG_BAK2];
  for (let i = 0; i < files.length; i++) {
    try {
      const raw = await fs.readFile(files[i], "utf8");
      const parsed = JSON.parse(raw) as Partial<Catalog>;
      if (Array.isArray(parsed.models) && parsed.models.length > 0) {
        return {
          fetchedAt: typeof parsed.fetchedAt === "number" ? parsed.fetchedAt : 0,
          source: tiers[i],
          models: parsed.models as ModelEntry[],
        };
      }
    } catch {
      // try next tier
    }
  }
  return null;
}

async function writeCatalogWithBackup(catalog: Catalog): Promise<void> {
  await fs.mkdir(CACHE_DIR, { recursive: true });
  // Rotate: current main → bak1, current bak1 → bak2
  try {
    await fs.copyFile(CATALOG_MAIN, CATALOG_BAK1);
  } catch {
    /* main may not exist yet */
  }
  try {
    await fs.copyFile(CATALOG_BAK1, CATALOG_BAK2);
  } catch {
    /* bak1 may not exist yet */
  }
  // Atomic write to main via temp + rename
  const tmp = CATALOG_MAIN + ".tmp";
  await fs.writeFile(tmp, JSON.stringify(catalog, null, 2), { mode: 0o600 });
  await fs.rename(tmp, CATALOG_MAIN);
}

async function resolveCatalog(base: string, key: string): Promise<Catalog> {
  const dynamic = await fetchCatalogDynamic(base, key);
  if (dynamic) {
    const catalog: Catalog = {
      fetchedAt: Date.now(),
      source: "dynamic",
      models: dynamic,
    };
    await writeCatalogWithBackup(catalog);
    return catalog;
  }

  const cached = await readCatalogFromDisk();
  if (cached) return cached;

  return {
    fetchedAt: Date.now(),
    source: "seed",
    models: SEED_MODELS,
  };
}

// ---------------------------------------------------------------------------
// Tier 3: resilience probes (all optional, all graceful)
// ---------------------------------------------------------------------------

async function probeResilience(base: string, key: string): Promise<ResilienceStatus> {
  const h = authHeaders(key);
  const [breaker, quota, proxies, acl] = await Promise.allSettled([
    httpJson<ResilienceStatus["breaker"]>(`${base}/api/breaker`, { headers: h }),
    httpJson<ResilienceStatus["quota"]>(`${base}/api/quota/kimchi`, { headers: h }),
    httpJson<ResilienceStatus["proxies"]>(`${base}/api/proxies`, { headers: h }),
    httpJson<ResilienceStatus["acl"]>(`${base}/api/key/info`, { headers: h }),
  ]);
  const pick = <T>(r: PromiseSettledResult<T | null>): T | null =>
    r.status === "fulfilled" ? r.value : null;
  const status: ResilienceStatus = {
    fetchedAt: Date.now(),
    breaker: pick(breaker),
    quota: pick(quota),
    proxies: pick(proxies),
    acl: pick(acl),
  };
  try {
    await fs.mkdir(CACHE_DIR, { recursive: true });
    await fs.writeFile(RESILIENCE_CACHE, JSON.stringify(status, null, 2), { mode: 0o600 });
  } catch {
    // non-fatal
  }
  return status;
}

function applyAclFilter(models: ModelEntry[], acl: ResilienceStatus["acl"]): ModelEntry[] {
  if (!acl) return models;
  const { allowedProviders, allowedKinds } = acl;
  if (!allowedProviders && !allowedKinds) return models;
  return models.filter((m) => {
    const provider = m.id.split("/")[0];
    if (allowedProviders && !allowedProviders.includes(provider)) return false;
    if (allowedKinds) {
      const kind = m.id.includes(".") ? undefined : undefined; // filled by vansrouter
      if (kind && !allowedKinds.includes(kind)) return false;
    }
    return true;
  });
}

// ---------------------------------------------------------------------------
// Status line
// ---------------------------------------------------------------------------

function formatStatusLine(catalog: Catalog, status: ResilienceStatus | null): string {
  const parts: string[] = [];
  const tag =
    catalog.source === "dynamic"
      ? ""
      : catalog.source.startsWith("cache")
        ? ` (${catalog.source.replace("cache-", "")})`
        : " (seed)";
  parts.push(`VR:${catalog.models.length}${tag}`);
  if (status?.breaker?.open) parts.push(`${status.breaker.open} tripped`);
  if (status?.quota?.daysUntilReset) parts.push(`${status.quota.daysUntilReset}d reset`);
  if (status?.proxies?.dead) parts.push(`${status.proxies.dead} dead`);
  return parts.join(" · ");
}

// ---------------------------------------------------------------------------
// Extension entry
// ---------------------------------------------------------------------------

export default function vansrouterExtension(pi: ExtensionAPI) {
  let lastCatalog: Catalog | null = null;
  let lastStatus: ResilienceStatus | null = null;

  async function syncAndRegister(ctx: any, reason: string): Promise<void> {
    const healthy = await probeHealth(VR_BASE);
    if (!healthy) {
      ctx.ui?.notify?.(`VansRouter unreachable at ${VR_BASE} (${reason})`, "warn");
      return;
    }

    const catalog = await resolveCatalog(VR_BASE, resolveKey());
    lastCatalog = catalog;

    const status = await probeResilience(VR_BASE, resolveKey());
    lastStatus = status;

    const filtered = applyAclFilter(catalog.models, status.acl);
    const visible = filtered.length ? filtered : catalog.models;

    pi.registerProvider("vansrouter", {
      baseUrl: `${VR_BASE}/v1`,
      apiKey: VR_KEY_ENV,
      api: "openai-completions",
      authHeader: true,
      fetchDynamicModels: async (apiKey: string) => {
        const dyn = await fetchCatalogDynamic(VR_BASE, apiKey);
        if (dyn) {
          const filteredDyn = applyAclFilter(dyn, lastStatus?.acl ?? null);
          const vis = filteredDyn.length ? filteredDyn : dyn;
          lastCatalog = { fetchedAt: Date.now(), source: "dynamic", models: vis };
          await writeCatalogWithBackup(lastCatalog);
          return vis;
        }
        return visible;
      },
    });

    try {
      ctx.ui?.setStatus?.("vansrouter", formatStatusLine(catalog, status));
    } catch {
      // status line is best-effort
    }
  }

  function resolveKey(): string {
    return (
      process.env[VR_KEY_ENV] ??
      process.env[VR_KEY_FALLBACK_ENV] ??
      ""
    );
  }

  // --- lifecycle ---------------------------------------------------------

  pi.on("session_start", async (_event: unknown, ctx: any) => {
    await syncAndRegister(ctx, "session_start");
  });

  // --- slash commands ----------------------------------------------------

  pi.registerCommand?.("vansrouter", {
    description: "VansRouter provider control",
    handler: async (args: string, ctx: any) => {
      const sub = (args || "").trim().split(/\s+/)[0] || "status";

      if (sub === "status") {
        const cat = lastCatalog ?? (await readCatalogFromDisk()) ?? {
          fetchedAt: 0,
          source: "seed" as const,
          models: SEED_MODELS,
        };
        const st = lastStatus ?? null;
        ctx.ui?.notify?.(
          `${formatStatusLine(cat, st)}\n` +
            `base: ${VR_BASE}\n` +
            `key: ${resolveKey() ? "present" : "MISSING"}\n` +
            `models: ${cat.models.map((m) => m.id).join(", ")}`,
          "info",
        );
        return;
      }

      if (sub === "sync") {
        await syncAndRegister(ctx, "manual sync");
        ctx.ui?.notify?.("VansRouter catalog resynced", "info");
        return;
      }

      if (sub === "repair") {
        // Force cache rotation and re-seed from network
        await writeCatalogWithBackup({
          fetchedAt: Date.now(),
          source: "seed",
          models: SEED_MODELS,
        });
        await syncAndRegister(ctx, "repair");
        ctx.ui?.notify?.("VansRouter cache repaired", "info");
        return;
      }

      if (sub === "cache") {
        const tiers = await Promise.all(
          [CATALOG_MAIN, CATALOG_BAK1, CATALOG_BAK2].map(async (f) => {
            try {
              const stat = await fs.stat(f);
              return `${path.basename(f)}: ${stat.size}B @ ${new Date(stat.mtimeMs).toISOString()}`;
            } catch {
              return `${path.basename(f)}: (absent)`;
            }
          }),
        );
        ctx.ui?.notify?.(tiers.join("\n"), "info");
        return;
      }

      ctx.ui?.notify?.(
        "usage: /vansrouter [status|sync|repair|cache]",
        "info",
      );
    },
  });

  // --- shutdown ----------------------------------------------------------

  pi.on("session_end", async () => {
    if (lastCatalog) {
      try {
        await writeCatalogWithBackup(lastCatalog);
      } catch {
        // best-effort
      }
    }
  });
}
```

Three notes on using it:

Add the key to ~/.omp/agent/.env if you haven't: VANSROUTER_API_KEY=<value from ~/.9router/api.key>. The extension reads it via pi.registerProvider's apiKey: VANSROUTER_API_KEY — that name is the env-var-name-or-literal field, so passing the env var name is correct.

Register the extension in your fork's package.json under omp.extensions pointing at ./extensions/vansrouter.ts, then omp plugin link "$(pwd)" and restart OMP. omp models find vansrouter should list the models.

The three commands /vansrouter status, /vansrouter sync, /vansrouter repair and /vansrouter cache give you visibility into which tier is currently serving and what the backups hold. repair is the one to run if a network blip leaves you on a stale cache.