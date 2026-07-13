#!/usr/bin/env bun
// fleet_universal_maximal.ts — parses EVERYTHING from ik_llama.cpp, works for ANY model
// Architecture-aware flag selection, exact log format matching, source-derived formulas
// Includes: SSM state size calculation, MLA kv_lora_rank parsing, recurrent layer detection

import { $ } from "bun";
import { writeFile } from "node:fs/promises";

const HOME = "/home/toxic";
const SERVER = `${HOME}/ik_llama.cpp-main/build/bin/llama-server`;
const PORT = 28080;
const REPORT = `${HOME}/sovereign/fleet_maximal.json`;

// ═══════════════════════════════════════════════════════════════════════════════
// ARCHITECTURE CONFIGURATION MAP — derived from ik_llama.cpp source
// ═══════════════════════════════════════════════════════════════════════════════

interface ArchConfig {
  name: string;
  isMla: boolean;
  isHybrid: boolean;
  isRecurrent: boolean;
  isMoe: boolean;
  mlaDefault: number;
  flashAttnRecommended: boolean;
  cacheTypeK: string;
  cacheTypeV: string;
  fusedMoe: boolean;
  groupedExpertRouting: boolean;
  attnMaxBatch: number;
  runtimeRepack: boolean;
  overrideTensors?: string[];
  extraFlags: string[];
}

const ARCH_CONFIG: Record<string, ArchConfig> = {
  "deepseek2": {
    name: "DeepSeek-V2/V3/R1",
    isMla: true, isHybrid: false, isRecurrent: false, isMoe: true,
    mlaDefault: 2, flashAttnRecommended: true,
    cacheTypeK: "q8_0", cacheTypeV: "q8_0",
    fusedMoe: true, groupedExpertRouting: false, attnMaxBatch: 512,
    runtimeRepack: true,
    overrideTensors: ["exps=CPU"],
    extraFlags: ["--parallel", "1"],
  },
  "deepseek": {
    name: "DeepSeek-V1",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: true,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: true, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "qwen3next": {
    name: "Qwen3-Next (hybrid)",
    isMla: false, isHybrid: true, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "qwen35moe": {
    name: "Qwen3.5-MoE",
    isMla: false, isHybrid: true, isRecurrent: false, isMoe: true,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: true, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "qwen35": {
    name: "Qwen3.5",
    isMla: false, isHybrid: true, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "qwen2": {
    name: "Qwen2",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "qwen2moe": {
    name: "Qwen2-MoE",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: true,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: true, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "llama": {
    name: "Llama",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "llama4": {
    name: "Llama 4",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: true,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: true, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "mistral3": {
    name: "Mistral 3",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "mistral4": {
    name: "Mistral 4 (MLA)",
    isMla: true, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 2, flashAttnRecommended: true,
    cacheTypeK: "q8_0", cacheTypeV: "q8_0",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 256,
    runtimeRepack: false,
    extraFlags: [],
  },
  "gemma": {
    name: "Gemma",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "gemma2": {
    name: "Gemma 2",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "gemma3": {
    name: "Gemma 3",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "gemma4": {
    name: "Gemma 4",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "gemma4_mtp": {
    name: "Gemma 4 MTP",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: ["--mtp"],
  },
  "mamba": {
    name: "Mamba",
    isMla: false, isHybrid: false, isRecurrent: true, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: false,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "phi2": {
    name: "Phi-2",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "phi3": {
    name: "Phi-3",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "glm4": {
    name: "GLM-4",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "glm4_moe": {
    name: "GLM-4-MoE",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: true,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: true, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "glm_dsa": {
    name: "GLM-DSA (MLA)",
    isMla: true, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 2, flashAttnRecommended: true,
    cacheTypeK: "q8_0", cacheTypeV: "q8_0",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 256,
    runtimeRepack: false,
    extraFlags: [],
  },
  "cohere2": {
    name: "Cohere 2",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "cohere2_moe": {
    name: "Cohere 2 MoE",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: true,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: true, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "bailingmoe2": {
    name: "BailingMoE2 (Ling/Ring)",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: true,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: true, groupedExpertRouting: true, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "granite": {
    name: "Granite",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "granite_moe": {
    name: "Granite MoE",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: true,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: true, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
  "unknown": {
    name: "Unknown",
    isMla: false, isHybrid: false, isRecurrent: false, isMoe: false,
    mlaDefault: 0, flashAttnRecommended: true,
    cacheTypeK: "f16", cacheTypeV: "f16",
    fusedMoe: false, groupedExpertRouting: false, attnMaxBatch: 0,
    runtimeRepack: false,
    extraFlags: [],
  },
};

function getArchConfig(arch: string): ArchConfig {
  const key = arch?.toLowerCase().replace(/[^a-z0-9]/g, "") || "unknown";
  if (ARCH_CONFIG[key]) return ARCH_CONFIG[key];
  for (const [k, v] of Object.entries(ARCH_CONFIG)) {
    if (key.includes(k) || k.includes(key)) return v;
  }
  return ARCH_CONFIG["unknown"];
}

// ═══════════════════════════════════════════════════════════════════════════════
// SSM STATE SIZE CALCULATION — derived from llama-hparams.h:n_embd_v_s()
// ═══════════════════════════════════════════════════════════════════════════════

interface SsmParams {
  ssm_d_conv: number;
  ssm_d_inner: number;
  ssm_d_state: number;
  ssm_dt_rank: number;
  ssm_n_group: number;
}

/**
 * Calculate recurrent state size per sequence slot.
 * From llama-hparams.h:282-297
 * 
 * For Qwen3-Next style hybrid (ssm_n_group > 0):
 *   conv_state_dim = (ssm_d_conv - 1) * (2 * ssm_d_state * ssm_n_group + ssm_d_inner)
 *   head_v_dim = ssm_d_inner / ssm_dt_rank
 *   ssm_state_dim = head_v_dim * head_v_dim * ssm_dt_rank
 *   total = conv_state_dim + ssm_state_dim
 * 
 * For pure Mamba (ssm_n_group == 0):
 *   total = ssm_d_state * ssm_d_inner
 */
function calculateSsmStateSize(p: SsmParams): number {
  if (p.ssm_n_group > 0) {
    // Qwen3-Next style hybrid recurrent state
    const key_dim = p.ssm_d_state * p.ssm_n_group;
    const value_dim = p.ssm_d_inner;
    const conv_dim = 2 * key_dim + value_dim;
    const conv_state_dim = (p.ssm_d_conv > 0 ? p.ssm_d_conv - 1 : 0) * conv_dim;
    const head_v_dim = p.ssm_dt_rank > 0 ? p.ssm_d_inner / p.ssm_dt_rank : 0;
    const ssm_state_dim = head_v_dim * head_v_dim * p.ssm_dt_rank;
    return conv_state_dim + ssm_state_dim;
  }
  // Pure Mamba
  return p.ssm_d_state * p.ssm_d_inner;
}

/**
 * Calculate per-layer recurrent cache size.
 * From llama-model.cpp:2062-2064
 *   size = n_embd_v_s * state_slots * sizeof(float)
 *   state_slots = min(max(1, n_seq_max), kv_size)
 * 
 * For our purposes (single sequence): state_slots = min(ctx, 1) effectively = 1
 * But at max ctx: state_slots = ctx (capped by n_seq_max which defaults to ctx)
 */
function calculateRecurrentCacheSize(ssmStateSize: number, ctx: number, nSeqMax?: number): number {
  const stateSlots = Math.min(Math.max(1, nSeqMax || ctx), ctx);
  return ssmStateSize * stateSlots * 4; // sizeof(float) = 4 bytes
}

// ═══════════════════════════════════════════════════════════════════════════════
// MLA KV CACHE FORMULA — derived from llama-model.cpp:2066-2078
// ═══════════════════════════════════════════════════════════════════════════════

interface MlaParams {
  kvLoraRank: number;
  nEmbdHeadQkRope: number; // n_rot
  nLayer: number;
  ctx: number;
  cacheTypeK: string;
  cacheTypeV: string;
  mlaMode: number;
  flashAttn: boolean;
}

/**
 * Calculate MLA KV cache size per layer.
 * From llama-model.cpp cache_size():
 * 
 * If flash_attn:
 *   size = ggml_row_size(type_k, kv_lora_rank + n_embd_head_qk_rope) * ctx
 * 
 * If mla_attn == 1:
 *   kv_type = type_k
 *   size = ggml_row_size(kv_type, kv_lora_rank + n_embd_head_qk_rope) * ctx
 *        + ggml_row_size(type_v, kv_lora_rank * ctx)
 * 
 * If mla_attn == 2 or 3:
 *   kv_type = type_v
 *   size = ggml_row_size(kv_type, kv_lora_rank + n_embd_head_qk_rope) * ctx
 * 
 * ggml_row_size(type, n) = n * type_size / block_size
 * For F16: type_size=2, block_size=1 -> row_size = n * 2
 * For Q8_0: type_size=34, block_size=32 -> row_size = ceil(n/32) * 34
 * For Q4_0: type_size=18, block_size=32 -> row_size = ceil(n/32) * 18
 */
function ggmlRowSize(type: string, n: number): number {
  switch (type.toLowerCase()) {
    case "f32": return n * 4;
    case "f16": return n * 2;
    case "bf16": return n * 2;
    case "q8_0": return Math.ceil(n / 32) * 34;
    case "q4_0": return Math.ceil(n / 32) * 18;
    case "q4_1": return Math.ceil(n / 32) * 20;
    case "q5_0": return Math.ceil(n / 32) * 22;
    case "q5_1": return Math.ceil(n / 32) * 24;
    case "q2_k": return Math.ceil(n / 256) * 96; // approximate
    case "q3_k": return Math.ceil(n / 256) * 110; // approximate
    case "q4_k": return Math.ceil(n / 256) * 144;
    case "q5_k": return Math.ceil(n / 256) * 176;
    case "q6_k": return Math.ceil(n / 256) * 210;
    case "q8_k": return Math.ceil(n / 256) * 292;
    case "iq4_nl": return Math.ceil(n / 32) * 18;
    default: return n * 2; // default to f16
  }
}

function calculateMlaKvSize(p: MlaParams): number {
  const latentDim = p.kvLoraRank + p.nEmbdHeadQkRope;

  if (p.flashAttn) {
    // Flash attention: single buffer with type_k
    return ggmlRowSize(p.cacheTypeK, latentDim) * p.ctx;
  }

  if (p.mlaMode === 1) {
    // MLA mode 1: CPU-only, separate c^KV and kv^T
    const ckvSize = ggmlRowSize(p.cacheTypeK, latentDim) * p.ctx;
    const kvTSize = ggmlRowSize(p.cacheTypeV, p.kvLoraRank * p.ctx);
    return ckvSize + kvTSize;
  }

  // MLA mode 2 or 3: c^KV only, type_v
  return ggmlRowSize(p.cacheTypeV, latentDim) * p.ctx;
}

// ═══════════════════════════════════════════════════════════════════════════════
// LOG FORMAT MATCHING — exact regexes from ik_llama.cpp source analysis
// ═══════════════════════════════════════════════════════════════════════════════

interface LayerInfo {
  index: number;
  weights: number;
  kv: number;
  total: number;
  compute: number;
  output: boolean;
}

interface FullMetrics {
  arch?: string;
  modelName?: string;
  vramTotal?: number;
  vramFree?: number;
  nLayer?: number;
  nHead?: number;
  nHeadKv?: number;
  nEmbd?: number;
  headDim?: number;
  headDimV?: number;
  modelSizeMiB?: number;
  modelSizeGiB?: number;
  bpw?: number;
  nCtx?: number;
  nBatch?: number;
  nUbatch?: number;
  trainCtx?: number;
  kvSizeMiB?: number;
  kvCacheTypeK?: string;
  kvCacheTypeV?: string;
  kvCTotal?: number;
  kvTTotal?: number;
  computeMiB?: number;
  outputBufferMiB?: number;
  memRequired?: number;
  memAvailable?: number;
  cpuBuffer?: number;
  gpuBuffer?: number;
  graphNodes?: number;
  graphSplits?: number;
  slidingWindow?: number;
  swaPattern?: number;
  nLayerDenseLead?: number;
  ssmEnabled?: boolean;
  ssmState?: number;
  ssmInner?: number;
  ssmConv?: number;
  ssmDtRank?: number;
  ssmNGroup?: number;
  mlaMode?: number;
  flashAttn?: boolean;
  fusedMoe?: boolean;
  attnMaxBatch?: number;
  // MLA-specific
  kvLoraRank?: number;
  nLoraQ?: number;
  nRot?: number;
  nFfExp?: number;
  nExpertShared?: number;
  expertWeightsScale?: number;
  expertWeightsNorm?: number;
  // Layer analysis
  layers?: LayerInfo[];
  layerPattern?: {
    uniqueKvSizes: number;
    kvSizes: number[];
    isHybrid: boolean;
    interval?: number;
    weightsPattern?: string;
    recurrentLayers?: number[];
    attentionLayers?: number[];
  };
  // Calculated
  kvPerTokenKiB?: number;
  theoreticalMax?: number;
  ssmStateSize?: number;
  ssmCacheSizePerLayer?: number;
  mlaTheoreticalKvPerLayer?: number;
}

function parseLayerTable(log: string): LayerInfo[] {
  const layers: LayerInfo[] = [];
  const reNormal = /Layer\s+(\d+):\s+([\d.]+),\s+([\d.]+),\s+([\d.]+)\s+([\d.]+)\s+MiB/g;
  let m;
  while ((m = reNormal.exec(log)) !== null) {
    layers.push({
      index: parseInt(m[1]),
      weights: parseFloat(m[2]),
      kv: parseFloat(m[3]),
      total: parseFloat(m[4]),
      compute: parseFloat(m[5]),
      output: false,
    });
  }
  const reOutput = /Layer\s+(\d+):\s+([\d.]+),\s+([\d.]+),\s+([\d.]+)\s+MiB\s+\(output layer\)/;
  const outMatch = log.match(reOutput);
  if (outMatch) {
    layers.push({
      index: parseInt(outMatch[1]),
      weights: parseFloat(outMatch[2]),
      kv: parseFloat(outMatch[3]),
      total: parseFloat(outMatch[4]),
      compute: 0,
      output: true,
    });
  }
  return layers.sort((a, b) => a.index - b.index);
}

function parseFullMetrics(log: string): FullMetrics {
  const m: FullMetrics = {};
  const get = (re: RegExp, fn: ((s: string) => any) = parseFloat) => {
    const match = log.match(re);
    return match ? fn(match[1]) : undefined;
  };
  const getStr = (re: RegExp) => {
    const match = log.match(re);
    return match ? match[1] : undefined;
  };

  // Architecture info
  m.arch = getStr(/arch\s+=\s+(\S+)/);
  m.modelName = getStr(/general\.name\s+=\s+'([^']+)'/);
  m.trainCtx = get(/n_ctx_train\s+=\s+(\d+)/);
  m.nEmbd = get(/n_embd\s+=\s+(\d+)/);
  m.nLayer = get(/n_layer\s+=\s+(\d+)/);

  const nHeadStr = getStr(/n_head\s+=\s+([\d,\s]+)/);
  if (nHeadStr) {
    const first = nHeadStr.split(",")[0].trim();
    m.nHead = parseInt(first) || undefined;
  }
  const nHeadKvStr = getStr(/n_head_kv\s+=\s+([\d,\s]+)/);
  if (nHeadKvStr) {
    const first = nHeadKvStr.split(",")[0].trim();
    m.nHeadKv = parseInt(first) || undefined;
  }

  m.slidingWindow = get(/n_swa\s+=\s+(\d+)/);
  m.swaPattern = get(/n_swa_pattern\s+=\s+(\d+)/);
  m.headDim = get(/n_embd_head_k\s+=\s+(\d+)/);
  m.headDimV = get(/n_embd_head_v\s+=\s+(\d+)/);
  m.nRot = get(/n_rot\s+=\s+(\d+)/);
  m.nLayerDenseLead = get(/n_layer_dense_lead\s+=\s+(\d+)/);

  // SSM parameters
  m.ssmConv = get(/ssm_d_conv\s+=\s+(\d+)/);
  m.ssmInner = get(/ssm_d_inner\s+=\s+(\d+)/);
  m.ssmState = get(/ssm_d_state\s+=\s+(\d+)/);
  m.ssmDtRank = get(/ssm_dt_rank\s+=\s+(\d+)/);
  m.ssmNGroup = get(/ssm_n_group\s+=\s+(\d+)/);
  m.ssmEnabled = !!(m.ssmState || m.ssmInner);

  // MLA parameters (only logged for is_mla_model())
  m.kvLoraRank = get(/n_lora_kv\s+=\s+(\d+)/);
  m.nLoraQ = get(/n_lora_q\s+=\s+(\d+)/);
  m.nFfExp = get(/n_ff_exp\s+=\s+(\d+)/);
  m.nExpertShared = get(/n_expert_shared\s+=\s+(\d+)/);
  m.expertWeightsScale = get(/expert_weights_scale\s+=\s+([\d.]+)/);
  m.expertWeightsNorm = get(/expert_weights_norm\s+=\s+(\d+)/);

  // Model size
  m.modelSizeGiB = get(/model size\s+=\s+([\d.]+)\s+GiB/);
  m.modelSizeMiB = get(/model size\s+=\s+([\d.]+)\s+MiB/);
  m.bpw = get(/model size\s+=\s+[\d.]+\s+(?:MiB|GiB)\s+\(([\d.]+)\s+BPW\)/);

  // Context
  m.nCtx = get(/n_ctx\s+=\s+(\d+)/);
  m.nBatch = get(/n_batch\s+=\s+(\d+)/);
  m.nUbatch = get(/n_ubatch\s+=\s+(\d+)/);

  // KV cache — three formats
  const kvMla = log.match(/KV self size\s+=\s+([\d.]+)\s+MiB,\s+c\^KV\s+\(([^)]+)\):\s+([\d.]+)\s+MiB,\s+kv\^T\s+\(([^)]+)\):\s+([\d.]+)\s+MiB/);
  const kvMlaNoT = log.match(/KV self size\s+=\s+([\d.]+)\s+MiB,\s+c\^KV\s+\(([^)]+)\):\s+([\d.]+)\s+MiB,\s+kv\^T:\s+not used/);
  const kvStandard = log.match(/KV self size\s+=\s+([\d.]+)\s+MiB,\s+K\s+\(([^)]+)\):\s+([\d.]+)\s+MiB,\s+V\s+\(([^)]+)\):\s+([\d.]+)\s+MiB/);

  if (kvMla) {
    m.kvSizeMiB = parseFloat(kvMla[1]);
    m.kvCacheTypeK = kvMla[2];
    m.kvCTotal = parseFloat(kvMla[3]);
    m.kvCacheTypeV = kvMla[4];
    m.kvTTotal = parseFloat(kvMla[5]);
  } else if (kvMlaNoT) {
    m.kvSizeMiB = parseFloat(kvMlaNoT[1]);
    m.kvCacheTypeK = kvMlaNoT[2];
    m.kvCTotal = parseFloat(kvMlaNoT[3]);
    m.kvTTotal = 0;
  } else if (kvStandard) {
    m.kvSizeMiB = parseFloat(kvStandard[1]);
    m.kvCacheTypeK = kvStandard[2];
    m.kvCTotal = parseFloat(kvStandard[3]);
    m.kvCacheTypeV = kvStandard[4];
    m.kvTTotal = parseFloat(kvStandard[5]);
  }

  // Compute buffer
  const computeMatch = log.match(/(\S+)\s+compute buffer size\s+=\s+([\d.]+)\s+MiB/);
  if (computeMatch) {
    m.computeMiB = parseFloat(computeMatch[2]);
  }

  // Output buffer
  const outBufMatch = log.match(/output buffer size\s+=\s+([\d.]+)\s+MiB/);
  if (outBufMatch) {
    m.outputBufferMiB = parseFloat(outBufMatch[1]);
  }

  // Memory
  m.memRequired = get(/Memory required for model tensors \+ cache:\s+([\d.]+)\s+MiB/);
  m.memAvailable = get(/Memory available on all devices - compute:\s+([\d.]+)\s+MiB/);

  // VRAM
  const vramMatch = log.match(/using device\s+(\S+)\s+-\s+(\d+)\s+MiB free/);
  if (vramMatch) {
    m.vramFree = parseInt(vramMatch[2]);
  }

  // Graph
  m.graphNodes = get(/graph nodes\s+=\s+(\d+)/);
  m.graphSplits = get(/graph splits\s+=\s+(\d+)/);

  // Runtime flags
  m.flashAttn = log.includes("flash_attn = 1");
  m.mlaMode = get(/mla_attn\s+=\s+(\d)/);
  m.fusedMoe = log.includes("fused_moe  = 1");
  m.attnMaxBatch = get(/attn_max_b\s+=\s+(\d+)/);

  // Layer table
  m.layers = parseLayerTable(log);

  // ═══ SSM state size calculation ═══
  if (m.ssmEnabled) {
    const ssmParams: SsmParams = {
      ssm_d_conv: m.ssmConv || 0,
      ssm_d_inner: m.ssmInner || 0,
      ssm_d_state: m.ssmState || 0,
      ssm_dt_rank: m.ssmDtRank || 0,
      ssm_n_group: m.ssmNGroup || 0,
    };
    m.ssmStateSize = calculateSsmStateSize(ssmParams);
    if (m.nCtx) {
      m.ssmCacheSizePerLayer = calculateRecurrentCacheSize(m.ssmStateSize, m.nCtx) / (1024 * 1024); // MiB
    }
  }

  // ═══ MLA theoretical KV per layer ═══
  if (m.kvLoraRank && m.nRot !== undefined && m.nCtx) {
    const mlaParams: MlaParams = {
      kvLoraRank: m.kvLoraRank,
      nEmbdHeadQkRope: m.nRot,
      nLayer: m.nLayer || 1,
      ctx: m.nCtx,
      cacheTypeK: m.kvCacheTypeK || "f16",
      cacheTypeV: m.kvCacheTypeV || "f16",
      mlaMode: m.mlaMode || 2,
      flashAttn: m.flashAttn || false,
    };
    m.mlaTheoreticalKvPerLayer = calculateMlaKvSize(mlaParams) / (1024 * 1024); // MiB
  }

  // Layer pattern analysis
  if (m.layers.length > 0) {
    const nonOutput = m.layers.filter(l => !l.output);
    const kvSizes = [...new Set(nonOutput.map(l => l.kv.toFixed(2)))].map(Number).sort((a, b) => a - b);

    // Detect recurrent vs attention layers from KV sizes
    // Recurrent layers have near-zero or very small KV (state is constant)
    const recurrentLayers: number[] = [];
    const attentionLayers: number[] = [];

    if (kvSizes.length >= 2) {
      const threshold = kvSizes[0] * 1.5 + 0.01;
      for (const layer of nonOutput) {
        if (layer.kv < threshold) {
          recurrentLayers.push(layer.index);
        } else {
          attentionLayers.push(layer.index);
        }
      }
    }

    m.layerPattern = {
      uniqueKvSizes: kvSizes.length,
      kvSizes,
      isHybrid: kvSizes.length > 1 || !!m.nLayerDenseLead || (m.arch && getArchConfig(m.arch).isHybrid),
      recurrentLayers: recurrentLayers.length > 0 ? recurrentLayers : undefined,
      attentionLayers: attentionLayers.length > 0 ? attentionLayers : undefined,
    };

    if (kvSizes.length === 2) {
      const [small, large] = kvSizes;
      const largeLayers = nonOutput.filter(l => Math.abs(l.kv - large) < 0.1).map(l => l.index);
      if (largeLayers.length > 1) {
        const intervals = largeLayers.slice(1).map((v, i) => v - largeLayers[i]);
        const counts = new Map<number, number>();
        intervals.forEach(v => counts.set(v, (counts.get(v) || 0) + 1));
        let modeInterval = intervals[0];
        let modeCount = 0;
        for (const [val, count] of counts) {
          if (count > modeCount) {
            modeCount = count;
            modeInterval = val;
          }
        }
        m.layerPattern.interval = modeInterval;
      }
    }

    const weightSizes = [...new Set(nonOutput.map(l => l.weights.toFixed(2)))].map(Number);
    if (weightSizes.length > 2) {
      m.layerPattern.weightsPattern = "MoE or variable";
    }
  }

  // KV per token
  if (m.kvSizeMiB && m.nCtx && m.nCtx > 0) {
    m.kvPerTokenKiB = (m.kvSizeMiB / m.nCtx) * 1024;
  }

  return m;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PREDICTION ENGINE
// ═══════════════════════════════════════════════════════════════════════════════

interface PredictionResult {
  predicted: number;
  reasoning: string[];
  confidence: string;
  recommendedFlags: string[];
  estimatedVramAtPredicted: number;
}

function predictMax(m: FullMetrics, archConfig: ArchConfig): PredictionResult {
  const reasons: string[] = [];
  let confidence = "high";
  const flags: string[] = [];

  if (!m.vramFree || !m.modelSizeGiB || !m.kvSizeMiB || !m.nCtx) {
    return {
      predicted: 8192,
      reasoning: ["insufficient data for prediction"],
      confidence: "low",
      recommendedFlags: [],
      estimatedVramAtPredicted: 0,
    };
  }

  const kvPerToken = m.kvSizeMiB / m.nCtx;
  const modelSizeMiB = m.modelSizeGiB * 1024;
  const computeBuffer = m.computeMiB || 500;
  const outputBuffer = m.outputBufferMiB || 0;
  const safetyMargin = 512;

  const usableVram = m.vramFree - modelSizeMiB - computeBuffer - outputBuffer - safetyMargin;

  reasons.push(`Measured: ${m.kvSizeMiB.toFixed(2)} MiB KV @ ${m.nCtx} ctx = ${(kvPerToken * 1024).toFixed(4)} KiB/token`);
  reasons.push(`VRAM: ${m.vramFree} MiB free - ${modelSizeMiB.toFixed(0)} MiB model - ${computeBuffer.toFixed(0)} MiB compute - ${outputBuffer.toFixed(0)} MiB output - ${safetyMargin} MiB margin = ${usableVram.toFixed(0)} MiB usable`);

  let predicted = Math.floor(usableVram / kvPerToken);

  // ═══ SSM / Recurrent models ═══
  if (m.ssmEnabled || archConfig.isRecurrent) {
    reasons.push(`SSM/Recurrent: state_size=${m.ssmStateSize}, cache_per_layer=${m.ssmCacheSizePerLayer?.toFixed(4)} MiB`);
    reasons.push(`SSM memory is CONSTANT (not per-token) — context can scale to training limit`);
    // For pure SSM, KV cache is essentially just the state slots
    // The measured kvSizeMiB already includes this, so prediction is accurate
    // But we should cap at training context since state slots = min(ctx, n_seq_max)
    confidence = "very high";
    flags.push("--no-flash-attn");

    if (m.ssmNGroup && m.ssmNGroup > 0) {
      reasons.push(`Hybrid SSM (Qwen3-Next style): conv_state + delta-net state = ${m.ssmStateSize} floats`);
    } else if (m.ssmState && m.ssmInner) {
      reasons.push(`Pure Mamba: ssm_state = ${m.ssmState} * ${m.ssmInner} = ${m.ssmStateSize} floats`);
    }
  }

  // ═══ Hybrid models ═══
  if (m.layerPattern?.isHybrid || archConfig.isHybrid) {
    reasons.push(`Hybrid architecture: ${m.layerPattern?.uniqueKvSizes || 1} distinct layer KV sizes`);
    if (m.layerPattern?.recurrentLayers && m.layerPattern?.attentionLayers) {
      reasons.push(`Recurrent layers: [${m.layerPattern.recurrentLayers.join(",")}] (${m.layerPattern.recurrentLayers.length} layers)`);
      reasons.push(`Attention layers: [${m.layerPattern.attentionLayers.join(",")}] (${m.layerPattern.attentionLayers.length} layers)`);
    }
    if (m.layerPattern?.interval) {
      reasons.push(`Pattern: every ${m.layerPattern.interval} layers use full attention`);
    }
    if (m.nLayerDenseLead !== undefined) {
      reasons.push(`n_layer_dense_lead = ${m.nLayerDenseLead} (first N layers are dense attention)`);
    }
    confidence = "very high";
  }

  // ═══ Sliding window ═══
  if (m.slidingWindow && m.slidingWindow > 0) {
    reasons.push(`Sliding window: n_swa=${m.slidingWindow}, pattern=${m.swaPattern || 1}`);
    const effectiveCap = (m.trainCtx || 131072) * 1.5;
    if (predicted > effectiveCap) {
      reasons.push(`SWA caps effective context at ~${effectiveCap.toLocaleString()} tokens`);
      predicted = Math.min(predicted, effectiveCap);
    }
    confidence = "high";
  }

  // ═══ MLA models ═══
  if (archConfig.isMla || m.mlaMode) {
    const mlaMode = m.mlaMode || archConfig.mlaDefault;
    reasons.push(`MLA attention: mode=${mlaMode} (0=off, 1=CPU, 2=CPU+GPU, 3=CPU-only)`);

    if (m.kvLoraRank && m.nRot !== undefined) {
      reasons.push(`MLA params: kv_lora_rank=${m.kvLoraRank}, n_rot=${m.nRot}, latent_dim=${m.kvLoraRank + m.nRot}`);
      if (m.mlaTheoreticalKvPerLayer) {
        reasons.push(`Theoretical MLA KV per layer @ ${m.nCtx} ctx: ${m.mlaTheoreticalKvPerLayer.toFixed(4)} MiB`);
        const measuredPerLayer = m.kvSizeMiB / (m.nLayer || 1);
        const ratio = measuredPerLayer / m.mlaTheoreticalKvPerLayer;
        reasons.push(`Measured/theoretical per layer: ${(ratio * 100).toFixed(1)}%`);
      }
    }

    if (mlaMode >= 2) {
      reasons.push(`MLA+FlashAttn dramatically reduces KV cache vs standard attention`);
      confidence = "very high";
    }
    if (mlaMode === 3) {
      reasons.push(`MLA mode 3: minimal VRAM, CPU handles attention`);
    }
  }

  // ═══ MoE models ═══
  if (archConfig.isMoe || m.layerPattern?.weightsPattern === "MoE or variable") {
    reasons.push(`MoE architecture — expert layers have variable weight sizes`);
    if (m.nFfExp) {
      reasons.push(`n_ff_exp = ${m.nFfExp} (expert FFN dimension)`);
    }
    if (m.nExpertShared !== undefined) {
      reasons.push(`n_expert_shared = ${m.nExpertShared}`);
    }
    if (archConfig.fusedMoe) {
      flags.push("--fused-moe");
      reasons.push(`Fused MoE enabled`);
    }
    if (archConfig.groupedExpertRouting) {
      flags.push("--grouped-expert-routing");
      reasons.push(`Grouped expert routing enabled`);
    }
    if (archConfig.overrideTensors) {
      for (const ot of archConfig.overrideTensors) {
        flags.push("--override-tensor", ot);
      }
    }
  }

  // Training context cap
  if (m.trainCtx) {
    const capped = Math.min(predicted, m.trainCtx);
    if (capped < predicted) {
      reasons.push(`Capped at training context: ${m.trainCtx.toLocaleString()}`);
    }
    predicted = capped;
  }

  // Sanity check: theoretical KV per token vs measured (standard attention only)
  if (m.nLayer && m.nHeadKv && m.headDim && !archConfig.isMla && !archConfig.isRecurrent) {
    const theoreticalKvPerToken = (2 * m.nLayer * m.nHeadKv * m.headDim * 2) / (1024 * 1024);
    const ratio = kvPerToken / theoreticalKvPerToken;
    reasons.push(`Theoretical full-attention KV: ${theoreticalKvPerToken.toFixed(4)} MiB/token`);
    reasons.push(`Measured/theoretical ratio: ${(ratio * 100).toFixed(1)}%`);

    if (ratio < 0.3) {
      reasons.push(`→ Strong evidence of MLA, hybrid, or quantized KV cache`);
    } else if (ratio > 1.5) {
      reasons.push(`→ KV cache larger than theoretical (check cache types or GQA settings)`);
    }
  }

  // Estimated VRAM at predicted context
  const estimatedKvAtPredicted = kvPerToken * predicted;
  const estimatedTotal = modelSizeMiB + estimatedKvAtPredicted + computeBuffer + outputBuffer + safetyMargin;

  // Build recommended flags
  if (archConfig.flashAttnRecommended && !m.flashAttn) {
    flags.push("--flash-attn", "1");
  }
  if (archConfig.mlaDefault > 0 && (!m.mlaMode || m.mlaMode === 0)) {
    flags.push("--mla-use", String(archConfig.mlaDefault));
  }
  if (archConfig.cacheTypeK !== "f16") {
    flags.push("--cache-type-k", archConfig.cacheTypeK);
  }
  if (archConfig.cacheTypeV !== "f16") {
    flags.push("--cache-type-v", archConfig.cacheTypeV);
  }
  if (archConfig.attnMaxBatch > 0 && (!m.attnMaxBatch || m.attnMaxBatch === 0)) {
    flags.push("--attention-max-batch", String(archConfig.attnMaxBatch));
  }
  if (archConfig.runtimeRepack) {
    flags.push("--run-time-repack");
  }
  for (const ef of archConfig.extraFlags) {
    if (!flags.includes(ef)) flags.push(ef);
  }

  return {
    predicted: Math.max(256, Math.floor(predicted)),
    reasoning: reasons,
    confidence,
    recommendedFlags: flags,
    estimatedVramAtPredicted: estimatedTotal,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// SERVER MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

async function killPort() {
  await $`pkill -9 -f llama-server`.quiet().catch(() => {});
  await $`fuser -k ${PORT}/tcp`.quiet().catch(() => {});
  await Bun.sleep(1200);
}

function buildServerCmd(modelPath: string, ctx: number, archConfig: ArchConfig, probeMetrics?: FullMetrics): string[] {
  const cmd = [
    SERVER,
    "-m", modelPath,
    "-c", String(ctx),
    "-ngl", "99",
    "--host", "127.0.0.1",
    "--port", String(PORT),
    "--no-warmup",
    "--jinja",
  ];

  if (archConfig.flashAttnRecommended) {
    cmd.push("-fa", "1");
  }
  if (archConfig.mlaDefault > 0) {
    cmd.push("-mla", String(archConfig.mlaDefault));
  }
  if (archConfig.cacheTypeK !== "f16") {
    cmd.push("-ctk", archConfig.cacheTypeK);
  }
  if (archConfig.cacheTypeV !== "f16") {
    cmd.push("-ctv", archConfig.cacheTypeV);
  }
  if (archConfig.attnMaxBatch > 0) {
    cmd.push("-amb", String(archConfig.attnMaxBatch));
  }
  if (archConfig.fusedMoe) {
    cmd.push("-fmoe");
  }
  if (archConfig.groupedExpertRouting) {
    cmd.push("-ger");
  }
  if (archConfig.runtimeRepack) {
    cmd.push("-rtr");
  }
  if (archConfig.overrideTensors) {
    for (const ot of archConfig.overrideTensors) {
      cmd.push("-ot", ot);
    }
  }
  for (const ef of archConfig.extraFlags) {
    if (!cmd.includes(ef)) cmd.push(ef);
  }
  if (probeMetrics && !probeMetrics.kvSizeMiB) {
    cmd.push("--cache-ram", "0");
  }

  return cmd;
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODEL TESTING
// ═══════════════════════════════════════════════════════════════════════════════

async function testModel(modelPath: string, ctx: number, archConfig: ArchConfig, probeMetrics?: FullMetrics) {
  await killPort();

  const cmd = buildServerCmd(modelPath, ctx, archConfig, probeMetrics);

  console.log(`\n${"=".repeat(80)}`);
  console.log(`[TEST] ${modelPath.split("/").pop()} @ ctx=${ctx.toLocaleString()}`);
  console.log(`[FLAGS] ${cmd.slice(1).join(" ")}`);
  console.log(`${"=".repeat(80)}`);

  const proc = Bun.spawn(cmd, { stdout: "pipe", stderr: "pipe" });

  let log = "";
  const collect = async (stream: ReadableStream, isErr = false) => {
    for await (const chunk of stream) {
      const text = new TextDecoder().decode(chunk);
      if (isErr) process.stderr.write(text); else process.stdout.write(text);
      log += text;
    }
  };

  collect(proc.stdout);
  collect(proc.stderr);

  let ready = false;
  for (let i = 0; i < 50; i++) {
    await Bun.sleep(400);
    if (log.includes("unable to load model") || log.includes("out of memory") || log.includes("failed to allocate")) {
      break;
    }
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/health`, { signal: AbortSignal.timeout(800) });
      if (res.ok) { ready = true; break; }
    } catch {}
  }

  let response = "";
  if (ready) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: "What is 15% of 240? Show your work step by step." }],
          max_tokens: 150,
          temperature: 0.1,
        }),
        signal: AbortSignal.timeout(45000),
      });
      const data = await res.json();
      response = data.choices?.[0]?.message?.content ?? "";
    } catch (e: any) {
      console.log(`[ERROR] Inference failed: ${e.message}`);
    }
  }

  proc.kill();
  await Bun.sleep(500);

  const metrics = parseFullMetrics(log);
  const config = getArchConfig(metrics.arch || "");
  const prediction = predictMax(metrics, config);

  console.log(`\n${"─".repeat(80)}`);
  console.log(`[ANALYSIS]`);
  console.log(` Architecture: ${metrics.arch} (${config.name})`);
  console.log(` Model: ${metrics.nLayer} layers | ${metrics.nHead} heads | ${metrics.nHeadKv} KV heads | embd=${metrics.nEmbd}`);
  console.log(` Head dims: k=${metrics.headDim}, v=${metrics.headDimV}, rot=${metrics.nRot}`);
  console.log(` Model size: ${metrics.modelSizeGiB?.toFixed(3)} GiB (${metrics.bpw?.toFixed(2)} BPW)`);
  console.log(` VRAM: ${metrics.vramFree} MiB free`);
  console.log(` Memory: ${metrics.memRequired?.toFixed(0)} MiB required, ${metrics.memAvailable?.toFixed(0)} MiB available`);
  console.log(` KV Cache: ${metrics.kvSizeMiB?.toFixed(2)} MiB @ ${metrics.nCtx} ctx (${metrics.kvPerTokenKiB?.toFixed(4)} KiB/token)`);
  console.log(` KV Types: K=${metrics.kvCacheTypeK || "?"}, V=${metrics.kvCacheTypeV || "?"}`);
  console.log(` Compute: ${metrics.computeMiB?.toFixed(2)} MiB | Output: ${metrics.outputBufferMiB?.toFixed(2)} MiB`);
  console.log(` Graph: ${metrics.graphNodes} nodes, ${metrics.graphSplits} splits`);

  // SSM info
  if (metrics.ssmEnabled) {
    console.log(`\n SSM State:`);
    console.log(`  d_conv=${metrics.ssmConv}, d_inner=${metrics.ssmInner}, d_state=${metrics.ssmState}`);
    console.log(`  dt_rank=${metrics.ssmDtRank}, n_group=${metrics.ssmNGroup}`);
    console.log(`  State size: ${metrics.ssmStateSize} floats`);
    console.log(`  Cache per layer @ ${metrics.nCtx} ctx: ${metrics.ssmCacheSizePerLayer?.toFixed(4)} MiB`);
    if (metrics.ssmNGroup && metrics.ssmNGroup > 0) {
      console.log(`  Type: Hybrid SSM (Qwen3-Next style)`);
    } else {
      console.log(`  Type: Pure Mamba`);
    }
  }

  // Hybrid info
  if (metrics.layerPattern?.isHybrid) {
    console.log(`\n Hybrid Architecture:`);
    console.log(`  ${metrics.layerPattern.uniqueKvSizes} distinct layer KV sizes`);
    console.log(`  KV sizes: ${metrics.layerPattern.kvSizes.join(", ")} MiB`);
    if (metrics.layerPattern.recurrentLayers) {
      console.log(`  Recurrent layers: [${metrics.layerPattern.recurrentLayers.join(",")}]`);
    }
    if (metrics.layerPattern.attentionLayers) {
      console.log(`  Attention layers: [${metrics.layerPattern.attentionLayers.join(",")}]`);
    }
    if (metrics.layerPattern.interval) {
      console.log(`  Pattern: every ${metrics.layerPattern.interval} layers use full attention`);
    }
    if (metrics.nLayerDenseLead !== undefined) {
      console.log(`  n_layer_dense_lead: ${metrics.nLayerDenseLead}`);
    }
  }

  // MLA info
  if (metrics.kvLoraRank) {
    console.log(`\n MLA Parameters:`);
    console.log(`  kv_lora_rank=${metrics.kvLoraRank}, n_lora_q=${metrics.nLoraQ}, n_rot=${metrics.nRot}`);
    console.log(`  latent_dim=${metrics.kvLoraRank + (metrics.nRot || 0)}`);
    if (metrics.mlaTheoreticalKvPerLayer) {
      console.log(`  Theoretical KV per layer: ${metrics.mlaTheoreticalKvPerLayer.toFixed(4)} MiB`);
    }
  }

  if (metrics.slidingWindow) {
    console.log(`\n Sliding Window: n_swa=${metrics.slidingWindow}, pattern=${metrics.swaPattern}`);
  }

  if (metrics.mlaMode !== undefined) {
    console.log(`\n MLA: mode=${metrics.mlaMode}`);
  }

  if (metrics.flashAttn) {
    console.log(` Flash Attention: enabled`);
  }

  console.log(`\n[PREDICTION] ${prediction.predicted.toLocaleString()} tokens (confidence: ${prediction.confidence})`);
  prediction.reasoning.forEach(r => console.log(` • ${r}`));

  if (prediction.recommendedFlags.length > 0) {
    console.log(`\n[RECOMMENDED FLAGS] ${prediction.recommendedFlags.join(" ")}`);
  }

  if (response) {
    console.log(`\n[RESPONSE] ${response.substring(0, 200)}${response.length > 200 ? "..." : ""}`);
  }
  console.log(`${"─".repeat(80)}\n`);

  return {
    success: ready && response.length > 20,
    metrics,
    prediction,
    response: response.substring(0, 500),
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODEL PROFILING
// ═══════════════════════════════════════════════════════════════════════════════

async function profileModel(modelPath: string) {
  const name = modelPath.split("/").pop()!;
  console.log(`\n${"#".repeat(80)}`);
  console.log(`# PROFILING: ${name}`);
  console.log(`${"#".repeat(80)}`);

  // Phase 1: Probe at 4k
  const probe = await testModel(modelPath, 4096, ARCH_CONFIG["unknown"]);
  if (!probe.metrics.kvSizeMiB) {
    console.log("[ERROR] Failed to parse metrics from probe — retrying with defaults");
    const retry = await testModel(modelPath, 4096, ARCH_CONFIG["unknown"]);
    if (!retry.metrics.kvSizeMiB) {
      console.log("[ERROR] Complete failure — model may be incompatible or OOM at 4k");
      return null;
    }
  }

  const archConfig = getArchConfig(probe.metrics.arch || "");
  console.log(`[DETECTED] Architecture: ${probe.metrics.arch} -> ${archConfig.name}`);
  console.log(`[CONFIG] MLA=${archConfig.mlaDefault}, FA=${archConfig.flashAttnRecommended}, MoE=${archConfig.isMoe}`);

  // Phase 1b: Re-probe with architecture-aware flags
  let finalProbe = probe;
  if (archConfig.mlaDefault > 0 || archConfig.flashAttnRecommended || archConfig.cacheTypeK !== "f16") {
    console.log(`\n${"=".repeat(80)}`);
    console.log("[PHASE 1b] Re-probing with architecture-aware flags");
    console.log(`${"=".repeat(80)}`);
    finalProbe = await testModel(modelPath, 4096, archConfig);
  }

  const predicted = finalProbe.prediction.predicted;
  const trainCtx = finalProbe.metrics.trainCtx || 262144;
  const testCtx = Math.min(predicted, trainCtx);

  console.log(`\n${"=".repeat(80)}`);
  console.log(`[PHASE 2] Testing predicted maximum: ${testCtx.toLocaleString()} tokens`);
  console.log(`${"=".repeat(80)}`);

  const final = await testModel(modelPath, testCtx, archConfig, finalProbe.metrics);

  return {
    model: name,
    path: modelPath,
    timestamp: new Date().toISOString(),
    architecture: {
      detected: finalProbe.metrics.arch,
      config_name: archConfig.name,
      type: finalProbe.metrics.arch,
      layers: finalProbe.metrics.nLayer,
      heads: finalProbe.metrics.nHead,
      heads_kv: finalProbe.metrics.nHeadKv,
      embedding: finalProbe.metrics.nEmbd,
      head_dim_k: finalProbe.metrics.headDim,
      head_dim_v: finalProbe.metrics.headDimV,
      n_rot: finalProbe.metrics.nRot,
      is_hybrid: finalProbe.metrics.layerPattern?.isHybrid || false,
      is_mla: archConfig.isMla,
      is_recurrent: archConfig.isRecurrent || finalProbe.metrics.ssmEnabled || false,
      is_moe: archConfig.isMoe,
      sliding_window: finalProbe.metrics.slidingWindow || 0,
      swa_pattern: finalProbe.metrics.swaPattern || 0,
      n_layer_dense_lead: finalProbe.metrics.nLayerDenseLead,
    },
    mla: {
      kv_lora_rank: finalProbe.metrics.kvLoraRank,
      n_lora_q: finalProbe.metrics.nLoraQ,
      n_ff_exp: finalProbe.metrics.nFfExp,
      n_expert_shared: finalProbe.metrics.nExpertShared,
      expert_weights_scale: finalProbe.metrics.expertWeightsScale,
      expert_weights_norm: finalProbe.metrics.expertWeightsNorm,
      theoretical_kv_per_layer_mib: finalProbe.metrics.mlaTheoreticalKvPerLayer,
    },
    ssm: {
      enabled: finalProbe.metrics.ssmEnabled || false,
      d_conv: finalProbe.metrics.ssmConv,
      d_inner: finalProbe.metrics.ssmInner,
      d_state: finalProbe.metrics.ssmState,
      dt_rank: finalProbe.metrics.ssmDtRank,
      n_group: finalProbe.metrics.ssmNGroup,
      state_size_floats: finalProbe.metrics.ssmStateSize,
      cache_per_layer_mib: finalProbe.metrics.ssmCacheSizePerLayer,
    },
    memory: {
      model_size_gib: finalProbe.metrics.modelSizeGiB,
      model_size_mib: finalProbe.metrics.modelSizeMiB,
      bpw: finalProbe.metrics.bpw,
      vram_total_mib: finalProbe.metrics.vramTotal,
      vram_free_mib: finalProbe.metrics.vramFree,
      kv_size_mib: finalProbe.metrics.kvSizeMiB,
      kv_per_token_kib: finalProbe.metrics.kvPerTokenKiB,
      kv_cache_type_k: finalProbe.metrics.kvCacheTypeK,
      kv_cache_type_v: finalProbe.metrics.kvCacheTypeV,
      compute_buffer_mib: finalProbe.metrics.computeMiB,
      output_buffer_mib: finalProbe.metrics.outputBufferMiB,
      mem_required_mib: finalProbe.metrics.memRequired,
      mem_available_mib: finalProbe.metrics.memAvailable,
    },
    context: {
      tested_4k: true,
      train_ctx: finalProbe.metrics.trainCtx,
      predicted_max: predicted,
      actual_max: final.success ? testCtx : 4096,
      prediction_accuracy: final.success ? "correct" : "overestimated",
    },
    performance: {
      graph_nodes: finalProbe.metrics.graphNodes,
      graph_splits: finalProbe.metrics.graphSplits,
    },
    flags: {
      used: buildServerCmd(modelPath, testCtx, archConfig),
      recommended: finalProbe.prediction.recommendedFlags,
    },
    layer_analysis: finalProbe.metrics.layerPattern,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

const models = (await $`find ${HOME}/models -name "*.gguf" -type f`.text())
  .trim()
  .split("\n")
  .filter(Boolean)
  .slice(0, 5);

console.log(`Found ${models.length} models to profile\n`);

const results = [];
for (const model of models) {
  try {
    const result = await profileModel(model);
    if (result) results.push(result);
  } catch (e) {
    console.error(`Failed to profile ${model}:`, e);
  }
}

results.sort((a, b) => b.context.actual_max - a.context.actual_max);

console.log("\n" + "=".repeat(80));
console.log("FINAL RESULTS");
console.log("=".repeat(80));
results.forEach(r => {
  const arch = r.architecture.is_hybrid ? "HYBRID" :
               r.architecture.is_mla ? "MLA" :
               r.architecture.is_moe ? "MoE" :
               r.architecture.is_recurrent ? "SSM" : "standard";
  console.log(`${r.context.actual_max.toString().padStart(8)} | ${r.model.padEnd(40)} | ${r.architecture.detected?.padEnd(12)} | ${arch}`);
});

await writeFile(REPORT, JSON.stringify(results, null, 2));
console.log(`\nFull report saved to: ${REPORT}`);
