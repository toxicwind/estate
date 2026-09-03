#!/usr/bin/env bun
/**
 * fleet_config_ranker.ts — benchmark every model through its exact llama-swap config
 *
 * Reads config.yaml, resolves macros, launches each model with its
 * production flags (fork, ctx, cache, draft, MTP), probes graduated
 * context sizes, and outputs a real-deployed-speed leaderboard.
 *
 * Usage:
 *   bun run tools/fleet/fleet_config_ranker.ts
 *   bun run tools/fleet/fleet_config_ranker.ts --model beellama/qwen-flash-64k
 *   bun run tools/fleet/fleet_config_ranker.ts --dry-run
 *   bun run tools/fleet/fleet_config_ranker.ts --parallel 3
 */

import { readFile, writeFile, mkdir } from "fs/promises";
import { spawn, ChildProcess } from "child_process";
import { resolve as resolvePath } from "path";

const CONFIG_PATH  = process.env.CONFIG_PATH  ?? resolvePath(__dirname, "../llama-swap/config.yaml");
const RESULTS_DIR  = process.env.FLEET_RESULTS ?? resolvePath(__dirname, "results");
const MODEL_DIR    = process.env.MODEL_DIR     ?? "/home/toxic/projects/models";

const CTX_PROBES   = (process.env.FLEET_CTX_PROBES ?? "4096,8192,16384,32768")
  .split(",").map(s => parseInt(s.trim(), 10)).filter(n => n > 0);

const PROBE_TOKENS = 32;
const HEALTH_TIMEOUT_MS = 60_000;
const PROBE_TIMEOUT_MS  = 120_000;
const PORT_RANGE_START  = parseInt(process.env.FLEET_PORT_START ?? "25150");
const PORT_RANGE_END    = PORT_RANGE_START + 50;

/** Safety margin — never use more than this fraction of available VRAM */
const VRAM_SAFETY_FRACTION = 0.85;
const VRAM_CTX_OVERHEAD_MB = 512; // per-probe context memory overhead

interface ModelConfig {
  name: string;
  cmd: string;
  metadata: Record<string, unknown>;
  fork: string;
  model_file: string;
}

interface RankResult {
  model: string;
  fork: string;
  model_file: string;
  resolved_cmd: string;
  ctx_probes: { ctx: number; tps: number | null }[];
  max_stable_ctx: number;
  best_tps: number;
  tier: "fast" | "mid" | "deep";
  health_ok: boolean;
  error?: string;
  timestamp: string;
}

function sleep(ms: number): Promise<void> {
  return new Promise(r => setTimeout(r, ms));
}

/** Kill any stale processes on benchmark ports to prevent VRAM pile-up. */
function cleanupStaleProcesses(): void {
  console.log("[cleanup] killing stale llama-server on benchmark ports...");
  try {
    require("child_process").execSync(
      `for port in $(seq ${PORT_RANGE_START} ${PORT_RANGE_END}); do ` +
      "  pid=$(lsof -ti :$port 2>/dev/null) && " +
      "  echo \"[cleanup] killing pid=$pid on port=$port\" && " +
      "  kill -9 $pid 2>/dev/null; " +
      "done",
      { encoding: "utf-8", timeout: 10000 }
    );
  } catch {}
  // Also kill any leftover llama-server that might be orphaned
  try {
    require("child_process").execSync(
      "pkill -9 -f 'llama-server.*2515[0-9]' 2>/dev/null || true",
      { encoding: "utf-8", timeout: 5000 }
    );
  } catch {}
}

/** Query available VRAM via nvidia-smi. Returns MiB or null if no GPU. */
function getAvailableVRAM(): number | null {
  try {
    const out = require("child_process").execSync(
      "nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null",
      { encoding: "utf-8", timeout: 5000 }
    ).trim();
    const mb = parseInt(out.split("\n")[0], 10);
    return isNaN(mb) ? null : mb;
  } catch {
    return null;
  }
}

/** Estimate VRAM needed for a model at a given ctx size (conservative). */
function estimateVRAM(modelPath: string, ctx: number): number {
  try {
    const size = require("fs").statSync(modelPath).size; // bytes
    const gb = size / 1024 / 1024 / 1024;
    // Heuristic: model weights + ctx * (layers * head_dim * 2 * kv_cache_bytes)
    // Conservative: 2x model size for kv cache at max ctx (covers q8_0 cache)
    return gb * 1024 + ctx * 0.5; // MiB
  } catch {
    return Infinity; // can't check — let it try
  }
}

function getFreePort(used: Set<number>): number {
  for (let p = PORT_RANGE_START; p < PORT_RANGE_END; p++) {
    if (!used.has(p)) return p;
  }
  throw new Error("No free ports in range " + PORT_RANGE_START + "-" + PORT_RANGE_END);
}

function expandMacros(
  val: string,
  macros: Record<string, string>,
  visited: Set<string> = new Set()
): string {
  const pattern = /\$\{(\w+)\}/g;
  let result = val;
  let prev: string;
  do {
    prev = result;
    result = result.replace(pattern, (_m, name) => {
      if (visited.has(name)) {
        console.warn(`[warn] circular macro ${name}, leaving as-is`);
        return _m;
      }
      const v = macros[name];
      if (v === undefined) {
        console.warn(`[warn] undefined macro ${name}, leaving as-is`);
        return _m;
      }
      visited.add(name);
      const expanded = expandMacros(v, macros, visited);
      visited.delete(name);
      return expanded;
    });
  } while (result !== prev);
  return result;
}

async function compileConfig(): Promise<{ models: ModelConfig[]; macros: Record<string, string> }> {
  const yaml = await import("js-yaml");
  const raw = await readFile(CONFIG_PATH, "utf-8");
  const doc = yaml.load(raw) as any;

  const rawMacros: Record<string, string> = doc.macros ?? {};
  const macros: Record<string, string> = {};
  for (const [k, v] of Object.entries(rawMacros)) {
    if (typeof v === "string") macros[k] = v;
  }

  const models: ModelConfig[] = [];
  for (const [name, cfg] of Object.entries(doc.models ?? {})) {
    const c = cfg as any;
    models.push({
      name,
      cmd: c.cmd ?? "",
      metadata: c.metadata ?? {},
      fork: c.metadata?.fork ?? "unknown",
      model_file: "",
    });
  }
  return { models, macros };
}

function resolveModelPath(cmd: string): string {
  const m = cmd.match(/--model\s+(\S+)/);
  if (!m) return "unknown";
  const path = m[1];
  if (path.startsWith("/")) return path;
  return resolvePath(MODEL_DIR, path);
}

function resolveCmd(cmd: string, macros: Record<string, string>, port: number): string {
  let resolved = expandMacros(cmd, macros);
  // Replace ${PORT} placeholders
  resolved = resolved.replace(/\$\{PORT\}/g, String(port));
  return resolved;
}

async function waitForHealth(url: string, timeoutMs: number): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url + "/health", { signal: AbortSignal.timeout(3000) });
      if (res.ok) return true;
    } catch {}
    await sleep(1000);
  }
  return false;
}

async function probeModel(port: number, ctx: number): Promise<number | null> {
  const prompt = "The quick brown fox " + " and ".repeat(Math.floor(ctx / 20));
  const body = JSON.stringify({
    model: "local",
    messages: [{ role: "user", content: prompt.slice(0, ctx * 3) }],
    max_tokens: PROBE_TOKENS,
    temperature: 0,
    stream: false,
  });

  try {
    const t0 = performance.now();
    const res = await fetch(`http://127.0.0.1:${port}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
    });
    if (!res.ok) return null;
    const data: any = await res.json();
    const ms = performance.now() - t0;
    const toks = data?.usage?.completion_tokens ?? PROBE_TOKENS;
    return toks / ms * 1000;
  } catch {
    return null;
  }
}

function spawnModel(cmd: string, port: number, logFile: string): { proc: ChildProcess; killed: Promise<void> } {
  // Parse the resolved cmd string into exec and args
  const tokens: string[] = [];
  let current = "";
  let inQuote: string | null = null;
  for (const ch of cmd) {
    if (inQuote) {
      if (ch === inQuote) inQuote = null;
      else current += ch;
    } else if (ch === "'" || ch === '"') {
      inQuote = ch;
    } else if (ch === " ") {
      if (current) { tokens.push(current); current = ""; }
    } else {
      current += ch;
    }
  }
  if (current) tokens.push(current);

  const exec = tokens[0];
  const args = tokens.slice(1);

  const proc = spawn(exec, args, {
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, LLAMA_API_KEY: "", LLAMA_ARG_API_KEY: "" },
  });

  const killed = new Promise<void>((resolve) => {
    proc.on("exit", () => resolve());
  });

  // Write stderr to log
  const logStream = require("fs").createWriteStream(logFile, { flags: "a" });
  const debugStream = require("fs").createWriteStream("/tmp/herd-debug.log", { flags: "a" });
  proc.stdout?.pipe(logStream);
  proc.stderr?.pipe(debugStream);
  proc.stderr?.pipe(logStream);

  return { proc, killed };
}

async function killProcess(proc: ChildProcess | null): Promise<void> {
  if (!proc) return;
  if (proc.pid) {
    try {
      process.kill(-proc.pid, "SIGTERM");
    } catch {}
    try {
      process.kill(proc.pid, "SIGTERM");
    } catch {}
  }
  await sleep(2000);
  if (proc.exitCode === null && proc.pid) {
    try {
      process.kill(proc.pid, "SIGKILL");
    } catch {}
  }
}

async function benchmarkModel(
  name: string,
  cmd: string,
  macros: Record<string, string>,
  port: number,
  logDir: string
): Promise<RankResult> {
  const resolvedCmd = resolveCmd(cmd, macros, port);
  const modelFile = resolveModelPath(resolvedCmd);
  const logFile = resolvePath(logDir, name.replace(/[\/\s]/g, "_") + ".log");

  const result: RankResult = {
    model: name,
    fork: "",
    model_file: modelFile,
    resolved_cmd: resolvedCmd,
    ctx_probes: [],
    max_stable_ctx: 0,
    best_tps: 0,
    tier: "fast",
    health_ok: false,
    timestamp: new Date().toISOString(),
  };

  console.log(`[bench] ${name} | port ${port} | ${modelFile}`);

  const { proc } = spawnModel(resolvedCmd, port, logFile);

  const healthOk = await waitForHealth(`http://127.0.0.1:${port}`, HEALTH_TIMEOUT_MS);
  result.health_ok = healthOk;

  if (!healthOk) {
    console.log(`[bench] ${name} — health failed, skipping probes`);
    result.error = "health check failed";
    await killProcess(proc);
    return result;
  }

  await sleep(2000); // let the model settle

  for (const ctx of CTX_PROBES) {
    const tps = await probeModel(port, ctx);
    result.ctx_probes.push({ ctx, tps });
    console.log(`[bench] ${name} ctx=${ctx} tps=${tps?.toFixed(1) ?? "OOM"}`);
    if (tps === null) break;
    result.max_stable_ctx = ctx;
    result.best_tps = Math.max(result.best_tps, tps);
  }

  result.tier = result.max_stable_ctx >= 65536 ? "deep"
    : result.max_stable_ctx >= 16384 ? "mid" : "fast";

  await killProcess(proc);
  return result;
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");

  // Collect all --model values (support multiple: --model A --model B)
  const filterModels: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--model" && i + 1 < args.length) {
      filterModels.push(args[++i]);
    }
  }

  const parallelCount = args.includes("--parallel")
    ? parseInt(args[args.indexOf("--parallel") + 1], 10) || 1
    : 1;

  const { models, macros } = await compileConfig();
  const logDir = resolvePath(RESULTS_DIR, "logs");
  await mkdir(logDir, { recursive: true });

  console.log(`[fleet-config-ranker] ${models.length} models in config`);
  console.log(`[fleet-config-ranker] ctx probes: ${CTX_PROBES.join(", ")}`);
  console.log(`[fleet-config-ranker] parallel: ${parallelCount} | dry-run: ${dryRun}\n`);

  if (dryRun) {
    for (const m of models) {
      if (filterModels.length && !filterModels.includes(m.name)) continue;
      const resolved = resolveCmd(m.cmd, macros, 25150);
      const modelFile = resolveModelPath(resolved);
      console.log(`  ${m.name}`);
      console.log(`    model: ${modelFile}`);
      console.log(`    fork:  ${m.fork}`);
      console.log(`    cmd:   ${resolved.slice(0, 200)}...`);
      console.log();
    }
    return;
  }

  let targets = filterModels.length
    ? models.filter(m => filterModels.includes(m.name))
    : models;

  // VRAM safety pre-flight
  const vramMb = getAvailableVRAM();
  if (vramMb !== null) {
    const maxSafe = Math.floor(vramMb * VRAM_SAFETY_FRACTION);
    console.log(`[fleet-config-ranker] GPU VRAM: ${vramMb} MiB available, using max ${maxSafe} MiB (${VRAM_SAFETY_FRACTION*100}%)`);

    targets = targets.filter(m => {
      const cmd = resolveCmd(m.cmd, macros, 25150);
      const modelFile = resolveModelPath(cmd);
      const est = estimateVRAM(modelFile, Math.max(...CTX_PROBES));
      if (est > maxSafe) {
        console.log(`[vram-skip] ${m.name} — est ${est.toFixed(0)} MiB > ${maxSafe} MiB (${modelFile})`);
        return false;
      }
      return true;
    });
  } else {
    console.log("[fleet-config-ranker] No GPU VRAM info — running without VRAM safety check");
  }

  // Kill any leftover processes before starting
  cleanupStaleProcesses();

  const usedPorts = new Set<number>();
  const results: RankResult[] = [];

  for (let i = 0; i < targets.length; i += parallelCount) {
    const batch = targets.slice(i, i + parallelCount);
    const batchResults = await Promise.all(
      batch.map(async (m) => {
        const port = getFreePort(usedPorts);
        usedPorts.add(port);
        console.log(`[bench] ${m.name} — port ${port}, model ${m.model_file}`);
        try {
          return await benchmarkModel(m.name, m.cmd, macros, port, logDir);
        } catch (err: any) {
          return {
            model: m.name,
            fork: m.fork,
            model_file: "",
            resolved_cmd: "",
            ctx_probes: [],
            max_stable_ctx: 0,
            best_tps: 0,
            tier: "fast" as const,
            health_ok: false,
            error: err?.message ?? String(err),
            timestamp: new Date().toISOString(),
          } as RankResult;
        } finally {
          usedPorts.delete(port);
        }
      })
    );
    results.push(...batchResults);
  }

  results.sort((a, b) => b.best_tps - a.best_tps);

  const outPath = resolvePath(RESULTS_DIR, `config_bench_${new Date().toISOString().slice(0,10)}.json`);
  await writeFile(outPath, JSON.stringify(results, null, 2));
  console.log(`\n[fleet-config-ranker] results written to ${outPath}`);

  console.log("\n=== LEADERBOARD (by TPS) ===");
  console.log(`${"RANK".padEnd(5)} ${"MODEL".padEnd(40)} ${"TPS".padEnd(8)} ${"MAX_CTX".padEnd(8)} ${"TIER".padEnd(6)} ${"HEALTH"}`);
  results.forEach((r, i) => {
    console.log(
      `${(i+1).toString().padEnd(5)} ${r.model.padEnd(40)} ${r.best_tps.toFixed(0).padEnd(8)} ${r.max_stable_ctx.toString().padEnd(8)} ${r.tier.padEnd(6)} ${r.health_ok ? "OK" : "FAIL"}`
    );
  });
}

main().catch(err => {
  console.error("[fatal]", err);
  process.exit(1);
});
