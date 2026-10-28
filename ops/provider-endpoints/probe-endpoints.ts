/**
 * probe-endpoints — the LIVE truth about every provider's models endpoint.
 *
 * The provider catalog (ranch/mimetite/generated/providers.json) says where a
 * provider lives; this script says whether that endpoint actually answers and
 * which models it lists. It is the endpoint map the control plane and the
 * estate operators use instead of guessing a path per provider.
 *
 * Rules:
 *   - `/v1/models/sse` is preferred when a provider exposes it, else
 *     `/v1/models` (the OpenAI-compatible model list).
 *   - A provider-specific path override exists for providers whose models
 *     list does NOT live under /v1 (chutes: /v1/chutes/models).
 *   - `{region}` templates (bedrock-mantle) are resolved before probing.
 *   - The verdict is what actually happened: ok / needs-auth / throttled /
 *     missing / unreachable. Nothing is inferred from the catalog.
 *
 * Run: bun ops/provider-endpoints/probe-endpoints.ts
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const MIMETITE_PROVIDERS =
  process.env.MIMETITE_PROVIDERS_JSON ??
  "/home/toxic/pens/estate/ranch/mimetite/generated/providers.json";
const OUT_DIR = here;
const PROBE_TIMEOUT_MS = 8000;
const CONCURRENCY = 12;

/** Provider-specific model-list paths that are not `/v1/models`. */
const PATH_OVERRIDES: Record<string, (base: string) => string[]> = {
  chutes: (base) => [
    `${base.replace(/\/+$/, "")}/chutes/models`,
    `${base.replace(/\/+$/, "")}/chutes/models/sse`,
  ],
  "bedrock-mantle": (base) => {
    const resolved = base.replace("{region}", "us-east-1");
    return [
      `${resolved.replace(/\/+$/, "")}/models/sse`,
      `${resolved.replace(/\/+$/, "")}/models`,
    ];
  },
  qianfan: (base) => [
    `${base.replace(/\/+$/, "")}/models`,
    `${base.replace(/\/+$/, "")}/models/sse`,
  ],
};

export type EndpointVerdict =
  "ok" | "needs-auth" | "throttled" | "missing" | "unreachable";

export interface ProviderEndpoint {
  readonly name: string;
  readonly baseUrl: string;
  readonly endpoint: string | null;
  readonly status: number | null;
  readonly verdict: EndpointVerdict;
  readonly models: number;
  readonly qwenModels: readonly string[];
  readonly qwenCount: number;
  readonly keyEnv: string | null;
  readonly attempts: ReadonlyArray<{
    readonly url: string;
    readonly status: number;
  }>;
}

function candidatesFor(name: string, baseUrl: string): string[] {
  const override = PATH_OVERRIDES[name];
  if (override) return override(baseUrl);
  const base = baseUrl.replace(/\/+$/, "");
  if (base.endsWith("/v1")) {
    return [
      `${base}/models/sse`,
      `${base}/models`,
      `${base.replace(/\/v1$/, "")}/models`,
    ];
  }
  return [
    `${base}/v1/models/sse`,
    `${base}/v1/models`,
    `${base}/models/sse`,
    `${base}/models`,
  ];
}

function keyFor(provider: Record<string, unknown>): {
  key: string | null;
  env: string | null;
} {
  const names = [
    provider.keyEnv as string | undefined,
    ...((provider.keyEnvs as string[] | undefined) ?? []),
  ].filter((n): n is string => typeof n === "string" && n.length > 0);
  for (const env of names) {
    const value = process.env[env];
    if (value) return { key: value, env };
  }
  return { key: null, env: null };
}

async function fetchModels(
  url: string,
  headers: Record<string, string>,
): Promise<{ status: number; models: string[] }> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);
  try {
    const res = await fetch(url, { headers, signal: controller.signal });
    const text = await res.text();
    if (res.status !== 200) return { status: res.status, models: [] };
    let parsed: unknown;
    try {
      parsed = JSON.parse(text);
    } catch {
      return { status: res.status, models: [] };
    }
    const items =
      parsed &&
      typeof parsed === "object" &&
      Array.isArray((parsed as { data?: unknown }).data)
        ? (parsed as { data: unknown[] }).data
        : Array.isArray(parsed)
          ? parsed
          : [];
    const models = items
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const rec = item as Record<string, unknown>;
          const id = rec.id ?? rec.name ?? rec.model;
          return typeof id === "string" ? id : null;
        }
        return null;
      })
      .filter((id): id is string => typeof id === "string");
    return { status: res.status, models };
  } catch {
    return { status: 0, models: [] };
  } finally {
    clearTimeout(timer);
  }
}

async function probeProvider(
  provider: Record<string, unknown>,
): Promise<ProviderEndpoint> {
  const name = (provider.name as string) ?? "unknown";
  const baseUrl = (provider.baseUrl as string) ?? "";
  const { key, env } = keyFor(provider);
  const attempts: Array<{ url: string; status: number }> = [];

  if (!baseUrl) {
    return {
      name,
      baseUrl,
      endpoint: null,
      status: null,
      verdict: "missing",
      models: 0,
      qwenModels: [],
      qwenCount: 0,
      keyEnv: env,
      attempts,
    };
  }

  for (const url of candidatesFor(name, baseUrl)) {
    const headerSets: Array<Record<string, string>> = [];
    if (key) {
      headerSets.push({ Authorization: `Bearer ${key}` });
      if (name.includes("chutes")) headerSets.push({ "Chutes-Auth": key });
    }
    headerSets.push({});

    for (const headers of headerSets) {
      const { status, models } = await fetchModels(url, headers);
      attempts.push({ url, status });
      if (status === 200 && models.length > 0) {
        const qwen = models.filter((m) => m.toLowerCase().includes("qwen"));
        return {
          name,
          baseUrl,
          endpoint: url,
          status,
          verdict: "ok",
          models: models.length,
          qwenModels: qwen.slice(0, 12),
          qwenCount: qwen.length,
          keyEnv: env,
          attempts,
        };
      }
      if (status === 401 || status === 403) break;
    }
  }

  const best = attempts.reduce<{ url: string; status: number } | null>(
    (acc, attempt) => {
      const score = (s: number) =>
        s === 429
          ? 5
          : s === 401 || s === 403
            ? 4
            : s === 404
              ? 2
              : s === 0
                ? 1
                : 3;
      if (!acc) return attempt;
      return score(attempt.status) > score(acc.status) ? attempt : acc;
    },
    null,
  );
  const status = best?.status ?? null;
  const verdict: EndpointVerdict =
    status === null
      ? "unreachable"
      : status === 429
        ? "throttled"
        : status === 401 || status === 403
          ? "needs-auth"
          : "missing";
  return {
    name,
    baseUrl,
    endpoint: best?.url ?? null,
    status,
    verdict,
    models: 0,
    qwenModels: [],
    qwenCount: 0,
    keyEnv: env,
    attempts,
  };
}

async function main(): Promise<void> {
  const raw = JSON.parse(readFileSync(MIMETITE_PROVIDERS, "utf8")) as {
    providers?: Array<Record<string, unknown>>;
  };
  const providers = Array.isArray(raw.providers) ? raw.providers : [];
  const results: ProviderEndpoint[] = [];
  const queue = [...providers];
  const workers = Array.from({ length: CONCURRENCY }, async () => {
    for (;;) {
      const next = queue.shift();
      if (!next) return;
      results.push(await probeProvider(next));
    }
  });
  await Promise.all(workers);
  results.sort((a, b) => a.name.localeCompare(b.name));

  const summary = {
    total: results.length,
    ok: results.filter((r) => r.verdict === "ok").length,
    needsAuth: results.filter((r) => r.verdict === "needs-auth").length,
    throttled: results.filter((r) => r.verdict === "throttled").length,
    missing: results.filter((r) => r.verdict === "missing").length,
    unreachable: results.filter((r) => r.verdict === "unreachable").length,
    withQwen: results.filter((r) => r.qwenCount > 0).length,
  };

  const artifact = {
    generatedAt: new Date().toISOString(),
    source: MIMETITE_PROVIDERS,
    summary,
    providers: results,
  };
  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(
    join(OUT_DIR, "provider-endpoints.json"),
    `${JSON.stringify(artifact, null, 2)}\n`,
    "utf8",
  );

  const lines = [
    "# Provider endpoints (live probe)",
    "",
    `Generated: ${artifact.generatedAt}`,
    "",
    "| provider | verdict | endpoint | models | qwen |",
    "| --- | --- | --- | --- | --- |",
    ...results.map(
      (r) =>
        `| ${r.name} | ${r.verdict} | ${r.endpoint ?? "—"} | ${r.models} | ${r.qwenCount} |`,
    ),
    "",
  ];
  writeFileSync(
    join(OUT_DIR, "provider-endpoints.md"),
    `${lines.join("\n")}\n`,
    "utf8",
  );

  console.log(JSON.stringify(summary, null, 2));
  for (const r of results) {
    console.log(
      `${r.verdict.padEnd(12)} ${r.name.padEnd(20)} ${String(r.status ?? "-").padStart(4)} models=${String(r.models).padStart(4)} qwen=${String(r.qwenCount).padStart(3)} ${r.endpoint ?? ""}`,
    );
  }
}

if (import.meta.main) {
  await main();
}
