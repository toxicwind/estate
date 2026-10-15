// Builds the static NIM model list from metadata + family compat.
import { readFileSync } from "node:fs";
import type { NimModelConfig, NimModelCompat } from "./types.ts";
import {
  applyFamilyCompat,
  classifyThinkingFormat,
  findFamily,
  STUB_DEFAULT_CONTEXT_WINDOW,
  STUB_DEFAULT_MAX_TOKENS,
} from "../config/model-families.ts";
import { collectLiveStubIds, isLLMModel as isLLMModelId } from "../lib/catalog-merge.mjs";
import { readRouterConfig } from "../extensions/lib/router-policy.mjs";

interface MetadataEntry {
  id: string;
  owned_by: string;
  contextWindow?: number;
  maxOutputTokens?: number;
  supportsVision?: boolean;
  supportsReasoning?: boolean;
  reasoningBudget?: number;
  reasoningEffortValues?: string[];
  thinkingFormat?: string;
  exampleRequestExtra?: Record<string, unknown>;
}

const metadataJson = JSON.parse(
  readFileSync(new URL("./metadata.json", import.meta.url), "utf8"),
) as MetadataEntry[];

const REASONING_EFFORT_ORDER = ["none", "low", "medium", "high", "max"] as const;
type ReasoningEffort = (typeof REASONING_EFFORT_ORDER)[number];

function reasoningEffortRank(value: string): number | undefined {
  const idx = REASONING_EFFORT_ORDER.indexOf(value as ReasoningEffort);
  return idx === -1 ? undefined : idx;
}

// Map scraper thinking labels to pi compat flags.
export function mapThinkingFormatToCompat(
  thinkingFormat: string | undefined
): NimModelCompat {
  switch (thinkingFormat) {
    case "qwen-chat-template":
      return { thinkingFormat: "qwen-chat-template" };
    case "deepseek-v4":
    case "deepseek-nim":
      return {}; // Handled by before_provider_request handler
    case "minimax-inline":
      return {}; // Handled by before_provider_request handler
    case "thinking-budget":
      return {}; // Handled by before_provider_request handler
    case "nemotron-3-super-effort":
      return { supportsReasoningEffort: true }; // Pi sends reasoning_effort, handler converts to enable_thinking + low_effort
    case "nemotron-system-detailed":
      return {}; // Handled by before_provider_request handler (system message injection)
    case "nemotron-system-think":
      return {}; // Handled by before_provider_request handler (system message injection)
    case "reasoning-effort":
      return { supportsReasoningEffort: true };
    case "none":
    case undefined:
    default:
      return {};
  }
}

// Convert allowed provider effort values into pi thinking levels.
export function buildReasoningEffortThinkingLevelMap(
  values?: string[]
): NimModelConfig["thinkingLevelMap"] | undefined {
  if (!values?.length) return undefined;

  const supported = Array.from(
    new Set(values.map((value) => value.trim().toLowerCase()).filter(Boolean))
  )
    .filter((value): value is ReasoningEffort => reasoningEffortRank(value) !== undefined)
    .sort((a, b) => reasoningEffortRank(a)! - reasoningEffortRank(b)!);

  if (supported.length === 0) return undefined;

  const pick = (desiredRank: number): string | null => {
    const candidate = supported.find((value) => reasoningEffortRank(value)! >= desiredRank);
    return candidate ?? supported[supported.length - 1] ?? null;
  };

  return {
    off: supported.includes("none") ? "none" : null,
    minimal: pick(1),
    low: pick(1),
    medium: pick(2),
    high: pick(3),
    xhigh: pick(4),
  };
}

export function isLLMModel(entry: string | { id: string }): boolean {
  return isLLMModelId(typeof entry === "string" ? entry : entry.id);
}

// One metadata row → one provider model.
export function metadataToModelConfig(entry: MetadataEntry): NimModelConfig {
  const compat = mapThinkingFormatToCompat(entry.thinkingFormat);
  const thinkingLevelMap =
    entry.thinkingFormat === "reasoning-effort"
      ? buildReasoningEffortThinkingLevelMap(entry.reasoningEffortValues)
      : undefined;

  return {
    id: entry.id,
    name: makeDisplayName(entry.id),
    reasoning: entry.supportsReasoning ?? false,
    input: entry.supportsVision ? ["text", "image"] : ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: entry.contextWindow ?? STUB_DEFAULT_CONTEXT_WINDOW,
    maxTokens: entry.maxOutputTokens ?? STUB_DEFAULT_MAX_TOKENS,
    reasoningBudget: entry.reasoningBudget,
    thinkingLevelMap,
    compat,
    exampleRequestExtra: entry.exampleRequestExtra,
    headers: { "NVCF-POLL-SECONDS": "3600" },
  };
}

function makeDisplayName(id: string): string {
  const name = id.split("/").pop() || id;
  return name
    .split(/[-_]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function stubFromLiveId(id: string): NimModelConfig {
  const family = findFamily(id);
  return metadataToModelConfig({
    id,
    owned_by: id.split("/")[0] ?? "unknown",
    supportsReasoning: false,
    supportsVision: family?.input?.includes("image") ?? false,
    contextWindow: family?.contextWindow,
    maxOutputTokens: family?.maxTokens,
  });
}

/**
 * Honest virtual-router window: min(chain) so Pi compact-triggers before Llama
 * overflow. When MiniMax (or another large model) is the sticky pick, advertise
 * that model's window so long sessions stay on the model that can serve them.
 */
export function advertisedRouterLimits(
  catalog: Iterable<NimModelConfig> | Map<string, NimModelConfig>,
  chain: string[],
  stickyId?: string | null,
): {
  contextWindow: number;
  maxTokens: number;
  input: NimModelConfig["input"];
} {
  const map =
    catalog instanceof Map
      ? catalog
      : new Map([...catalog].map((model) => [model.id, model]));
  const chainModels = chain
    .map((id) => map.get(id))
    .filter((model): model is NimModelConfig => Boolean(model));
  const sticky =
    stickyId && chain.includes(stickyId) ? map.get(stickyId) : undefined;
  const source = sticky ? [sticky] : chainModels;
  if (source.length === 0) {
    return {
      contextWindow: STUB_DEFAULT_CONTEXT_WINDOW,
      maxTokens: STUB_DEFAULT_MAX_TOKENS,
      input: ["text"],
    };
  }
  const hasVision = source.some((model) => model.input?.includes("image"));
  return {
    contextWindow: Math.min(...source.map((model) => model.contextWindow)),
    maxTokens: Math.min(...source.map((model) => model.maxTokens)),
    input: hasVision ? ["text", "image"] : ["text"],
  };
}

export function applyRouterVirtualLimits(
  model: NimModelConfig,
  catalog: Iterable<NimModelConfig> | Map<string, NimModelConfig>,
  chain: string[],
  stickyId?: string | null,
): NimModelConfig {
  const limits = advertisedRouterLimits(catalog, chain, stickyId);
  model.contextWindow = limits.contextWindow;
  model.maxTokens = limits.maxTokens;
  model.input = limits.input;
  return model;
}

const entries = metadataJson as MetadataEntry[];
const llmEntries = entries.filter((entry) => isLLMModel(entry.id));

const seen = new Set<string>();
const uniqueEntries: MetadataEntry[] = [];
for (const entry of llmEntries) {
  if (seen.has(entry.id)) continue;
  seen.add(entry.id);
  uniqueEntries.push(entry);
}

const MODELS_FROM_METADATA: NimModelConfig[] = uniqueEntries.map(metadataToModelConfig);

export const ROUTER_MODEL_ID = "nvidia-router";

// Load, dedupe, convert, then merge family compat.
const BASE_MODELS = applyFamilyCompat(MODELS_FROM_METADATA);

const ROUTER_VIRTUAL_MODEL: NimModelConfig = {
  id: ROUTER_MODEL_ID,
  name: "NVIDIA Router (auto)",
  reasoning: true,
  input: ["text", "image"],
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  contextWindow: STUB_DEFAULT_CONTEXT_WINDOW,
  maxTokens: STUB_DEFAULT_MAX_TOKENS,
};

applyRouterVirtualLimits(ROUTER_VIRTUAL_MODEL, BASE_MODELS, readRouterConfig().chain);

export const STATIC_MODELS = [ROUTER_VIRTUAL_MODEL, ...BASE_MODELS];
export const STATIC_MODEL_MAP = new Map(STATIC_MODELS.map((model) => [model.id, model]));

export { classifyThinkingFormat };

let activeModels: NimModelConfig[] = STATIC_MODELS;
let activeModelMap = new Map(STATIC_MODELS.map((model) => [model.id, model]));

export function getActiveModels(): NimModelConfig[] {
  return activeModels;
}

export function getActiveModelMap(): Map<string, NimModelConfig> {
  return activeModelMap;
}

export function isLiveStub(modelId: string): boolean {
  return !STATIC_MODEL_MAP.has(modelId) && activeModelMap.has(modelId);
}

export function setActiveModels(models: NimModelConfig[]): void {
  activeModels = models;
  activeModelMap = new Map(models.map((model) => [model.id, model]));
}

/** Curated catalog plus new live chat IDs (family compat on stubs). Never drops curated models. */
export function mergeCatalog(liveIds: string[]): NimModelConfig[] {
  const stubIds = collectLiveStubIds(
    STATIC_MODELS.map((model) => model.id),
    liveIds,
  );
  const stubs = applyFamilyCompat(stubIds.map(stubFromLiveId));
  return [...STATIC_MODELS, ...stubs];
}

export function applyLiveCatalog(liveIds: string[]): NimModelConfig[] {
  const merged = mergeCatalog(liveIds);
  setActiveModels(merged);
  return merged;
}

const metadataMap = new Map(entries.map((entry) => [entry.id, entry]));

export function getModelMetadata(modelId: string): MetadataEntry | undefined {
  return metadataMap.get(modelId);
}

export function getAllMetadata(): MetadataEntry[] {
  return Array.from(metadataMap.values());
}

export function hasMetadata(modelId: string): boolean {
  return metadataMap.has(modelId);
}
