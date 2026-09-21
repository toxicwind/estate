// @sovereign/keypool — server: Bun.serve HTTP handler.
// Port of herd-keypool.py Handler. Routes /<pool>/... to upstream,
// strips caller auth, injects selected key, streams responses.

import { Pool, raceFirstValid, extractModel } from "./pool.js";
import type { KeyState } from "./types.js";
import { Auditor } from "./audit.js";

const HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

const STRIP_AUTH = new Set(["authorization", "x-api-key", "api-key"]);

// reasoning-first model substrings -> token floor
const REASONING_MODELS = ["o1", "o3", "gpt-5", "deepseek-r", "qwq", "r1"];
const TOKEN_FLOOR = 512;

function adaptBody(poolName: string, model: string | null, raw: Uint8Array): Uint8Array {
  if (!raw.length || !model) return raw;
  try {
    const body = JSON.parse(Buffer.from(raw).toString("utf8"));
    const m = model.toLowerCase();
    // reasoning-first: ensure token floor
    if (REASONING_MODELS.some((s) => m.includes(s))) {
      if (typeof body.max_tokens === "number" && body.max_tokens < TOKEN_FLOOR) {
        body.max_tokens = TOKEN_FLOOR;
      }
    }
    // o1/o3/gpt-5: strip unsupported sampling fields
    if (m.includes("o1") || m.includes("o3") || m.includes("gpt-5")) {
      delete body.temperature;
      delete body.top_p;
      delete body.presence_penalty;
      delete body.frequency_penalty;
    }
    return Buffer.from(JSON.stringify(body));
  } catch {
    return raw;
  }
}

export interface ServerDeps {
  pools: Map<string, Pool>;
  auditor: Auditor;
  raceKeys: number;
}

export function createHandler(deps: ServerDeps) {
  const { pools, auditor, raceKeys } = deps;

  return async (req: Request): Promise<Response> => {
    const url = new URL(req.url);
    const path = url.pathname;

    // /health
    if (path === "/health" && req.method === "GET") {
      return Response.json({ ok: true, service: "keypool" });
    }

    // /status
    if (path === "/status" && req.method === "GET") {
      const out: Record<string, unknown> = {};
      for (const [name, pool] of pools) {
        out[name] = {
          pool: name,
          upstream: pool.upstream,
          keys: pool.keys.map((k) => ({
            name: k.name,
            fp: k.fp,
            state: k.state,
            latency_ms: Math.round(k.latencyMs),
            down_until:
              k.downUntil > Date.now() ? new Date(k.downUntil).toISOString() : null,
            free_only: k.freeOnly,
          })),
          race_stats: pool.raceStats,
        };
      }
      return Response.json(out);
    }

    // /<pool>/... routing
    const m = path.match(/^\/([^/]+)(\/.*)?$/);
    if (!m) return Response.json({ error: "unknown keypool route" }, { status: 404 });
    const poolName = m[1];
    const rest = m[2] || "/";
    const pool = pools.get(poolName);
    if (!pool) {
      return Response.json({ error: "unknown keypool route" }, { status: 404 });
    }

    const raw = new Uint8Array(await req.arrayBuffer());
    const model = extractModel(raw);
    const adapted = adaptBody(poolName, model, raw);

    const t0 = Date.now();
    let keyName = "none";
    let status = 502;

    try {
      if (raceKeys > 1) {
        const candidates = pool.raceCandidates(model, raceKeys);
        if (!candidates.length) {
          return Response.json(
            {
              error: `keypool '${poolName}': no healthy key`,
              tried: [],
              hint: "see /status for per-key states; keys revalidate on demand",
            },
            { status: 502 },
          );
        }
        const kind = await raceFirstValid(
          pool,
          (ks) => forward(pool, rest, url.search, req, adapted, ks),
          candidates,
        );
        pool.recordRace(kind.kind === "winner");
        if (kind.kind === "winner" && kind.payload instanceof Response) {
          keyName = kind.keyName ?? "unknown";
          status = kind.payload.status;
          auditor.log({
            ts: new Date().toISOString(),
            pool: poolName,
            key_fp: keyFp(pool, keyName),
            model,
            method: req.method,
            path: rest,
            status,
            ms: Date.now() - t0,
            race: true,
          });
          return kind.payload;
        }
        if (kind.kind === "error" && typeof kind.payload === "number") {
          return Response.json(
            { error: `keypool upstream: HTTP ${kind.payload}` },
            { status: kind.payload },
          );
        }
        return Response.json(
          {
            error: `keypool '${poolName}': no healthy key`,
            tried: candidates.map((c) => c.name),
            hint: "see /status for per-key states; keys revalidate on demand",
          },
          { status: 502 },
        );
      }

      // Sequential path (RACE_KEYS=1)
      const tried: string[] = [];
      for (;;) {
        const ks = await pool.pick(model);
        if (!ks) {
          return Response.json(
            {
              error: `keypool '${poolName}': no healthy key`,
              tried,
              hint: "see /status for per-key states; keys revalidate on demand",
            },
            { status: 502 },
          );
        }
        if (tried.includes(ks.name)) {
          return Response.json(
            { error: `keypool '${poolName}': keys exhausted`, tried },
            { status: 502 },
          );
        }
        tried.push(ks.name);
        keyName = ks.name;
        try {
          const resp = await forward(pool, rest, url.search, req, adapted, ks);
          status = resp.status;
          auditor.log({
            ts: new Date().toISOString(),
            pool: poolName,
            key_fp: ks.fp,
            model,
            method: req.method,
            path: rest,
            status,
            ms: Date.now() - t0,
            race: false,
          });
          return resp;
        } catch (e) {
          const st = (e as { status?: number }).status ?? 0;
          if (st !== 0 && pool.failStatus.has(st)) {
            pool.markDown(ks, st);
            continue;
          }
          if (st !== 0) {
            return Response.json(
              { error: `keypool upstream: HTTP ${st}` },
              { status: st },
            );
          }
          return Response.json(
            { error: `keypool upstream: ${e}` },
            { status: 502 },
          );
        }
      }
    } finally {
      // audit on early returns is handled inline above
    }
  };
}

function keyFp(pool: Pool, name: string): string {
  return pool.keys.find((k) => k.name === name)?.fp ?? "unknown";
}

async function forward(
  pool: Pool,
  rest: string,
  search: string,
  req: Request,
  body: Uint8Array,
  ks: KeyState,
): Promise<Response> {
  const target = pool.upstream + rest + search;
  const headers = new Headers();
  for (const [k, v] of req.headers) {
    const lk = k.toLowerCase();
    if (HOP_HEADERS.has(lk) || STRIP_AUTH.has(lk)) continue;
    headers.set(k, v);
  }
  headers.set("Authorization", `Bearer ${pool.secretFor(ks.name)}`);

  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), pool.requestTimeoutMs);

  try {
    const resp = await fetch(target, {
      method: req.method,
      headers,
      body: body.length > 0 ? body : undefined,
      signal: ctrl.signal,
    });
    // Match urllib behavior: non-2xx throws with status attached
    if (resp.status >= 400) {
      // Drain to avoid socket leaks
      await resp.arrayBuffer().catch(() => {});
      throw Object.assign(new Error(`HTTP ${resp.status}`), {
        status: resp.status,
      });
    }
    return resp;
  } catch (e) {
    // Normalize to status-carrying error for the race/sequential logic
    const err = e as Error & { status?: number };
    if (err.name === "AbortError") {
      throw Object.assign(new Error("upstream timeout"), { status: 0 });
    }
    throw Object.assign(e as Error, { status: 0 });
  } finally {
    clearTimeout(t);
  }
}
