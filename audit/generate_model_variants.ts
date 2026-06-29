#!/usr/bin/env bun
/**
 * generate_model_variants.ts
 *
 * Deeply analyzes flags.json and each .gguf model to produce three targeted
 * llama-server commands: MAX_CONTEXT, BALANCED, CONSERVATIVE.
 *
 * Heuristics: model family, README, mmproj, file size, name patterns.
 */

import { readdirSync, existsSync, readFileSync, realpathSync, statSync } from "fs";
import { join, dirname, basename } from "path";

// ----------------------------------------------------------------------------
// Configuration
// ----------------------------------------------------------------------------

const MODELS_DIR = "/home/toxic/models";
const FLAGS_PATH = "/home/toxic/sovereign/flags.json";
const SERVER_BIN = "/home/toxic/ik_llama.cpp-main/build/bin/llama-server";

// Default ports: start at 25001, increment per model to avoid conflicts
let nextPort = 25001;

// ----------------------------------------------------------------------------
// Types & Interfaces
// ----------------------------------------------------------------------------

interface Flag {
  long: string;
  short?: string;
  description: string;
  default?: string;   // not always given, but we can parse from description
}

interface ModelInfo {
  canonicalPath: string;    // real absolute path
  name: string;
  dir: string;
  sizeBytes: number;
  hasMmproj: boolean;
  mmprojPath?: string;
  readmeText?: string;
  // Inferred properties
  contextLength: number;
  ropeScaling: "none" | "linear" | "yarn";
  isMultimodal: boolean;
  isMoE: boolean;
  isReasoning: boolean;
  isInstruct: boolean;
  family: string;           // "llama", "qwen", "gemma", "deepseek", "mistral", etc.
}

// ----------------------------------------------------------------------------
// Utilities
// ----------------------------------------------------------------------------

/** Load and parse flags.json, return a map: longName -> Flag */
function loadFlags(): Map<string, Flag> {
  if (!existsSync(FLAGS_PATH)) {
    console.warn(`flags.json not found at ${FLAGS_PATH}, proceeding without validation.`);
    return new Map();
  }
  const data = JSON.parse(readFileSync(FLAGS_PATH, "utf-8")) as any[];
  const map = new Map<string, Flag>();
  for (const f of data) {
    if (f.long) map.set(f.long, f);
    if (f.short) map.set(f.short, f);   // also store short for completion
  }
  return map;
}

/** Find all unique .gguf files (resolving symlinks) */
function findModels(root: string): ModelInfo[] {
  const seen = new Set<string>();
  const results: ModelInfo[] = [];

  function walk(dir: string) {
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      const full = join(dir, e.name);
      let realPath: string;
      try {
        realPath = realpathSync(full);
      } catch {
        continue;
      }

      if (e.isDirectory() || (e.isSymbolicLink() && statSync(full).isDirectory())) {
        walk(realPath);
        continue;
      }

      if (!realPath.endsWith(".gguf")) continue;
      if (seen.has(realPath)) continue;
      seen.add(realPath);

      const dirName = dirname(realPath);
      let mmprojPath: string | undefined;
      const siblings = readdirSync(dirName);
      for (const s of siblings) {
        if (s.match(/^mmproj-.+\.gguf$/i)) {
          mmprojPath = join(dirName, s);
          break;
        }
      }

      const readmePath = join(dirName, "README.md");
      let readmeText: string | undefined;
      if (existsSync(readmePath)) {
        readmeText = readFileSync(readmePath, "utf8");
      }

      const stats = statSync(realPath);
      results.push({
        canonicalPath: realPath,
        name: basename(realPath),
        dir: dirName,
        sizeBytes: stats.size,
        hasMmproj: !!mmprojPath,
        mmprojPath,
        readmeText,
        contextLength: 0,
        ropeScaling: "none",
        isMultimodal: !!mmprojPath,
        isMoE: false,
        isReasoning: false,
        isInstruct: false,
        family: "unknown",
      });
    }
  }

  walk(root);
  return results;
}

/** Infer model family from filename + README */
function inferFamily(model: ModelInfo): string {
  const text = (model.readmeText || "") + " " + model.name + " " + model.canonicalPath;
  const lower = text.toLowerCase();
  if (lower.includes("deepseek")) return "deepseek";
  if (lower.includes("qwen")) return "qwen";
  if (lower.includes("gemma")) return "gemma";
  if (lower.includes("llama")) return "llama";
  if (lower.includes("mistral")) return "mistral";
  return "other";
}

/** Infer context length from README or fallback */
function inferContextLength(model: ModelInfo): number {
  const text = model.readmeText || "";
  const name = model.name;
  const combined = text + " " + name + " " + model.canonicalPath;

  const patterns = [
    /context\s*(?:length|size)\s*[:=]\s*(\d+)/i,
    /max\s*(?:sequence|ctx|context)\s*(?:length|size)?\s*[:=]\s*(\d+)/i,
    /(\d+)\s*k\s*context/i,
    /context\s*:\s*(\d+)/i,
  ];
  for (const pat of patterns) {
    const m = combined.match(pat);
    if (m) {
      const val = parseInt(m[1], 10);
      if (m[0].toLowerCase().includes("k")) return val * 1024;
      return val;
    }
  }

  // Fallback based on family
  const fam = model.family;
  if (fam === "deepseek" || fam === "qwen" || fam === "llama") {
    // newer models often have 128k+
    return 131072;
  }
  if (fam === "gemma") {
    return 8192;
  }
  return 4096;
}

/** Infer rope scaling method */
function inferRopeScaling(model: ModelInfo): "none" | "linear" | "yarn" {
  const text = (model.readmeText || "") + " " + model.name + " " + model.canonicalPath;
  const lower = text.toLowerCase();
  if (lower.includes("yarn") || lower.includes("ya r n")) return "yarn";
  if (lower.includes("linear") || lower.includes("rope scale")) return "linear";
  if (model.contextLength > 8192) return "linear";
  return "none";
}

/** Detect MoE (likely has "moe" in name or README) */
function inferMoE(model: ModelInfo): boolean {
  const text = (model.readmeText || "") + " " + model.name + " " + model.canonicalPath;
  return /moe|mixture of experts/i.test(text);
}

/** Detect reasoning model (DeepSeek R1, etc.) */
function inferReasoning(model: ModelInfo): boolean {
  const text = (model.readmeText || "") + " " + model.name + " " + model.canonicalPath;
  return /reasoning|think|r1/i.test(text);
}

/** Detect instruct model (has "instruct" or "chat") */
function inferInstruct(model: ModelInfo): boolean {
  const text = (model.readmeText || "") + " " + model.name + " " + model.canonicalPath;
  return /instruct|chat|conversation/i.test(text);
}

/** Build a command variant using only flags that exist in flags.json */
function buildVariant(
  model: ModelInfo,
  flagsMap: Map<string, Flag>,
  ctxSize: number,
  batchSize: number,
  ubatchSize: number,
  extraFlags: Record<string, string | number | boolean> = {}
): string {
  const parts = [SERVER_BIN, `-m ${model.canonicalPath}`];

  // mmproj
  if (model.hasMmproj && flagsMap.has("--mmproj")) {
    parts.push(`--mmproj ${model.mmprojPath}`);
  }

  // Host & port (auto-increment)
  const port = nextPort++;
  parts.push(`--host 127.0.0.1`, `--port ${port}`);

  // Context
  if (flagsMap.has("--ctx-size")) {
    parts.push(`-c ${ctxSize}`);
  }

  // Batch sizes
  if (flagsMap.has("--batch-size")) {
    parts.push(`-b ${batchSize}`);
  }
  if (flagsMap.has("--ubatch-size")) {
    parts.push(`--ubatch-size ${ubatchSize}`);
  }

  // GPU offload
  if (flagsMap.has("--gpu-layers")) {
    parts.push(`-ngl 99`);  // offload all layers
  }

  // mmap – we prefer --no-mmap for faster start
  if (flagsMap.has("--no-mmap")) {
    parts.push(`--no-mmap`);
  }

  // Flash Attention (enable by default unless conservative variant sets off)
  const noFlash = extraFlags["no-flash-attn"] === true;
  if (flagsMap.has("--flash-attn") && !noFlash) {
    parts.push(`--flash-attn 1`);
  } else if (flagsMap.has("--no-flash-attn") && noFlash) {
    parts.push(`--no-flash-attn`);
  }

  // Rope scaling
  if (model.ropeScaling !== "none") {
    if (flagsMap.has("--rope-scaling")) {
      parts.push(`--rope-scaling ${model.ropeScaling}`);
    }
    if (model.ropeScaling === "yarn") {
      // include YaRN parameters if available
      if (flagsMap.has("--yarn-ext-factor")) parts.push(`--yarn-ext-factor -1.0`);
      if (flagsMap.has("--yarn-attn-factor")) parts.push(`--yarn-attn-factor -1.0`);
      if (flagsMap.has("--yarn-beta-slow")) parts.push(`--yarn-beta-slow -1.0`);
      if (flagsMap.has("--yarn-beta-fast")) parts.push(`--yarn-beta-fast -1.0`);
    }
  }

  // MoE flags
  if (model.isMoE) {
    if (flagsMap.has("--cpu-moe")) parts.push(`--cpu-moe`);
    if (flagsMap.has("--defer-experts")) parts.push(`--defer-experts`);
  }

  // Reasoning flags (DeepSeek R1)
  if (model.isReasoning) {
    if (flagsMap.has("--reasoning-format")) {
      parts.push(`--reasoning-format deepseek`);
    }
    if (flagsMap.has("--reasoning-budget")) {
      parts.push(`--reasoning-budget -1`);  // unlimited
    }
    // Maybe also --chat-template-kwargs, but we'll skip for brevity
  }

  // Sampling flags: set defaults based on model type
  const temp = model.isInstruct ? 0.6 : 0.8;
  const topP = model.isInstruct ? 0.9 : 0.95;
  if (flagsMap.has("--temp")) parts.push(`--temp ${temp}`);
  if (flagsMap.has("--top-p")) parts.push(`--top-p ${topP}`);
  if (flagsMap.has("--repeat-penalty")) parts.push(`--repeat-penalty 1.1`);

  // Extra flags passed in (e.g., for specific models)
  for (const [key, value] of Object.entries(extraFlags)) {
    if (flagsMap.has(key)) {
      if (typeof value === "boolean") {
        if (value) parts.push(key);
        // if false, skip (we already handled no-flash)
      } else {
        parts.push(`${key} ${value}`);
      }
    }
  }

  return parts.join(" \\\n  ");
}

// ----------------------------------------------------------------------------
// Main
// ----------------------------------------------------------------------------

function main() {
  const flagsMap = loadFlags();
  let models = findModels(MODELS_DIR);

  // Enrich each model with inferred properties
  for (const m of models) {
    m.family = inferFamily(m);
    m.contextLength = inferContextLength(m);
    m.ropeScaling = inferRopeScaling(m);
    m.isMoE = inferMoE(m);
    m.isReasoning = inferReasoning(m);
    m.isInstruct = inferInstruct(m);
  }

  // Sort models by name for consistent output
  models.sort((a, b) => a.name.localeCompare(b.name));

  let output = `# Sovereign Model Command Variants — Generated ${new Date().toISOString()}\n`;
  output += `# Flags validated against ${FLAGS_PATH}\n\n`;

  for (const m of models) {
    output += `## ${m.name}\n`;
    output += `# Family: ${m.family}, Context: ${m.contextLength}, Scaling: ${m.ropeScaling}\n`;
    if (m.readmeText) {
      const snippet = m.readmeText.split("\n").slice(0, 3).join(" | ");
      output += `# README: ${snippet}\n`;
    }
    if (m.hasMmproj) output += "# Multimodal enabled\n";
    if (m.isMoE) output += "# MoE model – using CPU offload\n";
    if (m.isReasoning) output += "# Reasoning model – enabling --reasoning-format\n";
    if (m.isInstruct) output += "# Instruct model – using lower temperature\n\n";

    // Determine three context sizes
    const maxCtx = Math.min(m.contextLength, 131072);
    const balancedCtx = Math.min(maxCtx, 65536);
    const conservativeCtx = Math.min(maxCtx, 32768);

    // ---- Variant 1: MAX_CONTEXT ----
    const maxCmd = buildVariant(m, flagsMap, maxCtx, 2048, 512, {
      // extra: maybe enable all logits? Not needed.
    });
    output += `### MAX_CONTEXT\n${maxCmd}\n\n`;

    // ---- Variant 2: BALANCED ----
    const balCmd = buildVariant(m, flagsMap, balancedCtx, 2048, 512, {});
    output += `### BALANCED\n${balCmd}\n\n`;

    // ---- Variant 3: CONSERVATIVE ----
    const consCmd = buildVariant(m, flagsMap, conservativeCtx, 1024, 256, {
      "no-flash-attn": true,
    });
    output += `### CONSERVATIVE\n${consCmd}\n\n`;

    output += "=".repeat(80) + "\n\n";
  }

  console.log(output);
}

main();
