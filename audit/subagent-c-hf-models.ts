#!/usr/bin/env bun
// subagent-c-hf-models.ts
// Subagent C: HF Model Discovery & Deployer
// Focus: Weird finetunes, emergent models, HF CLI integration, VRAM estimation
// llama.cpp integration, mergekit frankenmerge, abliterated models

import { spawn } from "bun";

const RED  = "\x1b[31m"; const GRN = "\x1b[32m"; const YEL = "\x1b[33m";
const BLU  = "\x1b[34m"; const MAG = "\x1b[35m"; const CYN = "\x1b[36m";
const RST  = "\x1b[0m";  const BOLD = "\x1b[1m"; const DIM = "\x1b[2m";

const HF_WEIRD_MODELS = [
  { repo: "RavichandranJ/Dolphin3-Cyber-8B-GGUF",         desc: "Cybersecurity-specialized Dolphin3, abliterated for pentesting", tags: ["cybersec", "abliterated", "gguf", "uncensored"], size: "8B", quant: "GGUF", vram_gb: 5.2 },
  { repo: "DuoNeural/Cosmos3-Nano-Abliterated",           desc: "First abliterated Cosmos3-Nano. 2-pass PRISM abliteration on MoT architecture", tags: ["abliterated", "mot", "video", "cosmos3"], size: "15B", quant: "BF16", vram_gb: 30 },
  { repo: "unsloth/Qwen3.5-35B-A3B-GGUF",                 desc: "Qwen3.5 35B A3B MoE with UD-Q4_K_XL quant via Unsloth", tags: ["moe", "qwen3.5", "gguf", "deltanet"], size: "35B", quant: "GGUF", vram_gb: 22 },
  { repo: "Qwen/Qwen3.5-0.8B",                           desc: "Qwen3.5 0.8B dense for edge deployment", tags: ["qwen3.5", "edge", "dense"], size: "0.8B", quant: "BF16", vram_gb: 2 },
  { repo: "Qwen/Qwen3.5-27B",                            desc: "Qwen3.5 27B dense. MathArena 90.83 on AIME 2026", tags: ["qwen3.5", "dense", "agentic", "math"], size: "27B", quant: "BF16", vram_gb: 54 },
  { repo: "Qwen/Qwen3.5-397B-A17B",                      desc: "Qwen3.5 397B A17B production-scale validation. Hybrid DeltaNet", tags: ["moe", "qwen3.5", "frontier"], size: "397B", quant: "BF16", vram_gb: 794 },
  { repo: "unsloth/Qwen3-Next-80B-A3B-Instruct-GGUF",     desc: "Qwen3-Next 80B A3B instruct with speculative decoding support", tags: ["moe", "qwen3", "instruct", "speculative"], size: "80B", quant: "GGUF", vram_gb: 48 },
  { repo: "Qwen/Qwen3-Embedding-0.6B",                   desc: "Qwen3 embedding model for RAG pipelines", tags: ["qwen3", "embedding", "rag"], size: "0.6B", quant: "BF16", vram_gb: 1.2 },
  { repo: "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-GGUF", desc: "Nemotron 3 Ultra 550B frontier-scale reasoning. 1M context", tags: ["nemotron", "frontier", "reasoning", "1m-context"], size: "550B", quant: "GGUF", vram_gb: 330 },
  { repo: "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8", desc: "Nemotron 3 Super 120B for collaborative agents. FP8 quantized", tags: ["nemotron", "agentic", "fp8"], size: "120B", quant: "FP8", vram_gb: 60 },
  { repo: "nvidia/Nemotron-Cascade-2-30B-A3B",           desc: "Nemotron Cascade 2 with multi-domain on-policy distillation", tags: ["nemotron", "cascade", "distillation", "rl"], size: "30B", quant: "BF16", vram_gb: 60 },
  { repo: "nvidia/OpenReasoning-Nemotron-32B",           desc: "NVIDIA OpenReasoning on Qwen2.5 32B base. MathArena 84.85", tags: ["nemotron", "reasoning", "qwen2.5"], size: "32B", quant: "BF16", vram_gb: 64 },
  { repo: "LGAI-EXAONE/EXAONE-4.0-32B-GGUF",              desc: "LG EXAONE 4.0 32B Korean-English MoE. 256K context, SuperBPE", tags: ["exaone", "korean", "moe", "256k"], size: "32B", quant: "GGUF", vram_gb: 20 },
  { repo: "LGAI-EXAONE/EXAONE-4.0-1.2B-GGUF",             desc: "EXAONE 4.0 1.2B edge variant. Korean-English", tags: ["exaone", "korean", "edge"], size: "1.2B", quant: "GGUF", vram_gb: 0.8 },
  { repo: "moonshotai/Kimi-VL-A3B-Thinking-2506",         desc: "Kimi VL A3B thinking variant. Multimodal agentic", tags: ["kimi", "vl", "thinking", "multimodal"], size: "A3B", quant: "BF16", vram_gb: 6 },
  { repo: "NCSOFT/VARCO-VISION-2.0-14B",                 desc: "NCSoft VARCO Vision 2.0 on Qwen3 14B. Vision-language", tags: ["varco", "vision", "qwen3", "vl"], size: "14B", quant: "BF16", vram_gb: 28 },
  { repo: "Goedel-LM/Goedel-Prover-V2-32B",              desc: "Goedel Prover V2 on Qwen3 32B for formal mathematics", tags: ["prover", "math", "qwen3", "formal"], size: "32B", quant: "BF16", vram_gb: 64 },
  { repo: "dphn/Dolphin3.0-R1-Mistral-24B",              desc: "Dolphin3 R1 on Mistral 24B base. Reasoning-enhanced", tags: ["dolphin3", "mistral", "r1", "reasoning"], size: "24B", quant: "BF16", vram_gb: 48 },
  { repo: "dphn/Dolphin-Mistral-24B-Venice-Edition",     desc: "Dolphin Mistral 24B Venice Edition. Style-tuned", tags: ["dolphin", "mistral", "venice", "style"], size: "24B", quant: "BF16", vram_gb: 48 },
  { repo: "Jackrong/Qwopus-GLM-18B-Merged-GGUF",         desc: "Frankenmerge of Qwopus3.5-9B + GLM5.1. Experimental", tags: ["frankenmerge", "passthrough", "glm", "qwen"], size: "18B", quant: "GGUF", vram_gb: 11 },
  { repo: "DuoNeural/Cosmos3-Nano-GPTQ-4bit",            desc: "Cosmos3 Nano GPTQ 4bit for exllama loaders", tags: ["cosmos3", "gptq", "nano", "exllama"], size: "15B", quant: "GPTQ", vram_gb: 8 },
  { repo: "nvidia/Nemotron-Personas-Japan",              desc: "6M personas rooted in Japanese demographics. 1500+ occupations", tags: ["nemotron", "personas", "japanese", "synthetic"], size: "dataset", quant: "N/A", vram_gb: 0 },
];

function banner(t: string) {
  const p = "═".repeat(Math.max(0, 60 - t.length));
  console.log(`\n${MAG}${BOLD}╔══════════════════════════════════════════════════════════════╗${RST}`);
  console.log(`${MAG}${BOLD}║  ${t.padEnd(56)}  ║${RST}`);
  console.log(`${MAG}${BOLD}╚══════════════════════════════════════════════════════════════╝${RST}`);
}
function section(l: string) { console.log(`\n${CYN}${BOLD}[${l}]${RST}`); console.log(`${DIM}${"─".repeat(62)}${RST}`); }
function kv(k: string, v: string, alert = false) { const c = alert ? RED : GRN; console.log(`  ${BLU}${k.padEnd(22)}${RST} ${c}${v}${RST}`); }
function warn(m: string) { console.log(`  ${YEL}⚠ ${m}${RST}`); }
function crit(m: string) { console.log(`  ${RED}✖ ${m}${RST}`); }

async function sh(cmd: string[]): Promise<string> {
  const p = spawn(cmd, { stdout: "pipe", stderr: "pipe" });
  const o = await new Response(p.stdout).text();
  const e = await new Response(p.stderr).text();
  const c = await p.exited;
  if (c !== 0) return e.trim() || o.trim() || "";
  return o.trim();
}

function generateLaunchCommand(model: any, port: number): string {
  if (model.quant === "GGUF") {
    return `/home/toxic/beellama.cpp/build/bin/llama-server -hf ${model.repo} --port ${port} -ngl 999 --metrics`;
  } else if (model.quant === "FP8") {
    return `vllm serve ${model.repo} --port ${port} --quantization fp8`;
  } else if (model.quant === "GPTQ") {
    return `python3 -m exllamav2 ${model.repo} --port ${port}`;
  } else {
    return `/home/toxic/beellama.cpp/build/bin/llama-server -hf ${model.repo} --port ${port} -ngl 999 --metrics`;
  }
}

async function auditHFModels() {
  banner("HF WEIRD FINETUNES & EMERGENT MODELS");
  section("Model Registry (June 2026)");
  for (const m of HF_WEIRD_MODELS) {
    const port = 45080 + HF_WEIRD_MODELS.indexOf(m);
    const vramAlert = m.vram_gb > 24;
    console.log(`${GRN}●${RST} ${YEL}${m.repo}${RST}`);
    kv("  Size", m.size);
    kv("  Quant", m.quant);
    kv("  Est VRAM", `${m.vram_gb} GB`, vramAlert);
    kv("  Tags", m.tags.join(", "));
    kv("  Port", String(port));
    console.log(`  ${DIM}${m.desc}${RST}`);
    console.log(`  ${CYN}Launch:${RST} ${DIM}${generateLaunchCommand(m, port)}${RST}`);
    console.log("");
  }
}

async function auditHFDisk() {
  banner("HF CACHE & DISK");
  const cacheDir = process.env.HF_HOME || "/home/toxic/.cache/huggingface";
  const du = await sh(["du", "-sh", cacheDir]).catch(() => "unknown");
  kv("HF Cache Size", du);
  const modelsDir = "/home/toxic/models";
  const modelsDu = await sh(["du", "-sh", modelsDir]).catch(() => "not found");
  kv("Local Models", modelsDu);
}

async function auditHFCLI() {
  banner("HF CLI STATUS");
  const version = await sh(["hf", "--version"]).catch(() => "not installed");
  kv("hf CLI", version);
  const whoami = await sh(["hf", "whoami"]).catch(() => "not logged in");
  kv("HF User", whoami);
}

async function generateDownloadScript() {
  banner("GENERATE DOWNLOAD SCRIPT");
  let script = "#!/bin/bash\n# Auto-generated HF model download script\n# Generated by subagent-c-hf-models.ts\n\n";
  for (const m of HF_WEIRD_MODELS) {
    if (m.size === "dataset") continue;
    const dir = m.repo.replace(/\//g, "_");
    script += `# ${m.repo} (${m.size}, ${m.quant}, ~${m.vram_gb}GB VRAM)\n`;
    script += `hf model download ${m.repo} --local-dir /home/toxic/models/${dir}\n\n`;
  }
  console.log(`${DIM}${script}${RST}`);
  section("Save to download-models.sh");
  console.log(`  echo "${script}" > download-models.sh && chmod +x download-models.sh`);
}

async function generateMergekitConfig() {
  banner("MERGEKIT FRANKENMERGE CONFIG");
  const config = `slices:
  - sources:
    - model: Qwen/Qwen3.5-0.8B
      layer_range: [0, 24]
  - sources:
    - model: unsloth/Qwen3.5-35B-A3B-GGUF
      layer_range: [16, 32]
merge_method: passthrough
dtype: bfloat16
`;
  console.log(`${DIM}${config}${RST}`);
  section("Save to merge-config.yml");
  console.log(`  cat > merge-config.yml << 'EOF'\n${config}EOF\n  mergekit-yaml merge-config.yml ./frankenmodel --cuda`);
}

async function run() {
  console.log(`${MAG}${BOLD}
   ____                            __   _       __  ___      __  _
  / __/___  _______  ___ ___ ____/ /  | | /| / / / _ \\___ / /_(_)__  ___ _
 / _// _ \\/ __/ _ \\/ -_) _ \\/ _  /   | |/ |/ / / ___/ -_) __/ / _ \\/ _ \\
/___/\\___/\\_/\\___/\\__/\\___/\\_,_/    |__/|__/_/_/   \\__/\\__/_/\\___/\\_, /
                                                                  /___/
  SUBAGENT C — HF MODEL DISCOVERY & DEPLOYER — 2026 — v2.0.0
  Weird Finetunes | Emergent Models | Abliterated | Frankenmerge | HF CLI
${RST}`);
  await auditHFModels(); await auditHFDisk(); await auditHFCLI();
  await generateDownloadScript(); await generateMergekitConfig();
  banner("SUBAGENT C COMPLETE");
  console.log(`${DIM}Run:  bun run subagent-c-hf-models.ts${RST}`);
  console.log(`${DIM}Time: ${new Date().toISOString()}${RST}\n`);
}

run().catch(e => { console.error(e); process.exit(1); });
