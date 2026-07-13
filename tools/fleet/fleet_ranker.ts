#!/usr/bin/env bun
/**
 * fleet_ranker.ts — GGUF context + throughput profiler
 * Sovereign Mesh | June 2026
 *
 * Scans model dir, sends graduated context probes to llama-server,
 * measures TPS + stability, writes ranked JSON.
 *
 * Usage:
 *   bun run fleet_ranker.ts --port 25010 --upstream http://127.0.0.1:25001
 *   bun run fleet_ranker.ts --scan-dir ~/models --output rank_$(date +%Y%m%d).json
 */

import { serve } from "bun";
import { readdir } from "fs/promises";
import { join } from "path";

// Sovereign defaults (2026-07): rank via llama-swap front door; graduated ctx only.
const PORT        = parseInt(Bun.env.RANK_PORT      ?? "25107");
const UPSTREAM    = Bun.env.MODEL_URL               ?? "http://127.0.0.1:25100";
const SCAN_DIR    = Bun.env.MODEL_DIR
                    ?? Bun.env.MODEL_PATH?.split("/").slice(0,-1).join("/")
                    ?? "/home/toxic/sovereign/models";

// Context size is critical — never jump to 128k/max first (27B OOM → empty choices).
const CTX_PROBES  = (Bun.env.FLEET_CTX_PROBES ?? "4096,8192,16384,32768,65536")
  .split(",")
  .map((s) => parseInt(s.trim(), 10))
  .filter((n) => n > 0);
const PROBE_TOKENS = 32;
const RESULTS_DIR =
  Bun.env.FLEET_RESULTS ??
  `${Bun.env.HOME ?? "/home/toxic"}/sovereign/tools/fleet/results`;

interface RankResult {
  file:      string;
  max_ctx:   number;
  tps:       number;
  tier:      "fast" | "mid" | "deep";
  timestamp: string;
}

async function probeModel(modelPath: string, ctx: number): Promise<number | null> {
  // Returns TPS if stable at this context, null if OOM/error
  const prompt = "The quick brown fox " + " and ".repeat(Math.floor(ctx / 20));
  const body = JSON.stringify({
    model: "local",
    messages: [{ role: "user", content: prompt.slice(0, ctx * 3) }],
    max_tokens: PROBE_TOKENS,
    temperature: 0,
    stream: false,
  });
  try {
    const t0  = performance.now();
    const res = await fetch(`${UPSTREAM}/v1/chat/completions`, {
      method:  "POST",
      headers: { "Content-Type": "application/json", "X-Model-Path": modelPath },
      body,
      signal: AbortSignal.timeout(60_000),
    });
    if (!res.ok) return null;
    const data  = await res.json();
    const ms    = performance.now() - t0;
    const toks  = data?.usage?.completion_tokens ?? PROBE_TOKENS;
    return (toks / ms) * 1000;
  } catch {
    return null;
  }
}

async function rankModel(file: string): Promise<RankResult> {
  const path = join(SCAN_DIR, file);
  let maxCtx = 0, bestTps = 0;
  for (const ctx of CTX_PROBES) {
    const tps = await probeModel(path, ctx);
    if (tps === null) break;
    maxCtx = ctx;
    bestTps = tps;
  }
  const tier: RankResult["tier"] =
    maxCtx >= 65536 ? "deep" : maxCtx >= 16384 ? "mid" : "fast";
  return { file, max_ctx: maxCtx, tps: Math.round(bestTps), tier,
           timestamp: new Date().toISOString() };
}

async function scanAndRank(): Promise<RankResult[]> {
  const entries = await readdir(SCAN_DIR);
  const ggufs   = entries.filter(f => f.endsWith(".gguf"));
  const results: RankResult[] = [];
  for (const g of ggufs) {
    console.log(`[rank] probing ${g}...`);
    results.push(await rankModel(g));
  }
  return results.sort((a, b) => b.tps - a.tps);
}

// ── HTTP server ──────────────────────────────────────────────────────────────
const results: Map<string, RankResult[]> = new Map();

serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === "/health")
      return Response.json({ status: "ok", upstream: UPSTREAM, scan_dir: SCAN_DIR });

    if (url.pathname === "/metrics")
      return new Response("fleet_ranker_up 1\n", { headers: { "Content-Type": "text/plain" } });

    if (url.pathname === "/rank") {
      // Async scan — returns immediately with job ID, results via /results
      const jobId = Date.now().toString();
      scanAndRank().then(r => results.set(jobId, r));
      return Response.json({ job_id: jobId, status: "running" });
    }

    if (url.pathname.startsWith("/results/")) {
      const id = url.pathname.split("/")[2];
      const r  = results.get(id);
      if (!r) return Response.json({ status: "pending" }, { status: 202 });
      return Response.json({ status: "done", results: r });
    }

    if (url.pathname === "/latest") {
      const all = [...results.values()].at(-1) ?? [];
      return Response.json(all);
    }

    return new Response("Not found", { status: 404 });
  },
});

console.log(`[fleet-ranker] :${PORT} | upstream: ${UPSTREAM} | scan: ${SCAN_DIR}`);
