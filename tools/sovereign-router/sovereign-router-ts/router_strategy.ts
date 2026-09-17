import type { ChatBody, RouteResult } from "./router_types.ts";
import { state } from "./router_matrix.ts";
import { PROVIDERS, PROVIDER_MODELS, catalogModelsFor, modelFree, LOCAL_ROLES, CODING, MAX_PARALLEL, FIFO_MAX, STRATEGY, UA, AST_RE, getKey, keyOk, firstModelFor, resolveModel, isLocalSwapModelId, isAst, isExplicit, json } from "./router_config.ts";

// ---------------------------------------------------------------------------
// Substance guard: a completion is servable only if it carries non-empty
// content (or tool_calls). HTTP 200 with an empty message is a failure at
// every routing layer — never served, never sticky-pinned, always struck.
// ---------------------------------------------------------------------------
function messageOf(r: RouteResult): any {
  try {
    const raw =
      typeof r.data === "string"
        ? r.data
        : new TextDecoder().decode(r.data as Uint8Array);
    return JSON.parse(raw)?.choices?.[0]?.message;
  } catch {
    return undefined;
  }
}

export function substantive(r: RouteResult): boolean {
  if (!r.ok) return false;
  const m = messageOf(r);
  if (!m) return false;
  if (typeof m.content === "string" && m.content.trim() !== "") return true;
  return Array.isArray(m.tool_calls) && m.tool_calls.length > 0;
}

function contentText(r: RouteResult): string {
  const m = messageOf(r);
  const c = m?.content;
  return typeof c === "string" ? c : "";
}

// Any model id the router can directly address: explicit alias, local id,
// or any curated/live catalog id on any keyed provider. Unknown ids keep
// the old race-everything behavior.
function isRoutableModelId(model: string): boolean {
  if (isExplicit(model)) return true;
  for (const p of Object.keys(PROVIDERS)) {
    if (catalogModelsFor(p).includes(model)) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Provider call
// ---------------------------------------------------------------------------
export async function callOne(
  provider: string,
  model: string,
  body: ChatBody,
  stream = false,
): Promise<RouteResult> {
  if (!state.circuitOk(provider)) {
    return {
      ok: false,
      status: 503,
      provider,
      lat: 0,
      err: "circuit_open",
    };
  }
  const conf = PROVIDERS[provider];
  if (!conf) {
    return {
      ok: false,
      status: 500,
      provider,
      lat: 0,
      err: "unknown_provider",
    };
  }
  const url = conf.base.replace(/\/$/, "") + "/chat/completions";
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "User-Agent": UA,
    "Accept-Encoding": "identity",
  };
  if (!conf.no_auth) {
    // NVIDIA rotates across the multi-key pool (40 rpm token bucket per key);
    // null (all buckets dry) falls back to the default key.
    const rk = provider === "nvidia" ? state.nextNvidiaKey() : null;
    headers.Authorization = `Bearer ${rk || getKey(provider)}`;
  } else {
    headers.Authorization = "Bearer not-required-for-local";
  }
  if (provider === "openrouter") {
    headers["HTTP-Referer"] = "https://zed.dev";
    headers["X-Title"] = "Sovereign-Router";
  }
  const payload = { ...body, model, stream };
  const start = performance.now();
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(stream ? 180_000 : 120_000),
    });
    const lat = (performance.now() - start) / 1000;
    if (!resp.ok) {
      const errText = (await resp.text()).slice(0, 500);
      state.record(model, provider, resp.status, lat, 0, STRATEGY);
      return {
        ok: false,
        status: resp.status,
        provider,
        lat,
        err: errText,
      };
    }
    if (stream) {
      state.record(model, provider, 200, lat, 0, STRATEGY);
      if (state.circuit.get(provider) === "half")
        state.circuit.set(provider, "closed");
      return {
        ok: true,
        status: resp.status,
        provider,
        model,
        lat,
        stream: resp.body,
      };
    }
    const data = await resp.arrayBuffer();
    state.record(model, provider, resp.status, lat, 0, STRATEGY);
    if (state.circuit.get(provider) === "half")
      state.circuit.set(provider, "closed");
    return {
      ok: true,
      status: resp.status,
      data: new Uint8Array(data),
      provider,
      model,
      lat,
    };
  } catch (e) {
    const lat = (performance.now() - start) / 1000;
    state.record(model, provider, 500, lat, 0, STRATEGY);
    return {
      ok: false,
      status: 500,
      provider,
      lat,
      err: String(e),
    };
  }
}

export function pickWeighted(n = MAX_PARALLEL): [string, string][] {
  const scored: [number, string, string][] = [];
  for (const p of Object.keys(PROVIDERS)) {
    if (!keyOk(p) || !state.circuitOk(p)) continue;
    const sc = (state.elo.get(p) || 1000) + Math.random() * 10;
    const mid = firstModelFor(p);
    if (mid) scored.push([sc, p, mid]);
  }
  scored.sort((a, b) => b[0] - a[0]);
  const out: [string, string][] = [];
  const seen = new Set<string>();
  for (const [, p, mid] of scored) {
    if (seen.has(p)) continue;
    seen.add(p);
    out.push([p, mid]);
    if (out.length >= n) break;
  }
  if (!out.length && keyOk("openrouter")) {
    out.push(["openrouter", "tencent/hy3:free"]);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Strategies
// ---------------------------------------------------------------------------
export async function routeAstRace(
  body: ChatBody,
  session: string,
  candsOverride?: [string, string][],
): Promise<RouteResult> {
  const model = String(body.model || "auto");
  if (isRoutableModelId(model) && !candsOverride) {
    // Direct-addressable id (alias, local id, or any curated/live catalog
    // id): go straight to its provider instead of racing.
    const [p, mid] = resolveModel(model);
    const r = await callOne(p, mid, body);
    if (substantive(r)) {
      state.stickySet(session, p, mid);
      state.record(mid, p, 200, r.lat || 0, 1, "ast_race");
      return r;
    }
    if (r.ok) state.recordEmpty(p, mid);
    return {
      ok: false,
      status: r.ok ? 502 : r.status || 502,
      provider: p,
      lat: r.lat,
      err: r.ok ? "empty_completion" : r.err,
    };
  }
  const cands = candsOverride || pickWeighted(MAX_PARALLEL);
  if (!cands.length)
    return { ok: false, status: 503, err: "ast_race_exhausted" };
  const futs = cands.map(([p, mid]) => callOne(p, mid, body));
  let best: RouteResult | null = null;
  // Non-substantive (empty/whitespace-only, no tool_calls) completions are
  // failures, never winners: a 200 with no content must not be served or
  // sticky-pinned.
  try {
    const results = await Promise.race([
      Promise.allSettled(futs).then((all) => all),
      new Promise<"timeout">((res) => setTimeout(() => res("timeout"), 95_000)),
    ]);
    if (results !== "timeout") {
      for (const settled of results) {
        if (settled.status !== "fulfilled" || !settled.value.ok) continue;
        const r = settled.value;
        const content = contentText(r);
        if (isAst(content)) {
          state.stickySet(session, r.provider!, r.model!);
          state.record(r.model!, r.provider!, 200, r.lat || 0, 1, "ast_race");
          return r;
        }
        if (!substantive(r)) {
          // Non-substantive completion: never a winner — strike the model
          // (flap tracker benches it after FLAP_STRIKES within the window).
          state.recordEmpty(r.provider!, r.model!);
        } else if (!best) {
          best = r;
        }
      }
    } else {
      // timeout: take first completed substantive result, if any
      for (const f of futs) {
        const settled = await Promise.race([
          f.then((v) => v),
          Promise.resolve(null as RouteResult | null),
        ]);
        if (settled && substantive(settled)) {
          best = settled;
          break;
        }
      }
    }
  } catch {
    /* exhausted */
  }
  if (best?.ok) {
    state.stickySet(session, best.provider!, best.model!);
    return best;
  }
  return { ok: false, status: 503, err: "ast_race_exhausted" };
}

export async function routeSticky(
  body: ChatBody,
  session: string,
): Promise<RouteResult> {
  const model = String(body.model || "auto");
  if (isRoutableModelId(model)) return routeAstRace(body, session);
  const [p, m] = state.stickyGet(session);
  if (p && keyOk(p) && state.circuitOk(p)) {
    const r = await callOne(p, m || model, body);
    if (substantive(r)) return r;
    if (r.ok) state.recordEmpty(p, m || model);
  }
  return routeAstRace(body, session);
}

export async function routeWeighted(
  body: ChatBody,
  session: string,
): Promise<RouteResult> {
  const cands = pickWeighted(1);
  if (!cands.length) return { ok: false, status: 503, err: "no_providers" };
  const [p, mid] = cands[0];
  const r = await callOne(p, mid, body);
  if (substantive(r)) {
    state.stickySet(session, p, mid);
    return r;
  }
  if (r.ok) state.recordEmpty(p, mid);
  return {
    ok: false,
    status: r.ok ? 502 : r.status || 502,
    provider: p,
    lat: r.lat,
    err: r.ok ? "empty_completion" : r.err,
  };
}

export async function routeCircuitChain(
  body: ChatBody,
  session: string,
): Promise<RouteResult> {
  const model = String(body.model || "auto");
  if (isRoutableModelId(model)) {
    const [p, mid] = resolveModel(model);
    if (keyOk(p) && state.circuitOk(p)) {
      const r = await callOne(p, mid, body);
      if (substantive(r)) {
        state.stickySet(session, p, mid);
        return r;
      }
      if (r.ok) state.recordEmpty(p, mid);
      return {
        ok: false,
        status: r.ok ? 502 : r.status || 502,
        provider: p,
        lat: r.lat,
        err: r.ok ? "empty_completion" : r.err,
      };
    }
    return {
      ok: false,
      status: 502,
      err: `explicit_provider_unavailable:${p}`,
    };
  }
  const order = Object.keys(PROVIDERS).sort(
    (a, b) => (state.elo.get(b) || 1000) - (state.elo.get(a) || 1000),
  );
  for (const p of order) {
    if (!keyOk(p) || !state.circuitOk(p)) continue;
    const mid = firstModelFor(p);
    if (!mid) continue;
    const r = await callOne(p, mid, body);
    if (substantive(r)) {
      state.stickySet(session, p, mid);
      return r;
    }
    if (r.ok) state.recordEmpty(p, mid);
  }
  return { ok: false, status: 503, err: "circuit_chain_exhausted" };
}

export async function routeFifo(
  body: ChatBody,
  session: string,
): Promise<RouteResult> {
  if (state.fifoDepth >= FIFO_MAX) {
    return { ok: false, status: 429, err: "fifo_full" };
  }
  state.fifoDepth++;
  try {
    return await routeAstRace(body, session);
  } finally {
    state.fifoDepth = Math.max(0, state.fifoDepth - 1);
  }
}

export async function routeHybrid(
  body: ChatBody,
  session: string,
): Promise<RouteResult> {
  const model = String(body.model || "auto");
  if (isRoutableModelId(model)) {
    const [p, mid] = resolveModel(model);
    const r = await callOne(p, mid, body);
    if (substantive(r)) {
      state.stickySet(session, p, mid);
      state.record(mid, p, 200, r.lat || 0, 1, "hybrid_direct");
      return r;
    }
    if (r.ok) state.recordEmpty(p, mid);
    return {
      ok: false,
      status: r.ok ? 502 : r.status || 502,
      provider: p,
      lat: r.lat,
      err: r.ok ? "empty_completion" : r.err,
    };
  }
  const [p, m] = state.stickyGet(session);
  if (p && keyOk(p) && state.circuitOk(p)) {
    const r = await callOne(p, m || model, body);
    if (substantive(r)) return r;
    if (r.ok) state.recordEmpty(p, m || model);
  }
  const r2 = await routeAstRace(body, session);
  if (r2.ok) return r2;
  return routeCircuitChain(body, session);
}

export const ROUTERS: Record<
  string,
  (body: ChatBody, session: string) => Promise<RouteResult>
> = {
  fifo_matrix: routeFifo,
  ast_race: routeAstRace,
  sticky_affinity: routeSticky,
  weighted_elo: routeWeighted,
  circuit_chain: routeCircuitChain,
  hybrid: routeHybrid,
  free: routeFree,
};

// freeCandidates: the free pool is derived from LIVE catalog metadata, not a
// divergent static list (Chris 2026-09-17). For every keyed provider with a
// healthy circuit, every catalog id (curated ∪ live discovery) whose live
// metadata marks it free (modelFree) joins the pool — including
// live-discovered free models the static ":free"-suffix convention misses
// (e.g. stealth/union-alpha, openrouter/free). When a provider has no live
// metadata at all, modelFree falls back deterministically to the ":free"
// suffix convention, so a failed discovery refresh never empties the pool.
// Filters: circuit state, flap strikes (empty-output substance failures feed
// the strike counter, so substance-ineligible models sit out), and the local
// llama-swap roles are always zero-cost and always join.
export function freeCandidates(): [string, string][] {
  const out: [string, string][] = [];
  for (const [name] of Object.entries(PROVIDERS)) {
    if (!keyOk(name) || !state.circuitOk(name)) continue;
    for (const mid of catalogModelsFor(name)) {
      // Flap-benched models sit out until their empty-strikes decay.
      if (state.flapBanned(name, mid)) continue;
      if (modelFree(name, mid)) out.push([name, mid]);
    }
  }
  if (keyOk("llama-swap")) {
    out.push(["llama-swap", LOCAL_ROLES.fast]);
    out.push(["llama-swap", LOCAL_ROLES.quality]);
    out.push(["llama-swap", LOCAL_ROLES.longctx]);
  }
  return out;
}

// routeFree: maximal free-provider strategy. Races the free+local candidate
// pool through the SAME parallel-race / AST-preference / sticky / circuit
// machinery as ast_race — so local GPU and free cloud models compete on equal
// footing, and circuit breakers still apply per provider.
export async function routeFree(
  body: ChatBody,
  session: string,
): Promise<RouteResult> {
  const cands = freeCandidates();
  if (!cands.length)
    return { ok: false, status: 503, err: "no_free_providers" };
  return routeAstRace(body, session, cands);
}
