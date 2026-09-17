#!/usr/bin/env bun
/**
 * Sovereign Router v3.1 (Bun/TypeScript)
 * Port of sovereign-router/router.py — same strategies, HealthDB WAL, circuit breakers.
 *
 * Strategies: fifo_matrix | ast_race | sticky_affinity | weighted_elo | circuit_chain | hybrid
 * Default hybrid: sticky → ast_race → circuit_chain; explicit CODING aliases go direct.
 *
 * Env SSOT: sovereign/config/ports.env (mise _.file) + ~/.secrets
 *   SOVEREIGN_ROUTER_PORT / SOVEREIGN_PORT — never invent non-25xxx ports
 */

import { createHash } from "node:crypto";
import { handleMeshRequest } from "../../../src/lib/ghas-mesh-features.ts";
import type { ChatBody } from "./router_types.ts";
import { CODING, PROVIDERS, PROVIDER_MODELS, keyOk, STRATEGY, MAX_PARALLEL, PORT, json, log, DB_PATH, isExplicit } from "./router_config.ts";
import { catalogModelsFor, LIVE_MODELS, LIVE_MODEL_META, modelFree } from "./router_config.ts";
import { startLiveDiscovery, LIVE_STATUS } from "./router_live_models.ts";
import { state } from "./router_matrix.ts";
import { ROUTERS, routeHybrid, callOne, pickWeighted } from "./router_strategy.ts";
import { uiData, ROUTER_UI_HTML } from "./router_ui.ts";

// ---------------------------------------------------------------------------
// Optional client auth (absorbed from the retired :8000 key-proxy).
// Set SOVEREIGN_CLIENT_KEYS=comman,separated,keys to require a client key.
// Unset = open (daemon binds 127.0.0.1; localhost is the trust boundary).
// ---------------------------------------------------------------------------
const CLIENT_KEYS = (process.env.SOVEREIGN_CLIENT_KEYS || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

function clientAuthorized(req: Request): boolean {
  if (!CLIENT_KEYS.length) return true;
  const h = req.headers.get("authorization") || "";
  const bearer = h.startsWith("Bearer ") ? h.slice(7).trim() : "";
  const key = bearer || req.headers.get("x-api-key") || "";
  return key !== "" && CLIENT_KEYS.includes(key);
}

// ---------------------------------------------------------------------------
// HTTP
// ---------------------------------------------------------------------------
function sessionId(req: Request, body: ChatBody): string {
  const h = req.headers.get("X-Session-Id");
  if (h) return h;
  const seed = JSON.stringify((body.messages || []).slice(0, 1));
  return createHash("md5").update(seed).digest("hex").slice(0, 12);
}

async function handleStream(
  body: ChatBody,
  sid: string,
  _strat: string,
): Promise<Response> {
  const model = String(body.model || "auto");
  const tryStream = async (p: string, mid: string) => {
    const r = await callOne(p, mid, body, true);
    if (!r.ok || !r.stream) return null;
    state.stickySet(sid, p, mid);
    return new Response(r.stream, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "X-Routed-Via": `${p}/${mid}`,
      },
    });
  };

  if (isExplicit(model)) {
    const [p, mid] = CODING[model]!;
    const resp = await tryStream(p, mid);
    if (resp) return resp;
  } else {
    const [sp, sm] = state.stickyGet(sid);
    if (sp && keyOk(sp) && state.circuitOk(sp)) {
      const resp = await tryStream(sp, sm || model);
      if (resp) return resp;
    }
  }

  const cands = isExplicit(model)
    ? [CODING[model]!]
    : pickWeighted(MAX_PARALLEL);
  for (const [p, mid] of cands) {
    const resp = await tryStream(p, mid);
    if (resp) return resp;
  }
  return json({ error: "all_stream_providers_exhausted" }, 503);
}

const server = Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  async fetch(req) {
    const url = new URL(req.url);
    const path = url.pathname;

    if (path.startsWith("/mesh")) {
      const m = await handleMeshRequest(req, {
        service: "sovereign-router",
        version: "v3.1",
      });
      if (m) return m;
    }

    // Client-key gate (only when SOVEREIGN_CLIENT_KEYS is set). /health stays
    // open for liveness probes; everything else requires a key.
    if (path !== "/health" && !clientAuthorized(req)) {
      return json({ error: "unauthorized" }, 401);
    }

    if (req.method === "GET" && (path === "/v1/models" || path === "/models")) {
      // Union of every model every configured key can serve (curated + live
      // discovery), plus the CODING aliases. Each entry carries the provider's
      // live metadata (pricing, context_length, architecture...) plus the
      // router's own routing metadata under "x-sovereign". The free flag is
      // the same live-derived eligibility routing consumes (modelFree), not a
      // static suffix guess.
      const seen = new Set<string>();
      const data: Record<string, unknown>[] = [];
      const sovMeta = (p: string, id: string, source: string) => ({
        provider: p,
        source,
        free: modelFree(p, id),
        elo: Math.round((state.elo.get(p) || 1000) * 10) / 10,
        circuit: state.circuit.get(p) || "unknown",
        empty_strikes: state.emptyStrikeCount(p, id),
      });
      const push = (p: string, id: string, source: string) => {
        if (seen.has(id)) return;
        seen.add(id);
        const meta = (LIVE_MODEL_META[p] || {})[id] || {};
        data.push({
          id,
          object: "model",
          owned_by: p,
          ...(meta as Record<string, unknown>),
          "x-sovereign": sovMeta(p, id, source),
        });
      };
      for (const p of Object.keys(PROVIDERS)) {
        if (!keyOk(p)) continue;
        const curated = new Set(PROVIDER_MODELS[p] || []);
        const liveIds = new Set(LIVE_MODELS[p] || []);
        for (const m of catalogModelsFor(p)) {
          const source =
            curated.has(m) && liveIds.has(m)
              ? "curated+live"
              : liveIds.has(m)
                ? "live"
                : "curated";
          push(p, m, source);
        }
      }
      for (const id of Object.keys(CODING)) {
        if (seen.has(id)) continue;
        seen.add(id);
        data.push({
          id,
          object: "model",
          owned_by: "alias",
          "x-sovereign": {
            provider: "alias",
            source: "alias",
            free: id === "free",
            elo: null,
            circuit: null,
            empty_strikes: 0,
          },
        });
      }
      return json({ object: "list", data, live: LIVE_STATUS });
    }

    if (req.method === "GET" && path === "/metrics") {
      // Prometheus exposition (absorbed from the retired :8000 key-proxy).
      const dbSummary = state.health.getProviderSummary() as Record<
        string,
        {
          successes?: number;
          failures?: number;
          success_rate?: number;
          avg_latency_ms?: number;
          rate_limited?: number;
        }
      >;
      const L: string[] = [];
      const circuitNum = (p: string) => {
        const s = state.circuit.get(p) || "closed";
        return s === "open" ? 1 : s === "half" ? 2 : 0;
      };
      for (const p of Object.keys(PROVIDERS)) {
        const s = dbSummary[p] || {};
        const req_total = (s.successes || 0) + (s.failures || 0);
        L.push(
          `sovereign_router_requests_total{provider="${p}"} ${req_total}`,
          `sovereign_router_success_rate{provider="${p}"} ${s.success_rate ?? 0}`,
          `sovereign_router_avg_latency_ms{provider="${p}"} ${s.avg_latency_ms ?? 0}`,
          `sovereign_router_rate_limited_total{provider="${p}"} ${s.rate_limited ?? 0}`,
          `sovereign_router_circuit_open{provider="${p}"} ${circuitNum(p)}`,
          `sovereign_router_elo{provider="${p}"} ${Math.round((state.elo.get(p) || 1000) * 10) / 10}`,
          `sovereign_router_live_models{provider="${p}"} ${(LIVE_MODELS[p] || []).length}`,
        );
      }
      for (const [k, v] of state.emptyStrikes) {
        const [p, ...rest] = k.split("/");
        L.push(
          `sovereign_router_model_empty_strikes{provider="${p}",model="${rest.join("/").replace(/"/g, "")}"} ${v.n}`,
        );
      }
      return new Response(
        "# HELP sovereign_router_requests_total Total chat completion requests per provider\n" +
          "# TYPE sovereign_router_requests_total counter\n" +
          L.join("\n") +
          "\n",
        { headers: { "Content-Type": "text/plain; version=0.0.4" } },
      );
    }

    if (req.method === "GET" && (path === "/ui" || path === "/ui/")) {
      return new Response(ROUTER_UI_HTML, {
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }
    if (req.method === "GET" && path === "/ui/data") {
      return json(uiData());
    }

    if (req.method === "GET" && path === "/health") {
      const dbSummary = state.health.getProviderSummary();
      const providers: Record<string, unknown> = {};
      for (const p of Object.keys(PROVIDERS)) {
        providers[p] = {
          keys: keyOk(p) ? "configured" : "no_key",
          elo: Math.round((state.elo.get(p) || 1000) * 10) / 10,
          circuit: state.circuit.get(p) || "unknown",
          models: catalogModelsFor(p).length,
          live_models: (LIVE_MODELS[p] || []).length,
          live_status: LIVE_STATUS[p] || null,
          health: dbSummary[p] || null,
        };
      }
      return json({
        status: "ok",
        router: "sovereign-router-ts",
        version: "v3.1",
        strategy: STRATEGY,
        parallel: MAX_PARALLEL,
        providers,
      });
    }

    if (req.method === "GET" && path === "/debug/sqlite") {
      try {
        return json(state.health.debugAgg());
      } catch (e) {
        return json({ error: String(e) }, 500);
      }
    }

    if (req.method === "GET" && path === "/debug/health") {
      try {
        const healing: Record<string, unknown> = {};
        for (const p of Object.keys(PROVIDERS)) {
          healing[p] = state.health.recentHealing(p);
        }
        return json({
          summary: state.health.getProviderSummary(),
          healing,
        });
      } catch (e) {
        return json({ error: String(e) }, 500);
      }
    }

    if (req.method === "POST" && path.includes("/chat/completions")) {
      let body: ChatBody;
      try {
        body = (await req.json()) as ChatBody;
      } catch {
        return json({ error: "invalid_json" }, 400);
      }
      const sid = sessionId(req, body);
      const strat = req.headers.get("X-Sovereign-Strategy") || STRATEGY;
      log(`${req.method} ${path} model=${body.model} strat=${strat}`);

      if (body.stream) {
        return handleStream(body, sid, strat);
      }

      const fn = ROUTERS[strat] || routeHybrid;
      const r = await fn(body, sid);
      if (r.ok) {
        return new Response(r.data as BodyInit, {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "X-Routed-Via": `${r.provider}/${r.model}`,
            "X-Latency": String(Math.round((r.lat || 0) * 1000) / 1000),
            "X-Strategy": strat,
          },
        });
      }
      return json(
        { error: r.err || "exhausted", status: r.status },
        r.status || 503,
      );
    }

    return new Response("Not Found", { status: 404 });
  },
});

// Live model discovery: curated list + every model each key can serve.
startLiveDiscovery();

const keyed = Object.keys(PROVIDERS).filter(keyOk);

console.log(`Sovereign Router TS v3.1 on http://127.0.0.1:${PORT}/v1`);

console.log(
  `Strategy=${STRATEGY} | routes: ${Object.keys(ROUTERS).join(", ")}`,
);

console.log(`Streaming=SSE | Providers: ${keyed.join(", ") || "(none)"}`);

console.log(`Health DB: ${DB_PATH} (WAL)`);

console.log(`Listening ${server.hostname}:${server.port}`);

// hotreload-probe 1784356795195
