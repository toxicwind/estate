import type { ArchConfig, FullMetrics, PredictionResult } from "./fleet_types.ts";

export function predictMax(m: FullMetrics, archConfig: ArchConfig): PredictionResult {
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

  const usableVram =
    m.vramFree - modelSizeMiB - computeBuffer - outputBuffer - safetyMargin;

  reasons.push(
    `Measured: ${m.kvSizeMiB.toFixed(2)} MiB KV @ ${m.nCtx} ctx = ${(kvPerToken * 1024).toFixed(4)} KiB/token`,
  );
  reasons.push(
    `VRAM: ${m.vramFree} MiB free - ${modelSizeMiB.toFixed(0)} MiB model - ${computeBuffer.toFixed(0)} MiB compute - ${outputBuffer.toFixed(0)} MiB output - ${safetyMargin} MiB margin = ${usableVram.toFixed(0)} MiB usable`,
  );

  let predicted = Math.floor(usableVram / kvPerToken);

  // ═══ SSM / Recurrent models ═══
  if (m.ssmEnabled || archConfig.isRecurrent) {
    reasons.push(
      `SSM/Recurrent: state_size=${m.ssmStateSize}, cache_per_layer=${m.ssmCacheSizePerLayer?.toFixed(4)} MiB`,
    );
    reasons.push(
      `SSM memory is CONSTANT (not per-token) — context can scale to training limit`,
    );
    // For pure SSM, KV cache is essentially just the state slots
    // The measured kvSizeMiB already includes this, so prediction is accurate
    // But we should cap at training context since state slots = min(ctx, n_seq_max)
    confidence = "very high";
    flags.push("--no-flash-attn");

    if (m.ssmNGroup && m.ssmNGroup > 0) {
      reasons.push(
        `Hybrid SSM (Qwen3-Next style): conv_state + delta-net state = ${m.ssmStateSize} floats`,
      );
    } else if (m.ssmState && m.ssmInner) {
      reasons.push(
        `Pure Mamba: ssm_state = ${m.ssmState} * ${m.ssmInner} = ${m.ssmStateSize} floats`,
      );
    }
  }

  // ═══ Hybrid models ═══
  if (m.layerPattern?.isHybrid || archConfig.isHybrid) {
    reasons.push(
      `Hybrid architecture: ${m.layerPattern?.uniqueKvSizes || 1} distinct layer KV sizes`,
    );
    if (m.layerPattern?.recurrentLayers && m.layerPattern?.attentionLayers) {
      reasons.push(
        `Recurrent layers: [${m.layerPattern.recurrentLayers.join(",")}] (${m.layerPattern.recurrentLayers.length} layers)`,
      );
      reasons.push(
        `Attention layers: [${m.layerPattern.attentionLayers.join(",")}] (${m.layerPattern.attentionLayers.length} layers)`,
      );
    }
    if (m.layerPattern?.interval) {
      reasons.push(
        `Pattern: every ${m.layerPattern.interval} layers use full attention`,
      );
    }
    if (m.nLayerDenseLead !== undefined) {
      reasons.push(
        `n_layer_dense_lead = ${m.nLayerDenseLead} (first N layers are dense attention)`,
      );
    }
    confidence = "very high";
  }

  // ═══ Sliding window ═══
  if (m.slidingWindow && m.slidingWindow > 0) {
    reasons.push(
      `Sliding window: n_swa=${m.slidingWindow}, pattern=${m.swaPattern || 1}`,
    );
    const effectiveCap = (m.trainCtx || 131072) * 1.5;
    if (predicted > effectiveCap) {
      reasons.push(
        `SWA caps effective context at ~${effectiveCap.toLocaleString()} tokens`,
      );
      predicted = Math.min(predicted, effectiveCap);
    }
    confidence = "high";
  }

  // ═══ MLA models ═══
  if (archConfig.isMla || m.mlaMode) {
    const mlaMode = m.mlaMode || archConfig.mlaDefault;
    reasons.push(
      `MLA attention: mode=${mlaMode} (0=off, 1=CPU, 2=CPU+GPU, 3=CPU-only)`,
    );

    if (m.kvLoraRank && m.nRot !== undefined) {
      reasons.push(
        `MLA params: kv_lora_rank=${m.kvLoraRank}, n_rot=${m.nRot}, latent_dim=${m.kvLoraRank + m.nRot}`,
      );
      if (m.mlaTheoreticalKvPerLayer) {
        reasons.push(
          `Theoretical MLA KV per layer @ ${m.nCtx} ctx: ${m.mlaTheoreticalKvPerLayer.toFixed(4)} MiB`,
        );
        const measuredPerLayer = m.kvSizeMiB / (m.nLayer || 1);
        const ratio = measuredPerLayer / m.mlaTheoreticalKvPerLayer;
        reasons.push(
          `Measured/theoretical per layer: ${(ratio * 100).toFixed(1)}%`,
        );
      }
    }

    if (mlaMode >= 2) {
      reasons.push(
        `MLA+FlashAttn dramatically reduces KV cache vs standard attention`,
      );
      confidence = "very high";
    }
    if (mlaMode === 3) {
      reasons.push(`MLA mode 3: minimal VRAM, CPU handles attention`);
    }
  }

  // ═══ MoE models ═══
  if (
    archConfig.isMoe ||
    m.layerPattern?.weightsPattern === "MoE or variable"
  ) {
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
      reasons.push(
        `Capped at training context: ${m.trainCtx.toLocaleString()}`,
      );
    }
    predicted = capped;
  }

  // Sanity check: theoretical KV per token vs measured (standard attention only)
  if (
    m.nLayer &&
    m.nHeadKv &&
    m.headDim &&
    !archConfig.isMla &&
    !archConfig.isRecurrent
  ) {
    const theoreticalKvPerToken =
      (2 * m.nLayer * m.nHeadKv * m.headDim * 2) / (1024 * 1024);
    const ratio = kvPerToken / theoreticalKvPerToken;
    reasons.push(
      `Theoretical full-attention KV: ${theoreticalKvPerToken.toFixed(4)} MiB/token`,
    );
    reasons.push(`Measured/theoretical ratio: ${(ratio * 100).toFixed(1)}%`);

    if (ratio < 0.3) {
      reasons.push(`→ Strong evidence of MLA, hybrid, or quantized KV cache`);
    } else if (ratio > 1.5) {
      reasons.push(
        `→ KV cache larger than theoretical (check cache types or GQA settings)`,
      );
    }
  }

  // Estimated VRAM at predicted context
  const estimatedKvAtPredicted = kvPerToken * predicted;
  const estimatedTotal =
    modelSizeMiB +
    estimatedKvAtPredicted +
    computeBuffer +
    outputBuffer +
    safetyMargin;

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
  if (
    archConfig.attnMaxBatch > 0 &&
    (!m.attnMaxBatch || m.attnMaxBatch === 0)
  ) {
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
