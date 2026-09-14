export * from "@oh-my-pi/pi-catalog/models";
import type { Api, Model, ModelCost, TokenCost, Usage } from "@oh-my-pi/pi-catalog/types";

export type UsageRecord = Partial<Usage> & {
	input?: number;
	output?: number;
	cacheRead?: number;
	cacheWrite?: number;
	cost?: Partial<CostBreakdown>;
	[key: string]: unknown;
};

export type ModelDefinition = Partial<Model<Api>> & {
	cost?: Partial<ModelCost>;
	[key: string]: unknown;
};

export interface CostBreakdown {
	input: number;
	output: number;
	cacheRead: number;
	cacheWrite: number;
	total: number;
}

/**
 * Calculate token cost breakdown from model metadata and apply it to usage.
 */
export function applyReportedCost(usage: UsageRecord, model: ModelDefinition): CostBreakdown {
	const cost = model?.cost ?? {};
	const inputTokens = usage.input ?? 0;
	const outputTokens = usage.output ?? 0;
	const cacheReadTokens = usage.cacheRead ?? 0;
	const cacheWriteTokens = usage.cacheWrite ?? 0;

	const promptTokens = inputTokens + cacheReadTokens + cacheWriteTokens;
	const longContext = (cost as ModelCost).longContext;
	let rates: Partial<TokenCost> = cost;
	if (longContext) {
		const reachesThreshold =
			promptTokens > longContext.inputThreshold ||
			(longContext.inputThresholdInclusive === true && promptTokens === longContext.inputThreshold);
		if (reachesThreshold) {
			rates = longContext;
		}
	}

	const inputRate = (rates.input ?? 0) / 1_000_000;
	const outputRate = (rates.output ?? 0) / 1_000_000;
	const cacheReadRate = (rates.cacheRead ?? 0) / 1_000_000;
	const cacheWriteRate = (rates.cacheWrite ?? 0) / 1_000_000;

	const breakdown: CostBreakdown = {
		input: inputRate * inputTokens,
		output: outputRate * outputTokens,
		cacheRead: cacheReadRate * cacheReadTokens,
		cacheWrite: cacheWriteRate * cacheWriteTokens,
		total: 0,
	};
	breakdown.total = breakdown.input + breakdown.output + breakdown.cacheRead + breakdown.cacheWrite;

	if (usage.cost) {
		Object.assign(usage.cost, breakdown);
	}

	return breakdown;
}
