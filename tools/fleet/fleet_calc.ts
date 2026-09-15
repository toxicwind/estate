import type { SsmParams, MlaParams } from "./fleet_types.ts";

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

export function calculateSsmStateSize(p: SsmParams): number {
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

export function calculateRecurrentCacheSize(
  ssmStateSize: number,
  ctx: number,
  nSeqMax?: number,
): number {
  const stateSlots = Math.min(Math.max(1, nSeqMax || ctx), ctx);
  return ssmStateSize * stateSlots * 4; // sizeof(float) = 4 bytes
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

export function ggmlRowSize(type: string, n: number): number {
  switch (type.toLowerCase()) {
    case "f32":
      return n * 4;
    case "f16":
      return n * 2;
    case "bf16":
      return n * 2;
    case "q8_0":
      return Math.ceil(n / 32) * 34;
    case "q4_0":
      return Math.ceil(n / 32) * 18;
    case "q4_1":
      return Math.ceil(n / 32) * 20;
    case "q5_0":
      return Math.ceil(n / 32) * 22;
    case "q5_1":
      return Math.ceil(n / 32) * 24;
    case "q2_k":
      return Math.ceil(n / 256) * 96; // approximate
    case "q3_k":
      return Math.ceil(n / 256) * 110; // approximate
    case "q4_k":
      return Math.ceil(n / 256) * 144;
    case "q5_k":
      return Math.ceil(n / 256) * 176;
    case "q6_k":
      return Math.ceil(n / 256) * 210;
    case "q8_k":
      return Math.ceil(n / 256) * 292;
    case "iq4_nl":
      return Math.ceil(n / 32) * 18;
    default:
      return n * 2; // default to f16
  }
}

export function calculateMlaKvSize(p: MlaParams): number {
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
