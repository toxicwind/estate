import type { LayerInfo, FullMetrics, SsmParams, MlaParams } from "./fleet_types.ts";
import { getArchConfig } from "./fleet_arch_config.ts";
import { calculateSsmStateSize, calculateRecurrentCacheSize, calculateMlaKvSize } from "./fleet_calc.ts";

export function parseLayerTable(log: string): LayerInfo[] {
  const layers: LayerInfo[] = [];
  const reNormal =
    /Layer\s+(\d+):\s+([\d.]+),\s+([\d.]+),\s+([\d.]+)\s+([\d.]+)\s+MiB/g;
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
  const reOutput =
    /Layer\s+(\d+):\s+([\d.]+),\s+([\d.]+),\s+([\d.]+)\s+MiB\s+\(output layer\)/;
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

export function parseFullMetrics(log: string): FullMetrics {
  const m: FullMetrics = {};
  const get = (re: RegExp, fn: (s: string) => any = parseFloat) => {
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
  const kvMla = log.match(
    /KV self size\s+=\s+([\d.]+)\s+MiB,\s+c\^KV\s+\(([^)]+)\):\s+([\d.]+)\s+MiB,\s+kv\^T\s+\(([^)]+)\):\s+([\d.]+)\s+MiB/,
  );
  const kvMlaNoT = log.match(
    /KV self size\s+=\s+([\d.]+)\s+MiB,\s+c\^KV\s+\(([^)]+)\):\s+([\d.]+)\s+MiB,\s+kv\^T:\s+not used/,
  );
  const kvStandard = log.match(
    /KV self size\s+=\s+([\d.]+)\s+MiB,\s+K\s+\(([^)]+)\):\s+([\d.]+)\s+MiB,\s+V\s+\(([^)]+)\):\s+([\d.]+)\s+MiB/,
  );

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
  const computeMatch = log.match(
    /(\S+)\s+compute buffer size\s+=\s+([\d.]+)\s+MiB/,
  );
  if (computeMatch) {
    m.computeMiB = parseFloat(computeMatch[2]);
  }

  // Output buffer
  const outBufMatch = log.match(/output buffer size\s+=\s+([\d.]+)\s+MiB/);
  if (outBufMatch) {
    m.outputBufferMiB = parseFloat(outBufMatch[1]);
  }

  // Memory
  m.memRequired = get(
    /Memory required for model tensors \+ cache:\s+([\d.]+)\s+MiB/,
  );
  m.memAvailable = get(
    /Memory available on all devices - compute:\s+([\d.]+)\s+MiB/,
  );

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
      m.ssmCacheSizePerLayer =
        calculateRecurrentCacheSize(m.ssmStateSize, m.nCtx) / (1024 * 1024); // MiB
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
    const nonOutput = m.layers.filter((l) => !l.output);
    const kvSizes = [...new Set(nonOutput.map((l) => l.kv.toFixed(2)))]
      .map(Number)
      .sort((a, b) => a - b);

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
      isHybrid:
        kvSizes.length > 1 ||
        !!m.nLayerDenseLead ||
        (m.arch && getArchConfig(m.arch).isHybrid),
      recurrentLayers: recurrentLayers.length > 0 ? recurrentLayers : undefined,
      attentionLayers: attentionLayers.length > 0 ? attentionLayers : undefined,
    };

    if (kvSizes.length === 2) {
      const [small, large] = kvSizes;
      const largeLayers = nonOutput
        .filter((l) => Math.abs(l.kv - large) < 0.1)
        .map((l) => l.index);
      if (largeLayers.length > 1) {
        const intervals = largeLayers
          .slice(1)
          .map((v, i) => v - largeLayers[i]);
        const counts = new Map<number, number>();
        intervals.forEach((v) => counts.set(v, (counts.get(v) || 0) + 1));
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

    const weightSizes = [
      ...new Set(nonOutput.map((l) => l.weights.toFixed(2))),
    ].map(Number);
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
