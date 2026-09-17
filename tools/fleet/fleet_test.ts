import { $ } from "bun";
import { PORT } from "./fleet_config.ts";
import { ARCH_CONFIG, getArchConfig } from "./fleet_arch_config.ts";
import { parseFullMetrics } from "./fleet_parse.ts";
import { predictMax } from "./fleet_predict.ts";
import { killPort, buildServerCmd } from "./fleet_server.ts";
import type { ArchConfig, FullMetrics } from "./fleet_types.ts";

export async function testModel(
  modelPath: string,
  ctx: number,
  archConfig: ArchConfig,
  probeMetrics?: FullMetrics,
) {
  await killPort();

  const cmd = buildServerCmd(modelPath, ctx, archConfig, probeMetrics);

  console.log(`\n${"=".repeat(80)}`);
  console.log(
    `[TEST] ${modelPath.split("/").pop()} @ ctx=${ctx.toLocaleString()}`,
  );
  console.log(`[FLAGS] ${cmd.slice(1).join(" ")}`);
  console.log(`${"=".repeat(80)}`);

  const proc = Bun.spawn(cmd, { stdout: "pipe", stderr: "pipe" });

  let log = "";
  const collect = async (stream: ReadableStream, isErr = false) => {
    for await (const chunk of stream) {
      const text = new TextDecoder().decode(chunk);
      if (isErr) process.stderr.write(text);
      else process.stdout.write(text);
      log += text;
    }
  };

  collect(proc.stdout);
  collect(proc.stderr);

  let ready = false;
  for (let i = 0; i < 50; i++) {
    await Bun.sleep(400);
    if (
      log.includes("unable to load model") ||
      log.includes("out of memory") ||
      log.includes("failed to allocate")
    ) {
      break;
    }
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/health`, {
        signal: AbortSignal.timeout(800),
      });
      if (res.ok) {
        ready = true;
        break;
      }
    } catch {}
  }

  let response = "";
  if (ready) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [
            {
              role: "user",
              content: "What is 15% of 240? Show your work step by step.",
            },
          ],
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
  console.log(
    ` Model: ${metrics.nLayer} layers | ${metrics.nHead} heads | ${metrics.nHeadKv} KV heads | embd=${metrics.nEmbd}`,
  );
  console.log(
    ` Head dims: k=${metrics.headDim}, v=${metrics.headDimV}, rot=${metrics.nRot}`,
  );
  console.log(
    ` Model size: ${metrics.modelSizeGiB?.toFixed(3)} GiB (${metrics.bpw?.toFixed(2)} BPW)`,
  );
  console.log(` VRAM: ${metrics.vramFree} MiB free`);
  console.log(
    ` Memory: ${metrics.memRequired?.toFixed(0)} MiB required, ${metrics.memAvailable?.toFixed(0)} MiB available`,
  );
  console.log(
    ` KV Cache: ${metrics.kvSizeMiB?.toFixed(2)} MiB @ ${metrics.nCtx} ctx (${metrics.kvPerTokenKiB?.toFixed(4)} KiB/token)`,
  );
  console.log(
    ` KV Types: K=${metrics.kvCacheTypeK || "?"}, V=${metrics.kvCacheTypeV || "?"}`,
  );
  console.log(
    ` Compute: ${metrics.computeMiB?.toFixed(2)} MiB | Output: ${metrics.outputBufferMiB?.toFixed(2)} MiB`,
  );
  console.log(
    ` Graph: ${metrics.graphNodes} nodes, ${metrics.graphSplits} splits`,
  );

  // SSM info
  if (metrics.ssmEnabled) {
    console.log(`\n SSM State:`);
    console.log(
      `  d_conv=${metrics.ssmConv}, d_inner=${metrics.ssmInner}, d_state=${metrics.ssmState}`,
    );
    console.log(`  dt_rank=${metrics.ssmDtRank}, n_group=${metrics.ssmNGroup}`);
    console.log(`  State size: ${metrics.ssmStateSize} floats`);
    console.log(
      `  Cache per layer @ ${metrics.nCtx} ctx: ${metrics.ssmCacheSizePerLayer?.toFixed(4)} MiB`,
    );
    if (metrics.ssmNGroup && metrics.ssmNGroup > 0) {
      console.log(`  Type: Hybrid SSM (Qwen3-Next style)`);
    } else {
      console.log(`  Type: Pure Mamba`);
    }
  }

  // Hybrid info
  if (metrics.layerPattern?.isHybrid) {
    console.log(`\n Hybrid Architecture:`);
    console.log(
      `  ${metrics.layerPattern.uniqueKvSizes} distinct layer KV sizes`,
    );
    console.log(`  KV sizes: ${metrics.layerPattern.kvSizes.join(", ")} MiB`);
    if (metrics.layerPattern.recurrentLayers) {
      console.log(
        `  Recurrent layers: [${metrics.layerPattern.recurrentLayers.join(",")}]`,
      );
    }
    if (metrics.layerPattern.attentionLayers) {
      console.log(
        `  Attention layers: [${metrics.layerPattern.attentionLayers.join(",")}]`,
      );
    }
    if (metrics.layerPattern.interval) {
      console.log(
        `  Pattern: every ${metrics.layerPattern.interval} layers use full attention`,
      );
    }
    if (metrics.nLayerDenseLead !== undefined) {
      console.log(`  n_layer_dense_lead: ${metrics.nLayerDenseLead}`);
    }
  }

  // MLA info
  if (metrics.kvLoraRank) {
    console.log(`\n MLA Parameters:`);
    console.log(
      `  kv_lora_rank=${metrics.kvLoraRank}, n_lora_q=${metrics.nLoraQ}, n_rot=${metrics.nRot}`,
    );
    console.log(`  latent_dim=${metrics.kvLoraRank + (metrics.nRot || 0)}`);
    if (metrics.mlaTheoreticalKvPerLayer) {
      console.log(
        `  Theoretical KV per layer: ${metrics.mlaTheoreticalKvPerLayer.toFixed(4)} MiB`,
      );
    }
  }

  if (metrics.slidingWindow) {
    console.log(
      `\n Sliding Window: n_swa=${metrics.slidingWindow}, pattern=${metrics.swaPattern}`,
    );
  }

  if (metrics.mlaMode !== undefined) {
    console.log(`\n MLA: mode=${metrics.mlaMode}`);
  }

  if (metrics.flashAttn) {
    console.log(` Flash Attention: enabled`);
  }

  console.log(
    `\n[PREDICTION] ${prediction.predicted.toLocaleString()} tokens (confidence: ${prediction.confidence})`,
  );
  prediction.reasoning.forEach((r) => console.log(` • ${r}`));

  if (prediction.recommendedFlags.length > 0) {
    console.log(
      `\n[RECOMMENDED FLAGS] ${prediction.recommendedFlags.join(" ")}`,
    );
  }

  if (response) {
    console.log(
      `\n[RESPONSE] ${response.substring(0, 200)}${response.length > 200 ? "..." : ""}`,
    );
  }
  console.log(`${"─".repeat(80)}\n`);

  return {
    success: ready && response.length > 20,
    metrics,
    prediction,
    response: response.substring(0, 500),
  };
}

export async function profileModel(modelPath: string) {
  const name = modelPath.split("/").pop()!;
  console.log(`\n${"#".repeat(80)}`);
  console.log(`# PROFILING: ${name}`);
  console.log(`${"#".repeat(80)}`);

  // Phase 1: Probe at 4k
  const probe = await testModel(modelPath, 4096, ARCH_CONFIG["unknown"]);
  if (!probe.metrics.kvSizeMiB) {
    console.log(
      "[ERROR] Failed to parse metrics from probe — retrying with defaults",
    );
    const retry = await testModel(modelPath, 4096, ARCH_CONFIG["unknown"]);
    if (!retry.metrics.kvSizeMiB) {
      console.log(
        "[ERROR] Complete failure — model may be incompatible or OOM at 4k",
      );
      return null;
    }
  }

  const archConfig = getArchConfig(probe.metrics.arch || "");
  console.log(
    `[DETECTED] Architecture: ${probe.metrics.arch} -> ${archConfig.name}`,
  );
  console.log(
    `[CONFIG] MLA=${archConfig.mlaDefault}, FA=${archConfig.flashAttnRecommended}, MoE=${archConfig.isMoe}`,
  );

  // Phase 1b: Re-probe with architecture-aware flags
  let finalProbe = probe;
  if (
    archConfig.mlaDefault > 0 ||
    archConfig.flashAttnRecommended ||
    archConfig.cacheTypeK !== "f16"
  ) {
    console.log(`\n${"=".repeat(80)}`);
    console.log("[PHASE 1b] Re-probing with architecture-aware flags");
    console.log(`${"=".repeat(80)}`);
    finalProbe = await testModel(modelPath, 4096, archConfig);
  }

  const predicted = finalProbe.prediction.predicted;
  const trainCtx = finalProbe.metrics.trainCtx || 262144;
  const testCtx = Math.min(predicted, trainCtx);

  console.log(`\n${"=".repeat(80)}`);
  console.log(
    `[PHASE 2] Testing predicted maximum: ${testCtx.toLocaleString()} tokens`,
  );
  console.log(`${"=".repeat(80)}`);

  const final = await testModel(
    modelPath,
    testCtx,
    archConfig,
    finalProbe.metrics,
  );

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
      is_recurrent:
        archConfig.isRecurrent || finalProbe.metrics.ssmEnabled || false,
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
