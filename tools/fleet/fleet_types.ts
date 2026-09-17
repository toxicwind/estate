export interface ArchConfig {
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

export interface SsmParams {
  ssm_d_conv: number;
  ssm_d_inner: number;
  ssm_d_state: number;
  ssm_dt_rank: number;
  ssm_n_group: number;
}

export interface MlaParams {
  kvLoraRank: number;
  nEmbdHeadQkRope: number; // n_rot
  nLayer: number;
  ctx: number;
  cacheTypeK: string;
  cacheTypeV: string;
  mlaMode: number;
  flashAttn: boolean;
}

export interface LayerInfo {
  index: number;
  weights: number;
  kv: number;
  total: number;
  compute: number;
  output: boolean;
}

export interface FullMetrics {
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

export interface PredictionResult {
  predicted: number;
  reasoning: string[];
  confidence: string;
  recommendedFlags: string[];
  estimatedVramAtPredicted: number;
}
