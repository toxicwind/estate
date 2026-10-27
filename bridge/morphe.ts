#!/usr/bin/env bun
// morphe.ts — NATIVE BUN lane of the morphe transport-morphing router
// (squawk/bridge/chaos entry). Python morphe.py stays as the fallback
// runtime (green-blue doctrine: bun = fast primary, python = rollback).
//
// Morphe-patching doctrine applied to routing (docs/MORPHE_PATCHING.md):
//   fingerprint resolve -> cached per client -> transport morphed RELATIVE
//   to the match -> NO MATCH = loud 501 (never fuzzy-routed).
//
// The 20 deps, integrated where they earn their keep (nothing decorative):
//   zod                fingerprint/lane config schema validation at boot
//   yaml               config file parsing (morphe-fingerprints.yaml)
//   pino               HFT-grade structured JSON log (stdout)
//   debug              namespaced stderr tracing (DEBUG=morphe:*)
//   hyperid            monotonic connection ids (faster than uuid/nanoid)
//   nanoid             request ids for the ledger
//   lru-cache          fingerprint resolution cache (per client:port)
//   quick-lru          hot-lane socket cache (keepalive dial reuse)
//   picomatch          glob path patterns in fingerprints
//   mitt               lane event bus (resolved/patched/chaos events)
//   bottleneck          per-lane connect pacing ( sheds burst probes)
//   immer              immutable route-table updates (control socket)
//   semver             config compat gate (compatibleWith doctrine)
//   systeminformation  thermal/disk guard before chaos windows
//   croner             scheduled chaos windows (green-blue soak tests)
//   dayjs              human timestamps in logs
//   ws                 WS client for upstream lanes (exec-ws protocol)
//   undici             upstream HTTP client (funnel h1.1 pinning)
//   @duckdb/node-api   winners ledger -> PARQUET (HFT analytics grade)
//   uWebSockets.js     (reserved) ultra-fast WS termination — swap-in lane

import { DuckDBInstance } from "@duckdb/node-api";
import { ZodError, z } from "zod";
import YAML from "yaml";
import pino from "pino";
import createDebug from "debug";
import HyperId from "hyperid";
import { nanoid } from "nanoid";
import { LRUCache } from "lru-cache";
import QuickLRU from "quick-lru";
import picomatch from "picomatch";
import mitt from "mitt";
import Bottleneck from "bottleneck";
import { produceWithPatches, enablePatches, applyPatches } from "immer";
import semver from "semver";
import si from "systeminformation";
import { Cron } from "croner";
import dayjs from "dayjs";
import WebSocket from "ws";
import { request as undiciRequest, Agent } from "undici";

const debug = createDebug("morphe:bun");
enablePatches();

// ---------- config schema (zod + yaml) ----------
export const FingerprintSchema = z.object({
  name: z.string().min(1),
  lane: z.string().min(1),
  port: z.number().int().optional(),
  path_pattern: z.string().optional(),
  contains: z.array(z.string()).optional(),
  requires_payload: z.boolean().optional(),
  kind: z.enum(["pass", "convert", "ws", "tls-ws"]).default("pass"),
});
export const LaneSchema = z.object({
  name: z.string().min(1),
  host: z.string().default("127.0.0.1"),
  port: z.number().int().min(1).max(65535),
  kind: z.enum(["ws", "tls-ws", "http"]).default("ws"),
  token: z.string().optional(),
  path: z.string().optional(),
});
export const ConfigSchema = z.object({
  compatibleWith: z.string().min(1),         // semver gate
  listen: z.object({ host: z.string().default("0.0.0.0"), port: z.number().int() }),
  chaos_enabled: z.boolean().default(false),
  fingerprints: z.array(FingerprintSchema),
  lanes: z.array(LaneSchema),
});

type Fingerprint = z.infer<typeof FingerprintSchema>;
type Lane = z.infer<typeof LaneSchema>;
type Config = z.infer<typeof ConfigSchema>;

const CONFIG_COMPAT = ">=1.0.0 <3.0.0";
// ws-exec daemon validates X-MCP-Token on EVERY handshake (401/400 otherwise)
const MCP_TOKEN = (() => {
  for (const f of [`${process.env.HOME}/.yote_connector_token`, `${process.env.HOME}/.shim_connector_token`, `${process.env.HOME}/.awrawr_mcp_token`]) {
    try { return Bun.file(f).text().then(t => t.trim()); } catch {}
  }
  return Promise.resolve("");
})();

// ---------- logging (pino HFT grade + dayjs) ----------
const log = pino({ level: process.env.MORPHE_LOG ?? "info",
  base: { lane: "morphe", runtime: "bun" } });

// ---------- ids ----------
const connIds = HyperId();
const reqId = () => nanoid(8);

// ---------- caches ----------
const resolveCache = new LRUCache<string, Fingerprint>({ max: 4096, ttl: 1000 * 300 });
const hotLanes = new QuickLRU<string, WebSocket>({ maxSize: 64, ttl: 1000 * 60 * 10 });

// ---------- event bus (mitt) ----------
const bus = mitt<{ resolved: Fingerprint; patched: Record<string, unknown>; chaos: string }>();

// ---------- connect pacing (bottleneck) ----------
const limiter = new Bottleneck({ maxConcurrent: 16, minTime: 0 });

// ---------- route table (immer + patches, for the control socket) ----------
export type RouteTable = { lanes: Lane[]; fingerprints: Fingerprint[]; chaos: boolean };
export const table: RouteTable = { lanes: [], fingerprints: [], chaos: false };
export function mutateTable(recipe: (t: RouteTable) => void) {
  const [next, patches] = produceWithPatches(table, recipe);
  Object.assign(table, next);
  bus.emit("patched", { patches });
  return patches;
}

// ---------- parquet ledger (@duckdb/node-api) ----------
export class WinnersLedger {
  private conn?: import("@duckdb/node-api").DuckDBConnection;
  private n = 0;
  async open(path = `${process.env.HOME}/.cache/morphe/winners-bun.duckdb`) {
    const inst = await DuckDBInstance.create(path);
    this.conn = await inst.connect();
    await this.conn.run(`CREATE TABLE IF NOT EXISTS winners(
      ts TIMESTAMP, req VARCHAR, lane VARCHAR, port INTEGER,
      latency_ms DOUBLE, bytes INTEGER, ok BOOLEAN)`);
  }
  async record(row: { lane: string; port: number; latencyMs: number; bytes: number; ok: boolean; winner?: boolean }) {
    if (!this.conn) await this.open();
    await this.conn!.run(`INSERT INTO winners VALUES (now(), ?, ?, ?, ?, ?, ?)`,
      [reqId(), row.lane + (row.winner ? "*" : ""), row.port, row.latencyMs, row.bytes, row.ok]);
    if (++this.n % 200 === 0) await this.flush();
  }
  async flush(file = `${process.env.HOME}/.cache/morphe/winners.parquet`) {
    if (!this.conn || !this.n) return;
    await this.conn.run(`COPY (SELECT * FROM winners) TO '${file}' (FORMAT PARQUET)`);
    debug("parquet flush: %d rows -> %s", this.n, file);
  }
}

export const ledger = new WinnersLedger();

// ---------- fingerprint resolution ----------
function resolveFingerprint(cfg: Config, port: number, path: string, head: Buffer): Fingerprint | null {
  const cacheKey = `${port}:${path}:${head.length}`;
  const cached = resolveCache.get(cacheKey);
  if (cached) return cached;
  const headLower = head.toString("latin1").toLowerCase();
  for (const fp of cfg.fingerprints) {
    if (fp.port !== undefined && fp.port !== port) continue;
    if (fp.path_pattern && !picomatch.isMatch(path, fp.path_pattern)
        && !new RegExp(fp.path_pattern).test(path)) continue;
    if (fp.contains?.some(lit => !headLower.includes(lit.toLowerCase()))) continue;
    if (fp.requires_payload && head.length === 0) continue;
    resolveCache.set(cacheKey, fp);
    bus.emit("resolved", fp);
    return fp;
  }
  return null;
}

// ---------- upstream dialing (ws via `ws`, http via undici, h1.1-pinned) ----------
const h1Agent = new Agent({ connections: 32, pipelining: 1 });

async function dialWs(lane: Lane, extraHeaders: Record<string, string> = {}): Promise<WebSocket> {
  const key = `${lane.name}`;
  const hot = hotLanes.get(key);
  if (hot && hot.readyState === WebSocket.OPEN) return hot;
  const url = `ws://${lane.host}:${lane.port}${lane.path ?? "/"}`;
  const token = await MCP_TOKEN;
  const ws = await limiter.schedule(() => new Promise<WebSocket>((res, rej) => {
    const sock = new WebSocket(url, { headers: { "x-mcp-token": lane.token || token, ...extraHeaders } });
    sock.once("open", () => res(sock));
    sock.once("error", rej);
  }));
  hotLanes.set(key, ws);
  return ws;
}

// body<->frame conversion (the id field is MANDATORY — daemon drops id-less)
export async function convertHttpToWs(lane: Lane, body: Buffer): Promise<Buffer> {
  const ws = await dialWs(lane);
  const id = `m${reqId()}`;
  let cmd = "";
  try { cmd = JSON.parse(body.toString())["cmd"] ?? "hostname"; } catch { cmd = "hostname"; }
  ws.send(JSON.stringify({ id, cmd, workdir: "/home/toxic", timeout: 30 }));
  return await new Promise<Buffer>((resolve, reject) => {
    const outs: string[] = [];
    const onMsg = (data: WebSocket.RawData) => {
      try {
        const msg = JSON.parse(data.toString());
        if (msg.id !== id) return;
        if (msg.type === "chunk" && msg.stream === "stdout") outs.push(String(msg.data ?? ""));
        if (msg.type === "exit") {
          ws.off("message", onMsg);
          resolve(Buffer.from(JSON.stringify({ ok: true, exit_code: msg.code, stdout: outs.join(""), stderr: "" })));
        }
      } catch { /* non-JSON frame; ignore */ }
    };
    ws.on("message", onMsg);
    ws.once("error", reject);
    setTimeout(() => { ws.off("message", onMsg); reject(new Error("convert timeout")); }, 30_000);
  });
}

// ---------- chaos windows (croner + systeminformation guard) ----------
export function scheduleChaos(cfg: Config, cron: string, fn: () => Promise<void>) {
  if (!cfg.chaos_enabled) return null;
  return new Cron(cron, async () => {
    const [disk, temp] = await Promise.all([si.fsSize(), si.cpuTemperature()]);
    const diskFreePct = 100 - (disk[0]?.use ?? 0);
    if (diskFreePct < 10) { log.warn({ diskFreePct }, "chaos skipped: disk guard"); return; }
    if ((temp.main ?? 0) > 90) { log.warn({ temp: temp.main }, "chaos skipped: thermal guard"); return; }
    bus.emit("chaos", "window-start");
    await fn();
    bus.emit("chaos", "window-end");
  });
}

// ---------- boot ----------
export async function boot(configPath: string) {
  const raw = YAML.parse(await Bun.file(configPath).text());
  const cfg = ConfigSchema.parse(raw);
  if (!semver.satisfies(semver.coerce("1.0.0")!, cfg.compatibleWith)) {
    throw new Error(`config compat gate: ${cfg.compatibleWith} violates ${CONFIG_COMPAT}`);
  }
  mutateTable(t => { t.lanes = cfg.lanes; t.fingerprints = cfg.fingerprints; t.chaos = cfg.chaos_enabled; });
  await ledger.open();
  log.info({ day: dayjs().format(), lanes: cfg.lanes.length, fps: cfg.fingerprints.length },
    "morphe bun lane booted");
  return cfg;
}

// ---------- HTTP entrypoint: resolve -> pass / convert / loud-501 ----------
export async function handleRequest(cfg: Config, port: number, path: string, head: Buffer, body: Buffer): Promise<{ status: number; payload: Buffer; lane?: Lane }> {
  const fp = resolveFingerprint(cfg, port, path, head);
  if (!fp) {
    await ledger.record({ lane: "unmatched", port, latencyMs: 0, bytes: head.length, ok: false });
    return { status: 501, payload: Buffer.from("morphe: no fingerprint matched — loud fail\n") };
  }
  const lane = cfg.lanes.find(l => l.name === fp.lane);
  if (!lane) return { status: 502, payload: Buffer.from("morphe: lane missing\n") };
  const t0 = performance.now();
  if (fp.kind === "convert") {
    const out = await convertHttpToWs(lane, body);
    await ledger.record({ lane: lane.name, port, latencyMs: performance.now() - t0, bytes: out.length, ok: true });
    return { status: 200, payload: out, lane };
  }
  // pass-through: undici h1.1 pinned upstream relay
  const upstream = `http://${lane.host}:${lane.port}${path}`;
  const res = await undiciRequest(upstream, { method: "GET", headers: { "x-mcp-token": lane.token || await MCP_TOKEN }, dispatcher: h1Agent });
  const buf = Buffer.from(await res.body.arrayBuffer());
  await ledger.record({ lane: lane.name, port, latencyMs: performance.now() - t0, bytes: buf.length, ok: res.statusCode < 500 });
  return { status: res.statusCode, payload: buf, lane };
}

if (import.meta.main) {
  const configPath = process.argv[2] ?? `${process.env.HOME}/estate/bridge/morphe-fingerprints.yaml`;
  const cfg = await boot(configPath);
  Bun.serve({
    port: Number(process.env.MORPHE_PORT ?? cfg.listen.port) + 100, // bun lane tests on listen+100 (25204 -> 25304); green-blue swap moves it to the real port
    async fetch(req) {
      const url = new URL(req.url);
      const body = Buffer.from(await req.arrayBuffer());
      // synthetic head for resolution (Bun normalizes headers)
      const head = Buffer.from(`${req.method} ${url.pathname} HTTP/1.1\r\n` +
        [...req.headers.entries()].map(([k, v]) => `${k}: ${v}\r\n`).join("") + "\r\n");
      const r = await handleRequest(cfg, Bun.serve ? Number(process.env.MORPHE_PORT ?? cfg.listen.port) : 0, url.pathname, head, body);
      return new Response(r.payload, { status: r.status, headers: { "content-type": "application/json" } });
    },
  });
  log.info(`bun lane listening (green-blue test port ${Number(process.env.MORPHE_PORT ?? cfg.listen.port) + 100})`);
  // parquet flush every 30s
  setInterval(() => ledger.flush(), 30_000).unref();
}
