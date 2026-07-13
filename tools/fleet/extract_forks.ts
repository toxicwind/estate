#!/usr/bin/env bun
/**
 * Extract 4-fork bin + LD macros from llama-swap config.yaml (SSOT).
 * Never invent LD paths — they live next to beellama_ld / ik_ld / etc.
 */
import { resolve } from "path";

const ROOT = process.env.SOVEREIGN_ROOT || resolve(import.meta.dir, "../..");
const cfgPath =
  process.env.LLAMA_SWAP_CONFIG ||
  resolve(ROOT, "tools/llama-swap/config.yaml");
const outPath = resolve(import.meta.dir, "forks.json");

const text = await Bun.file(cfgPath).text();
const macros: Record<string, string> = {};
for (const line of text.split("\n")) {
  const m = line.match(/^\s{2}([A-Za-z0-9_]+):\s*"([^"]+)"/);
  if (m) macros[m[1]] = m[2];
}

const forks = {
  beellama: { bin: macros.beellama_bin, ld: macros.beellama_ld },
  turboquant: { bin: macros.turbo_bin, ld: macros.turbo_ld },
  ik_llama: { bin: macros.ik_bin, ld: macros.ik_ld },
  ik_turboquant: { bin: macros.ik_tq_bin, ld: macros.ik_tq_ld },
} as Record<
  string,
  { bin?: string; ld?: string; bench?: string | null; bin_resolved?: string }
>;

for (const [name, f] of Object.entries(forks)) {
  if (!f.bin) continue;
  const p = Bun.file(f.bin);
  // resolve symlink via realpath
  const proc = Bun.spawnSync(["readlink", "-f", f.bin]);
  const resolved = proc.exitCode === 0 ? proc.stdout.toString().trim() : f.bin;
  f.bin_resolved = resolved;
  const bench = resolved.replace(/llama-server$/, "llama-bench");
  f.bench = (await Bun.file(bench).exists()) ? bench : null;
  console.log(`${name}: bin=${resolved} ld_parts=${(f.ld || "").split(":").length} bench=${f.bench ? "yes" : "no"}`);
}

const payload = {
  MODEL_DIR: macros.MODEL_DIR || resolve(ROOT, "models"),
  config: cfgPath,
  extracted_at: new Date().toISOString(),
  forks,
  ctx_policy: {
    probes: [4096, 8192, 16384, 32768, 65536],
    deep_optional: 131072,
    never_start_27b_at_max: true,
    note: "Use graduated ctx; 27B class stops on first OOM; prefer qwen-flash for gates",
  },
};

await Bun.write(outPath, JSON.stringify(payload, null, 2) + "\n");
console.log(`wrote ${outPath}`);
