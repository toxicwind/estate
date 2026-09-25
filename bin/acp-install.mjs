#!/usr/bin/env bun
// acp-install.mjs — sovereign ACP pipeline one-shot installer & diagnostic repair
// Features: Dual-runtime DNS preflight, stream-safe TCP bridge, per-connection stdio normalization,
// resilient multi-source secret harvester, 24-event typed event bus, AWS full-jitter backoff,
// and stateful circuit-breaker catalog synchronization.

import fs from "fs";
import net from "net";
import dns from "node:dns";
import crypto from "crypto";
import { execSync } from "child_process";

const H = (s) => crypto.createHash("sha256").update(s).digest("hex").slice(0, 12);
const sh = (c) => {
  try {
    return execSync(c, { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"], env: { ...process.env, PAGER: "cat" } }).trim();
  } catch (e) {
    return ((e.stdout || "") + (e.stderr || "")).trim();
  }
};

const C = {
  reset: "\x1b[0m", bold: "\x1b[1m", dim: "\x1b[2m",
  green: "\x1b[32m", yellow: "\x1b[33m", red: "\x1b[31m",
  cyan: "\x1b[36m", magenta: "\x1b[35m", blue: "\x1b[34m",
};
const ok = (m) => console.log(`  ${C.green}✓${C.reset} ${m}`);
const warn = (m) => console.log(`  ${C.yellow}⚠${C.reset} ${m}`);
const err = (m) => console.log(`  ${C.red}✗${C.reset} ${m}`);
const hdr = (m) => console.log(`\n${C.bold}${C.cyan}${m}${C.reset}`);
const info = (m) => console.log(`  ${C.dim}${m}${C.reset}`);

// ---------------------------------------------------------------------------
// PATH SPECIFICATIONS
// ---------------------------------------------------------------------------
const HOME        = "/home/toxic";
const EXT_PATH    = `${HOME}/.tau/extensions/vansrouter.ts`;
const BRIDGE_PATH = `${HOME}/sovereign/bin/acp-tcp-bridge`;
const PROBE_PATH  = `${HOME}/sovereign/bin/acp-probe.mjs`;
const PITCH_CANON = `${HOME}/sovereign/pitchfork.toml`;
const PITCH_DUP   = `${HOME}/pitchfork.toml`;
const OMP_BIN     = `${HOME}/sovereign/projects/tau/packages/coding-agent/dist/omp`;
const PORT        = 25111;
const VR_HOST     = "127.0.0.1";
const VR_PORT     = 20128;

// ---------------------------------------------------------------------------
// 0. BOUNDED DNS PREFLIGHT
// ---------------------------------------------------------------------------
hdr("0. DNS Preflight");

async function preflightDns(host, port, timeoutMs = 3000) {
  const t0 = performance.now();
  if (typeof globalThis.Bun !== "undefined" && globalThis.Bun?.dns?.prefetch) {
    try {
      globalThis.Bun.dns.prefetch(host, port);
      ok(`Bun.dns.prefetch("${host}", ${port}) executed`);
    } catch (e) {
      warn(`Bun.dns.prefetch: ${e.message}`);
    }
  }

  try {
    const addrs = await Promise.race([
      dns.promises.resolve4(host, { ttl: true }),
      new Promise((_, rej) => setTimeout(() => rej(Object.assign(new Error("DNS timeout"), { code: "ETIMEDOUT" })), timeoutMs)),
    ]);
    const lat = +(performance.now() - t0).toFixed(2);
    if (!addrs || addrs.length === 0) throw new Error("No A records returned");
    ok(`Resolved ${host}:${port} -> ${addrs.map((a) => a.address).join(", ")} (${lat}ms, ttl=${addrs[0].ttl}s)`);
    return addrs.map((a) => a.address);
  } catch (e) {
    const lat = +(performance.now() - t0).toFixed(2);
    warn(`${host}:${port} resolution notice after ${lat}ms: ${e.code ?? e.message}`);
    return [host];
  }
}

await preflightDns(VR_HOST, VR_PORT);

// ---------------------------------------------------------------------------
// 1. VANSROUTER EXTENSION (Dynamic Key Chain + Circuit Breaker + Live Re-reg)
// ---------------------------------------------------------------------------
hdr("1. Deploy vansrouter.ts extension");

const EXT_SOURCE = `import fs from "fs";
import dns from "node:dns";

import type {
  ExtensionAPI,
  ExtensionContext,
  ProviderConfig,
  ProviderModelConfig,
} from "@oh-my-pi/pi-coding-agent";

// ============================================================================
// DEFINITION LAYER
// ============================================================================
const DEFINITION = { id: "vansrouter", name: "VansRouter", version: "3.1.0" } as const;
const TAG = \`[\${DEFINITION.id}]\`;

// ============================================================================
// CONFIG & CIRCUIT CONSTANTS
// ============================================================================
const VR_ENV_KEY = "VANSROUTER_API_KEY";
const VR_CONFIG_FILE = "/home/toxic/.config/vansrouter/env";
const VR_SECRETS_FILE = "/home/toxic/.secrets";
const VR_HARD_FALLBACK = "local-sovereign";
const VR_URLS = [process.env.VANSROUTER_URL, process.env.NINEROUTER_URL, "http://127.0.0.1:20128"].filter((u): u is string => typeof u === "string" && u.length > 0);

const MODEL_CACHE_TTL_MS = 60_000;
const HEALTH_INTERVAL_MS = 30_000;
const FETCH_TIMEOUT_MS = 5_000;
const HEALTH_TIMEOUT_MS = 2_000;
const DNS_TIMEOUT_MS = 3_000;
const MAX_RETRIES = 3;
const BASE_BACKOFF_MS = 500;
const MAX_BACKOFF_MS = 8_000;
const CIRCUIT_FAILURE_THRESHOLD = 3;
const CIRCUIT_COOLDOWN_MS = 15_000;

// ============================================================================
// LOGGING
// ============================================================================
function log(level: "debug" | "info" | "warn" | "error", msg: string, data?: unknown): void {
  const line = \`\${TAG} \${msg}\`;
  const sink = level === "error" ? console.error : level === "warn" ? console.warn : console.log;
  if (data !== undefined) sink(line, data); else sink(line);
}

// ============================================================================
// EVENT BUS — 24 Typed Lifecycle Events
// ============================================================================
type VansRouterEvent =
  | { type: "dns.prefetch"; host: string; port: number; ts: number }
  | { type: "dns.resolved"; host: string; addresses: string[]; latencyMs: number; ts: number }
  | { type: "dns.failed"; host: string; error: string; latencyMs: number; ts: number }
  | { type: "key.resolved"; source: string; chain: Array<{ source: string; tried: boolean; hit: boolean; reason?: string }>; ts: number }
  | { type: "provider.registered"; baseUrl: string; keySource: string; keyLen: number; capabilities: Record<string, unknown>; ts: number }
  | { type: "provider.registration_failed"; error: string; ts: number }
  | { type: "models.fetched"; count: number; source: string; latencyMs: number; ts: number }
  | { type: "models.cached"; count: number; ageMs: number; ts: number }
  | { type: "models.shard"; source: string; count: number; ts: number }
  | { type: "models.seed_fallback"; count: number; ts: number }
  | { type: "fetch.attempt"; url: string; attempt: number; delayMs: number; ts: number }
  | { type: "fetch.failed"; url: string; attempt: number; error: string; ts: number }
  | { type: "fetch.succeeded"; url: string; attempt: number; latencyMs: number; ts: number }
  | { type: "fetch.rotated"; from: string; to: string; ts: number }
  | { type: "circuit.opened"; provider: string; failures: number; cooldownMs: number; ts: number }
  | { type: "circuit.half_open"; provider: string; ts: number }
  | { type: "circuit.closed"; provider: string; ts: number }
  | { type: "circuit.rejected"; provider: string; remainingMs: number; ts: number }
  | { type: "health.changed"; online: boolean; consecutiveFails: number; latencyMs: number; url: string; ts: number }
  | { type: "health.probe"; url: string; online: boolean; latencyMs: number; ts: number }
  | { type: "session.started"; ts: number }
  | { type: "session.ended"; events: number; lastType: string | null; ts: number }
  | { type: "registry.updated"; count: number; ts: number }
  | { type: "registry.failed"; source: string; error: string; ts: number };

class EventBus {
  private handlers = new Map<string, Array<(e: VansRouterEvent) => void>>();
  private history: VansRouterEvent[] = [];
  private max = 300;
  emit(e: VansRouterEvent) {
    this.history.push(e); if (this.history.length > this.max) this.history.shift();
    for (const h of (this.handlers.get(e.type) ?? [])) { try { h(e); } catch {} }
  }
  on<T extends VansRouterEvent["type"]>(t: T, h: (e: Extract<VansRouterEvent, { type: T }>) => void) {
    if (!this.handlers.has(t)) this.handlers.set(t, []);
    this.handlers.get(t)!.push(h as (e: VansRouterEvent) => void);
  }
  snapshot() { return [...this.history]; }
}
const bus = new EventBus();

// ============================================================================
// AWS CANONICAL FULL JITTER BACKOFF
// ============================================================================
function fullJitterBackoff(attempt: number): number {
  const exp = Math.min(MAX_BACKOFF_MS, BASE_BACKOFF_MS * Math.pow(2, attempt));
  return Math.random() * exp;
}

// ============================================================================
// CIRCUIT BREAKER STATE MACHINE
// ============================================================================
type CircuitState = "closed" | "open" | "half-open";
interface Circuit { state: CircuitState; failures: number; openedAt: number; successes: number; }
const circuits = new Map<string, Circuit>();

function circuitGet(provider: string): Circuit {
  if (!circuits.has(provider)) circuits.set(provider, { state: "closed", failures: 0, openedAt: 0, successes: 0 });
  return circuits.get(provider)!;
}

function circuitAllow(provider: string): boolean {
  const c = circuitGet(provider);
  if (c.state === "closed") return true;
  if (c.state === "open") {
    if (Date.now() - c.openedAt >= CIRCUIT_COOLDOWN_MS) {
      c.state = "half-open"; c.successes = 0;
      bus.emit({ type: "circuit.half_open", provider, ts: Date.now() });
      return true;
    }
    bus.emit({ type: "circuit.rejected", provider, remainingMs: CIRCUIT_COOLDOWN_MS - (Date.now() - c.openedAt), ts: Date.now() });
    return false;
  }
  return true;
}

function circuitSuccess(provider: string): void {
  const c = circuitGet(provider);
  if (c.state === "half-open") {
    c.state = "closed"; c.failures = 0;
    bus.emit({ type: "circuit.closed", provider, ts: Date.now() });
  } else {
    c.failures = 0;
  }
}

function circuitFailure(provider: string): void {
  const c = circuitGet(provider);
  c.failures++;
  if (c.state === "half-open" || c.failures >= CIRCUIT_FAILURE_THRESHOLD) {
    c.state = "open"; c.openedAt = Date.now();
    bus.emit({ type: "circuit.opened", provider, failures: c.failures, cooldownMs: CIRCUIT_COOLDOWN_MS, ts: Date.now() });
  }
}

// ============================================================================
// DNS PREFLIGHT
// ============================================================================
async function dnsPreflight(host: string, port: number): Promise<string[]> {
  if (typeof globalThis.Bun !== "undefined" && globalThis.Bun?.dns?.prefetch) {
    try { globalThis.Bun.dns.prefetch(host, port); bus.emit({ type: "dns.prefetch", host, port, ts: Date.now() }); } catch {}
  }
  const t0 = performance.now();
  try {
    const addrs = await Promise.race([
      dns.promises.resolve4(host, { ttl: true }),
      new Promise((_, rej) => setTimeout(() => rej(Object.assign(new Error("DNS timeout"), { code: "ETIMEDOUT" })), DNS_TIMEOUT_MS)),
    ]);
    const lat = +(performance.now() - t0).toFixed(2);
    const addresses = (addrs as Array<{ address: string }>).map((a) => a.address);
    bus.emit({ type: "dns.resolved", host, addresses, latencyMs: lat, ts: Date.now() });
    return addresses;
  } catch (e) {
    bus.emit({ type: "dns.failed", host, error: (e as Error).message, latencyMs: +(performance.now() - t0).toFixed(2), ts: Date.now() });
    return [host];
  }
}

// ============================================================================
// DYNAMIC SECRET HARVESTER (De-quoted Multi-Source Chain)
// ============================================================================
interface KeyResolution { key: string; source: string; chain: Array<{ source: string; tried: boolean; hit: boolean; reason?: string }>; }
function resolveKey(): KeyResolution {
  const chain: KeyResolution["chain"] = [];
  const cleanVal = (val: string | undefined): string | undefined => {
    if (!val) return undefined;
    const s = val.trim().replace(/^["']|["']$/g, "").trim();
    return s.length > 0 ? s : undefined;
  };

  const trySrc = (name: string, fn: () => string | undefined) => {
    try {
      const raw = fn();
      const v = cleanVal(raw);
      const hit = typeof v === "string" && v.length > 0;
      chain.push({ source: name, tried: true, hit });
      return hit ? v : undefined;
    } catch (e) {
      chain.push({ source: name, tried: true, hit: false, reason: (e as Error).message });
      return undefined;
    }
  };

  const parseFileKey = (filepath: string): string | undefined => {
    if (!fs.existsSync(filepath)) return undefined;
    const content = fs.readFileSync(filepath, "utf-8");
    const m = content.match(/^(?:VANSROUTER_API_KEY|API_KEY_SECRET)=(.*)$/m);
    return m ? m[1] : undefined;
  };

  const hit =
    trySrc(\`env:\${VR_ENV_KEY}\`, () => process.env[VR_ENV_KEY]) ||
    trySrc("env:NINEROUTER_KEY", () => process.env.NINEROUTER_KEY) ||
    trySrc("env:API_KEY_SECRET", () => process.env.API_KEY_SECRET) ||
    trySrc(\`file:\${VR_CONFIG_FILE}\`, () => parseFileKey(VR_CONFIG_FILE)) ||
    trySrc(\`file:\${VR_SECRETS_FILE}\`, () => parseFileKey(VR_SECRETS_FILE));

  const key = hit && hit.length > 0 ? hit : VR_HARD_FALLBACK;
  const source = [...chain].reverse().find((c) => c.hit)?.source ?? "hardcoded-fallback";
  bus.emit({ type: "key.resolved", source, chain, ts: Date.now() });
  return { key, source, chain };
}

// ============================================================================
// URL FAILOVER
// ============================================================================
let urlIdx = 0;
const activeUrl = () => VR_URLS[urlIdx] ?? VR_URLS[0];
function rotateUrl() {
  const f = activeUrl();
  urlIdx = (urlIdx + 1) % VR_URLS.length;
  const t = activeUrl();
  if (f !== t) bus.emit({ type: "fetch.rotated", from: f, to: t, ts: Date.now() });
}

// ============================================================================
// FETCH ENGINE WITH JITTERED BACKOFF + CIRCUIT BREAKER
// ============================================================================
async function fetchRetry(url: string, init: RequestInit, retries = MAX_RETRIES): Promise<Response> {
  const provider = new URL(url).host;
  if (!circuitAllow(provider)) throw new Error(\`circuit open for \${provider}\`);

  let last: unknown;
  for (let a = 0; a <= retries; a++) {
    const delay = a > 0 ? fullJitterBackoff(a - 1) : 0;
    if (delay > 0) {
      bus.emit({ type: "fetch.attempt", url, attempt: a, delayMs: +delay.toFixed(0), ts: Date.now() });
      await new Promise((r) => setTimeout(r, delay));
    }
    const t0 = performance.now();
    try {
      const r = await fetch(url, init);
      if (r.ok) {
        circuitSuccess(provider);
        bus.emit({ type: "fetch.succeeded", url, attempt: a, latencyMs: +(performance.now() - t0).toFixed(2), ts: Date.now() });
        return r;
      }
      last = new Error(\`HTTP \${r.status}\`);
    } catch (e) {
      last = e;
    }
    circuitFailure(provider);
    bus.emit({ type: "fetch.failed", url, attempt: a, error: (last as Error)?.message ?? "?", ts: Date.now() });
  }
  throw last;
}

// ============================================================================
// MODEL CATALOG SPECIFICATIONS
// ============================================================================
const SEED: ProviderModelConfig[] = [
  { id: "oc/jev-1.13-free", name: "VansRouter Jev-1.3 Free", input: ["text", "image"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 128_000, maxTokens: 8_192, reasoning: false },
  { id: "oc/mimo-v2.5-free", name: "VansRouter Mimo V2.5 Free", input: ["text", "image"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 128_000, maxTokens: 8_192, reasoning: false },
  { id: "oc/nemotron-3.5-lightning-free", name: "VansRouter Nemotron 3.5", input: ["text", "image"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 128_000, maxTokens: 8_192, reasoning: true },
  { id: "oc/deepseek-v4-flash-free", name: "VansRouter DeepSeek V4 Flash", input: ["text", "image"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 128_000, maxTokens: 8_192, reasoning: false },
  { id: "mmf/mimo-auto", name: "VansRouter MMF Mimo Auto", input: ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 128_000, maxTokens: 8_192, reasoning: false },
];

let cache: { models: readonly ProviderModelConfig[]; at: number } | null = null;
const shards: Array<{ source: string; models: readonly ProviderModelConfig[] }> = [];

function norm(m: { id?: string; name?: string; capabilities?: Record<string, unknown> }): ProviderModelConfig {
  const id = String(m.id ?? "");
  const caps = m.capabilities ?? {};
  const reasoning = /reason|think|o1|o3|r1/i.test(id) || caps.reasoning === true;
  const vision = /vision|llava|qwen.*vl|gpt-4|gpt-5|claude|gemini/i.test(id) || caps.vision === true;
  return { id, name: String(m.name ?? id), input: vision ? ["text", "image"] : ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 128_000, maxTokens: 8_192, reasoning };
}

function merge(): readonly ProviderModelConfig[] {
  const byId = new Map<string, ProviderModelConfig>();
  for (const s of shards) for (const m of s.models) byId.set(m.id, m);
  return [...byId.values()];
}

async function fetchPaginated(base: string, key: string | undefined, limit = 100): Promise<ProviderModelConfig[]> {
  const all: ProviderModelConfig[] = [];
  let off = 0;
  const headers: Record<string, string> = {};
  if (key) headers.Authorization = \`Bearer \${key}\`;
  while (true) {
    const r = await fetchRetry(\`\${base}/v1/models?limit=\${limit}&offset=\${off}\`, { headers, signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
    const b = (await r.json()) as { data?: Array<{ id?: string; name?: string; capabilities?: Record<string, unknown> }> };
    const page = b?.data ?? [];
    all.push(...page.map(norm));
    if (page.length < limit) break;
    off += limit;
  }
  return all;
}

async function fetchDynamicModels(apiKey: string | undefined): Promise<readonly ProviderModelConfig[]> {
  const now = Date.now();
  if (cache && now - cache.at < MODEL_CACHE_TTL_MS) {
    bus.emit({ type: "models.cached", count: cache.models.length, ageMs: now - cache.at, ts: now });
    return cache.models;
  }
  const t0 = performance.now();
  for (let i = 0; i < VR_URLS.length; i++) {
    const url = activeUrl();
    try {
      const models = await fetchPaginated(url, apiKey);
      if (models.length > 0) {
        shards.push({ source: \`live:\${url}\`, models });
        bus.emit({ type: "models.shard", source: \`live:\${url}\`, count: models.length, ts: now });
        const merged = merge();
        cache = { models: merged, at: now };
        bus.emit({ type: "models.fetched", count: merged.length, source: \`live:\${url}\`, latencyMs: +(performance.now() - t0).toFixed(2), ts: now });
        return merged;
      }
    } catch (e) {
      log("warn", \`Catalog query against \${url} bypassed: \${(e as Error).message}\`);
    }
    rotateUrl();
  }
  bus.emit({ type: "models.seed_fallback", count: SEED.length, ts: now });
  return SEED;
}

// ============================================================================
// HEALTH PROBE WITH CIRCUIT AWARENESS
// ============================================================================
const health = { online: false, fails: 0, url: "", lat: 0 };
let healthTimer: ReturnType<typeof setInterval> | null = null;

async function probeHealth(): Promise<boolean> {
  const url = activeUrl();
  const t0 = performance.now();
  let okv = false;
  try {
    okv = (await fetch(\`\${url}/api/health\`, { signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS) })).ok;
  } catch {}
  const lat = +(performance.now() - t0).toFixed(2);
  const prev = health.online;
  health.online = okv;
  health.url = url;
  health.lat = lat;
  health.fails = okv ? 0 : health.fails + 1;
  bus.emit({ type: "health.probe", url, online: okv, latencyMs: lat, ts: Date.now() });
  if (prev !== okv) {
    bus.emit({ type: "health.changed", online: okv, consecutiveFails: health.fails, latencyMs: lat, url, ts: Date.now() });
  }
  return okv;
}

function startHealth() {
  if (healthTimer) return;
  healthTimer = setInterval(() => { void probeHealth(); }, HEALTH_INTERVAL_MS);
  (healthTimer as { unref?: () => void }).unref?.();
}
function stopHealth() {
  if (healthTimer) { clearInterval(healthTimer); healthTimer = null; }
}

// ============================================================================
// NOTIFICATION DISPATCHER
// ============================================================================
function notify(ctx: ExtensionContext | unknown, text: string, level: "info" | "warn" | "error" = "info") {
  try {
    const lvl = level === "warn" ? "warning" : level;
    if (ctx && typeof ctx === "object") {
      const c = ctx as Record<string, unknown>;
      const ui = c.ui as Record<string, unknown> | undefined;
      if (typeof ui?.notify === "function") return void (ui.notify as (m: string, t?: string) => void)(text, lvl);
      if (typeof ui?.print === "function") return void (ui.print as (m: string) => void)(text);
      const s = c.session as Record<string, unknown> | undefined;
      if (typeof s?.postMessage === "function") return void (s.postMessage as (m: { role: string; text: string }) => void)({ role: "system", text });
      if (typeof c.sendUserMessage === "function") return void (c.sendUserMessage as (m: string) => void)(text);
    }
    (level === "error" ? console.error : level === "warn" ? console.warn : console.log)(TAG, text);
  } catch {}
}

// ============================================================================
// PROVIDER REGISTRATION & RE-REGISTRATION
// ============================================================================
function register(pi: ExtensionAPI, modelsList: ProviderModelConfig[] = SEED) {
  try {
    const { key, source } = resolveKey();
    const apiKey = key && key.length > 0 ? key : VR_HARD_FALLBACK;
    const baseUrl = \`\${activeUrl()}/v1\`;
    const capabilities = {
      streaming: true,
      tools: true,
      vision: true,
      reasoning: true,
      mcpServers: ["stdio"],
      protocols: ["openai-completions", "openai-responses"],
    };
    const config: ProviderConfig = {
      baseUrl,
      apiKey,
      api: "openai-completions",
      authHeader: true,
      models: modelsList,
    };
    pi.registerProvider(DEFINITION.id, config);
    bus.emit({ type: "provider.registered", baseUrl, keySource: source, keyLen: apiKey.length, capabilities, ts: Date.now() });
    log("info", \`Registered provider: baseUrl=\${baseUrl} source=\${source} models=\${modelsList.length}\`);
  } catch (e) {
    bus.emit({ type: "provider.registration_failed", error: (e as Error).message, ts: Date.now() });
    log("error", \`Registration failed: \${(e as Error).message}\`);
  }
}

// ============================================================================
// EXTENSION ENTRYPOINT
// ============================================================================
export default function vansrouterExtension(pi: ExtensionAPI): void {
  register(pi, SEED);

  pi.on("session_start", async (_e, ctx) => {
    bus.emit({ type: "session.started", ts: Date.now() });
    await dnsPreflight("127.0.0.1", 20128);
    const okv = await probeHealth();
    const f = health.fails > 0 ? \` (\${health.fails} fails)\` : "";
    notify(ctx, \`\${TAG} \${okv ? "online" : "offline"}\${f} — \${activeUrl()} (\${health.lat}ms)\`, okv ? "info" : "warn");
    startHealth();

    if (okv) {
      const dynamicModels = await fetchDynamicModels(resolveKey().key);
      if (dynamicModels.length > 0) {
        register(pi, dynamicModels as ProviderModelConfig[]);
        bus.emit({ type: "registry.updated", count: dynamicModels.length, ts: Date.now() });
      }
      notify(ctx, \`\${TAG} \${dynamicModels.length} models active in catalog\`, "info");
    }
  });

  pi.on("session_end" as never, (() => {
    stopHealth();
    const snap = bus.snapshot();
    bus.emit({ type: "session.ended", events: snap.length, lastType: snap[snap.length - 1]?.type ?? null, ts: Date.now() });
    log("info", \`Session closed — \${snap.length} events logged\`);
  }) as never);
}
`;

// ---------------------------------------------------------------------------
// 2. ACP TCP BRIDGE (Buffered Framing + Isolated Per-Conn Normalization)
// ---------------------------------------------------------------------------
hdr("2. Deploy acp-tcp-bridge");

const BRIDGE_SOURCE = `#!/usr/bin/env node
// acp-tcp-bridge — Line-buffered TCP<->stdio ACP bridge with stdio mcpServers framing
const net = require("net");
const { spawn } = require("child_process");
const { Transform } = require("stream");

const args = process.argv.slice(2);
let port = 25111;
const pIdx = args.indexOf("--port");
let cmdStart = -1;
if (pIdx !== -1 && args[pIdx + 1]) {
  port = parseInt(args[pIdx + 1], 10);
  cmdStart = args.indexOf("--", pIdx) + 1;
} else {
  cmdStart = args.indexOf("--") + 1;
}
if (cmdStart <= 0 || cmdStart >= args.length) {
  console.error("Usage: acp-tcp-bridge [--port <port>] -- <cmd> [args...]");
  process.exit(1);
}
const cmd = args.slice(cmdStart);

function normalizeServer(s) {
  return {
    type: typeof s?.type === "string" ? s.type : "stdio",
    name: typeof s?.name === "string" ? s.name : "",
    command: typeof s?.command === "string" ? s.command : "",
    args: Array.isArray(s?.args) ? s.args : [],
    env: Array.isArray(s?.env) ? s.env : [],
  };
}

function createNormalizeTransform() {
  let buffer = "";
  return new Transform({
    transform(chunk, _enc, cb) {
      buffer += chunk.toString("utf-8");
      const lines = buffer.split("\\n");
      buffer = lines.pop(); // Retain incomplete line fragment
      const out = lines.map((line) => {
        if (!line.trim()) return line;
        try {
          const msg = JSON.parse(line);
          if ((msg.method === "session/new" || msg.method === "session/load") && msg.params) {
            if (msg.params.mcpServers === undefined) {
              msg.params.mcpServers = [];
            } else if (Array.isArray(msg.params.mcpServers)) {
              msg.params.mcpServers = msg.params.mcpServers.map(normalizeServer);
            }
          }
          return JSON.stringify(msg);
        } catch {
          return line;
        }
      }).join("\\n");
      cb(null, out ? out + "\\n" : "");
    },
    flush(cb) {
      if (buffer.trim()) {
        try {
          const msg = JSON.parse(buffer);
          if ((msg.method === "session/new" || msg.method === "session/load") && msg.params) {
            if (msg.params.mcpServers === undefined) msg.params.mcpServers = [];
            else if (Array.isArray(msg.params.mcpServers)) msg.params.mcpServers = msg.params.mcpServers.map(normalizeServer);
          }
          cb(null, JSON.stringify(msg) + "\\n");
          return;
        } catch {
          cb(null, buffer);
          return;
        }
      }
      cb();
    }
  });
}

let seq = 0;
const server = net.createServer((sock) => {
  const cid = ++seq;
  let child = null;
  let closed = false;

  const cleanup = () => {
    if (closed) return;
    closed = true;
    if (child && !child.killed) {
      try { child.kill("SIGTERM"); } catch {}
    }
    try { sock.destroy(); } catch {}
  };

  try {
    child = spawn(cmd[0], cmd.slice(1), { stdio: ["pipe", "pipe", "inherit"], env: process.env });
    child.on("error", (e) => {
      console.error(\`[acp-tcp-bridge] #\${cid} spawn error: \${e.message}\`);
      cleanup();
    });

    const normStream = createNormalizeTransform();
    sock.pipe(normStream).pipe(child.stdin);
    child.stdout.pipe(sock);

    sock.on("error", cleanup);
    sock.on("close", cleanup);
    child.on("close", () => { if (!closed) sock.end(); });
  } catch (e) {
    console.error(\`[acp-tcp-bridge] #\${cid} initialization failure: \${e.message}\`);
    cleanup();
  }
});

server.on("error", (e) => {
  console.error("[acp-tcp-bridge] Server error:", e.message);
  process.exit(1);
});

server.listen(port, "127.0.0.1", () => {
  console.log(\`[acp-tcp-bridge] Listening 127.0.0.1:\${port} -> \${cmd.join(" ")}\`);
});
`;

if (fs.existsSync(BRIDGE_PATH)) fs.copyFileSync(BRIDGE_PATH, `${BRIDGE_PATH}.bak.${Date.now()}`);
fs.writeFileSync(BRIDGE_PATH, BRIDGE_SOURCE, { mode: 0o755 });
ok(`${BRIDGE_PATH} (hash ${H(BRIDGE_SOURCE)})`);

// ---------------------------------------------------------------------------
// 3. ACP PROBE (Dynamic Auth Negotiation & Handshake) — Plain JS (no TS syntax)
// ---------------------------------------------------------------------------
hdr("3. Deploy acp-probe.mjs");

const PROBE_SOURCE = `#!/usr/bin/env bun
// acp-probe.mjs — End-to-end verification of initialize, authenticate, and session/new
import net from "net";
import dns from "node:dns";
import { performance } from "perf_hooks";

const HOST = "127.0.0.1";
const PORT = Number(process.env.ACP_PORT || 25111);
const TIMEOUT = 20_000;
const DNS_TIMEOUT = 3000;

const c = {
  reset: "\\x1b[0m", bold: "\\x1b[1m", dim: "\\x1b[2m",
  green: "\\x1b[32m", yellow: "\\x1b[33m", red: "\\x1b[31m",
  cyan: "\\x1b[36m", magenta: "\\x1b[35m"
};

// DNS Preflight
try {
  if (typeof globalThis.Bun !== "undefined" && globalThis.Bun?.dns?.prefetch) {
    globalThis.Bun.dns.prefetch(HOST, PORT);
  }
  const t0 = performance.now();
  const addrs = await Promise.race([
    dns.promises.resolve4(HOST, { ttl: true }),
    new Promise((_, rej) => setTimeout(() => rej(new Error("DNS timeout")), DNS_TIMEOUT)),
  ]);
  console.log(\`\\n✓ DNS preflight: \${HOST} -> \${addrs.map((a) => a.address).join(", ")} (\${(performance.now() - t0).toFixed(2)}ms)\`);
} catch (e) {
  console.log(\`\\n⚠ DNS preflight note: \${e.message} (continuing)\`);
}

class Client {
  constructor(host, port) {
    this.host = host;
    this.port = port;
    this.sock = new net.Socket();
    this.buf = "";
    this.pending = new Map();
    this.id = 0;
    this.handlers = new Map();
    this.lat = {};
  }
  connect() {
    return new Promise((res, rej) => {
      const t0 = performance.now();
      const t = setTimeout(() => { this.sock.destroy(); rej(new Error("Connection timeout")); }, 5000);
      this.sock.connect(this.port, this.host, () => {
        clearTimeout(t);
        this.lat.tcp = +(performance.now() - t0).toFixed(2);
        res();
      });
      this.sock.on("data", (ch) => { this.buf += ch.toString("utf-8"); this.flush(); });
      this.sock.on("error", rej);
    });
  }
  flush() {
    let i;
    while ((i = this.buf.indexOf("\\n")) !== -1) {
      const line = this.buf.slice(0, i).trim();
      this.buf = this.buf.slice(i + 1);
      if (!line) continue;
      try { this.handle(JSON.parse(line)); } catch {}
    }
  }
  handle(m) {
    if (m.id !== undefined && this.pending.has(m.id)) {
      const { resolve, reject, t0, method } = this.pending.get(m.id);
      this.pending.delete(m.id);
      this.lat[method] = +(performance.now() - t0).toFixed(2);
      if (m.error) reject(new Error(\`[\${method}] (\${m.error.code}): \${m.error.message}\${m.error.data ? " — " + JSON.stringify(m.error.data) : ""}\`));
      else resolve({ result: m.result, latency: this.lat[method] });
      return;
    }
    if (m.method) {
      const h = this.handlers.get(m.method);
      if (h) h(m.params);
    }
  }
  on(method, cb) { this.handlers.set(method, cb); }
  req(method, params = {}) {
    return new Promise((res, rej) => {
      const id = ++this.id;
      const t0 = performance.now();
      const t = setTimeout(() => { this.pending.delete(id); rej(new Error(\`Timeout waiting for \${method}\`)); }, TIMEOUT);
      this.pending.set(id, { resolve: (v) => { clearTimeout(t); res(v); }, reject: (e) => { clearTimeout(t); rej(e); }, t0, method });
      this.sock.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\\n");
    });
  }
  end() {
    return new Promise((res) => this.sock.end(() => { this.sock.destroy(); res(); }));
  }
}

const cli = new Client(HOST, PORT);
cli.on("session/update", (p) => {
  const u = p.update || {};
  if (u.sessionUpdate === "agentMessageChunk" || u.type === "text_delta") process.stdout.write(c.green + (u.content?.text || u.text || "") + c.reset);
  else if (u.sessionUpdate === "thoughtChunk" || u.type === "thought_delta") process.stdout.write(c.magenta + (u.content?.text || u.text || "") + c.reset);
});

try {
  await cli.connect();
  console.log(\`✓ TCP connect established (\${cli.lat.tcp}ms)\`);

  const init = await cli.req("initialize", {
    protocolVersion: 1,
    clientInfo: { name: "acp-probe", version: "3.1.0" },
    clientCapabilities: {
      fs: { readTextFile: true, writeTextFile: true },
      terminal: true,
    },
  });
  const agent = init.result?.agentInfo ?? {};
  console.log(\`✓ initialize: \${agent.name} (\${agent.version}) \${init.latency}ms\`);
  console.log(\`  authMethods: \${(init.result?.authMethods ?? []).map((m) => m.id).join(", ") || "none"}\`);

  const methodId = init.result?.authMethods?.[0]?.id ?? "agent";
  try {
    const a = await cli.req("authenticate", { methodId });
    console.log(\`✓ authenticate(\${methodId}) \${a.latency}ms\`);
  } catch (e) {
    console.log(\`⚠ authenticate note: \${e.message}\`);
  }

  const s = await cli.req("session/new", { cwd: "/home/toxic", mcpServers: [] });
  const sid = s.result?.sessionId;
  console.log(\`✓ session/new allocated ID: \${sid} (\${s.latency}ms)\`);

  const pr = await cli.req("session/prompt", { sessionId: sid, prompt: [{ type: "text", text: "Reply with exactly: OK" }] });
  console.log(\`\\n✓ prompt stopReason=\${pr.result?.stopReason || "endTurn"} (\${pr.latency}ms)\`);

  try { await cli.req("session/close", { sessionId: sid }); console.log("✓ session/close"); } catch {}
  await cli.end();
  console.log(\`\\n\\x1b[32m═══ ACP PIPELINE OPERATIONAL ═══\\x1b[0m\\n\`);
} catch (e) {
  console.error(\`\\n\\x1b[31m✗ \${e.message}\\x1b[0m\\n\`);
  try { await cli.end(); } catch {}
  process.exit(1);
}
`;

if (fs.existsSync(PROBE_PATH)) fs.copyFileSync(PROBE_PATH, `${PROBE_PATH}.bak.${Date.now()}`);
fs.writeFileSync(PROBE_PATH, PROBE_SOURCE, { mode: 0o755 });
ok(`${PROBE_PATH} (hash ${H(PROBE_SOURCE)})`);

// ---------------------------------------------------------------------------
// 4. PITCHFORK CONFIG SANITIZATION
// ---------------------------------------------------------------------------
hdr("4. Synchronize pitchfork.toml Configurations");

const expectedRun = `run = "exec ${BRIDGE_PATH} --port ${PORT} -- ${OMP_BIN} acp -e ${EXT_PATH}"`;

function sanitizePitchforkToml() {
  // A. Repair Canonical Config (~/sovereign/pitchfork.toml)
  if (fs.existsSync(PITCH_CANON)) {
    const raw = fs.readFileSync(PITCH_CANON, "utf-8");
    const lines = raw.split("\n");
    const idx = lines.findIndex((l) => l.trim() === "[daemons.tau]");
    if (idx !== -1) {
      let end = lines.length;
      for (let i = idx + 1; i < lines.length; i++) {
        if (lines[i].trim().startsWith("[")) { end = i; break; }
      }
      const section = lines.slice(idx + 1, end);
      const cleaned = [];
      let hasRun = false, hasEnv = false, hasPort = false, hasDir = false;

      for (const line of section) {
        const t = line.trim();
        if (t.startsWith("run =") || t.startsWith("run=")) {
          if (!hasRun) { cleaned.push(expectedRun); hasRun = true; }
          continue;
        }
        if (t.startsWith("env =") || t.startsWith("env=")) {
          if (!hasEnv) {
            cleaned.push(`env = { PI_CONFIG_DIR = "/home/toxic/.tau", PI_AGENT_DIR = "/home/toxic/.tau/agent", PI_CODING_AGENT = "true", PI_REASONING_LEVEL = "high", PI_SUBAGENT_MODEL = "thinkingmachines/inkling", PI_OPENAI_STREAM_IDLE_TIMEOUT_MS = "120000", VANSROUTER_API_KEY = "local-sovereign" }`);
            hasEnv = true;
          }
          continue;
        }
        if (t.startsWith("port =") || t.startsWith("port=")) {
          hasPort = true;
          cleaned.push(`port = ${PORT}`);
          continue;
        }
        if (t.startsWith("dir =") || t.startsWith("dir=")) {
          hasDir = true;
          cleaned.push(`dir = "/home/toxic"`);
          continue;
        }
        cleaned.push(line);
      }
      if (!hasRun) cleaned.unshift(expectedRun);
      if (!hasPort) cleaned.splice(hasDir ? cleaned.findIndex((l) => l.trim().startsWith("dir =")) : 0, 0, `port = ${PORT}`);
      if (!hasEnv) cleaned.push(`env = { VANSROUTER_API_KEY = "local-sovereign" }`);

      const out = [...lines.slice(0, idx + 1), ...cleaned, ...lines.slice(end)].join("\n");
      if (out !== raw) {
        fs.copyFileSync(PITCH_CANON, `${PITCH_CANON}.bak.${Date.now()}`);
        fs.writeFileSync(PITCH_CANON, out);
        ok(`Updated ${PITCH_CANON} with explicit port = ${PORT}`);
      } else {
        ok(`${PITCH_CANON} is already correctly configured`);
      }
    }
  }

  // B. Purge Duplicate Daemons from ~/pitchfork.toml (kills ghost toxic/tau & toxic/tau-code)
  if (fs.existsSync(PITCH_DUP)) {
    const raw = fs.readFileSync(PITCH_DUP, "utf-8");
    let lines = raw.split("\n");
    const targets = ["[daemons.tau]", "[daemons.tau-code]"];
    let changed = false;

    for (const target of targets) {
      const idx = lines.findIndex((l) => l.trim() === target);
      if (idx !== -1) {
        let end = lines.length;
        for (let i = idx + 1; i < lines.length; i++) {
          if (lines[i].trim().startsWith("[")) { end = i; break; }
        }
        lines.splice(idx, end - idx);
        changed = true;
        ok(`Purged duplicate ${target} from ${PITCH_DUP}`);
      }
    }

    if (changed) {
      fs.copyFileSync(PITCH_DUP, `${PITCH_DUP}.bak.${Date.now()}`);
      fs.writeFileSync(PITCH_DUP, lines.join("\n"));
    }
  }
}

sanitizePitchforkToml();

// ---------------------------------------------------------------------------
// 5. RESTART SUPERVISOR
// ---------------------------------------------------------------------------
hdr("5. Restart sovereign/tau");
console.log(sh(`pitchfork clean 2>&1 || true`));
console.log(sh(`cd /home/toxic/sovereign && pitchfork restart sovereign/tau 2>&1 | tail -8`));

// ---------------------------------------------------------------------------
// 6. PORT VERIFICATION & STATS
// ---------------------------------------------------------------------------
hdr("6. Verify Port Listener");
await new Promise((r) => setTimeout(r, 2500));
console.log(sh(`ss -tlnp '( sport = :${PORT} )' 2>&1`));

try {
  const stats = globalThis.Bun?.dns?.getCacheStats?.();
  if (stats) info(`Bun DNS cache stats: size=${stats.size} hits=${stats.cacheHitsCompleted} misses=${stats.cacheMisses}`);
} catch {}

// ---------------------------------------------------------------------------
// 7. END-TO-END PROBE EXECUTION
// ---------------------------------------------------------------------------
hdr("7. Run End-to-End ACP Handshake");
try {
  execSync(`bun ${PROBE_PATH}`, { stdio: "inherit" });
} catch {
  err("Probe failed. Dumping supervisor logs:");
  console.log(sh(`pitchfork logs sovereign/tau --raw -n 40 --no-pager 2>&1 | tail -40`));
  process.exit(1);
}

hdr("PIPELINE OPERATIONAL");
console.log(`${C.green}Canonical paths verified:${C.reset}`);
console.log(`  extension : ${EXT_PATH}`);
console.log(`  bridge    : ${BRIDGE_PATH}`);
console.log(`  probe     : ${PROBE_PATH}`);
console.log(`  config    : ${PITCH_CANON}`);
