/**
 * Usage ranking/metrics: plan classification, ranking strategies, usage-limit and usage-health types.
 *
 * Extracted verbatim from auth-storage.ts (surgical split 2026-09-14).
 * Re-exported through auth-storage.ts; import from there.
 */
import type { Provider } from "../types";
import type { CredentialRankingContext, CredentialRankingStrategy, UsageCredential, UsageProvider, UsageReport } from "../usage";
import { alibabaTokenPlanRankingStrategy, alibabaTokenPlanUsageProvider } from "../usage/alibaba-token-plan";
import { claudeRankingStrategy, claudeUsageProvider } from "../usage/claude";
import { clinePassUsageProvider } from "../usage/cline-pass";
import { charmHyperUsageProvider } from "../usage/charm-hyper";
import { cursorUsageProvider } from "../usage/cursor";
import { devinUsageProvider } from "../usage/devin";
import { googleGeminiCliUsageProvider } from "../usage/gemini";
import { githubCopilotUsageProvider } from "../usage/github-copilot";
import { antigravityRankingStrategy, antigravityUsageProvider } from "../usage/google-antigravity";
import { kimiRankingStrategy, kimiUsageProvider } from "../usage/kimi";
import { minimaxCodeUsageProvider } from "../usage/minimax-code";
import { museCodeUsageProvider } from "../usage/muse-code";
import { ollamaCloudUsageProvider, ollamaUsageProvider } from "../usage/ollama";
import { codexRankingStrategy, openaiCodexUsageProvider } from "../usage/openai-codex";
import { opencodeGoRankingStrategy, opencodeGoUsageProvider } from "../usage/opencode-go";
import { syntheticUsageProvider } from "../usage/synthetic";
import { umansUsageProvider } from "../usage/umans";
import { xaiOauthUsageProvider } from "../usage/xai-oauth";
import { zaiRankingStrategy, zaiUsageProvider } from "../usage/zai";
import type { AuthCredential } from "./storage-contract";
import { planRequirementFor } from "@oh-my-pi/pi-catalog/compat/behavior";

export const USAGE_RANKING_METRIC_EPSILON = 1e-9;
/**
 * Primary (short, e.g. 5h) window used-fraction at or above which a candidate
 * is demoted behind cooler siblings during ranking: a nearly exhausted short
 * window means an imminent mid-session block, so drain urgency defers to it.
 */
export const PRIMARY_WINDOW_HOT_FRACTION = 0.85;

export const DEFAULT_USAGE_PROVIDERS: UsageProvider[] = [
	alibabaTokenPlanUsageProvider,
	openaiCodexUsageProvider,
	kimiUsageProvider,
	minimaxCodeUsageProvider,
	museCodeUsageProvider,
	antigravityUsageProvider,
	googleGeminiCliUsageProvider,
	ollamaUsageProvider,
	ollamaCloudUsageProvider,
	claudeUsageProvider,
	clinePassUsageProvider,
	zaiUsageProvider,
	umansUsageProvider,
	opencodeGoUsageProvider,
	githubCopilotUsageProvider,
	cursorUsageProvider,
	syntheticUsageProvider,
	xaiOauthUsageProvider,
	devinUsageProvider,
	charmHyperUsageProvider,
];

export const DEFAULT_USAGE_PROVIDER_MAP = new Map<Provider, UsageProvider>(
	DEFAULT_USAGE_PROVIDERS.map(provider => [provider.id, provider]),
);

export { isDefinitiveOAuthFailure } from "../error/auth-classify";

/**
 * Outcome of {@link AuthStorage.markUsageLimitReached}.
 *
 * `switched` is `true` when an unblocked same-type sibling credential is
 * available right now, so the caller can retry immediately and the next
 * `getApiKey` will hand it out. When `false`, `retryAtMs` (epoch ms) carries
 * the earliest moment any same-type sibling's temporary block expires —
 * callers should prefer waiting until then over the provider's (often
 * multi-hour) retry-after when it is sooner. `retryAtMs` is `undefined` when
 * no sibling credentials exist at all, or when the session has no tracked
 * credential to rotate away from.
 *
 * `blockedUntilMs` (epoch ms) is the just-blocked credential's own unblock
 * deadline — the later of the caller's retry-after and any exhausted window
 * the usage report reveals. Callers that wait the account out (instead of
 * rotating) must sleep until this, not the error-text hint alone.
 *
 * `priorBlockedUntilMs` (epoch ms) is the live block deadline the map already
 * stored for this credential before this call. The merged `blockedUntilMs`
 * masks a pre-existing block shorter than this call's own heuristic
 * fallback (`Math.max` in the mark), so callers that replace that heuristic
 * with an authoritative report window must consult the prior deadline to
 * keep honoring the earlier response's provider-stated block.
 *
 * `priorBlockedUntilTimed` is `true` when that prior deadline came from
 * provider-stated timing (a parsed hint or usage-report reset) rather than
 * another session's heuristic guess — only timed priors may extend a wait
 * past an authoritative report window. Persisted blocks carry no provenance
 * and count as untimed: a stale persisted heuristic must not outrank a
 * fresh complete report (longer persisted deadlines still win through the
 * merged `blockedUntilMs`).
 *
 * `reportResetAtMs` (epoch ms) is present only when the usage report is a
 * complete authority for the wait: every exhausted window carries a future
 * reset, so sleeping until the latest one can actually clear the account. A
 * permanent cap alongside a timed window (or no report at all) leaves it
 * unset, and the heuristic fallback alone must never authorize a wait.
 */
export interface UsageLimitMarkResult {
	switched: boolean;
	retryAtMs?: number;
	blockedUntilMs?: number;
	/** This mark call's initial deadline, before report correction and merging. */
	requestedBlockedUntilMs?: number;
	priorBlockedUntilMs?: number;
	priorBlockedUntilTimed?: boolean;
	reportResetAtMs?: number;
}

export type ModelUsageHealthState = "healthy" | "reserve" | "depleted" | "unknown";

export interface ModelUsageAccountHealth {
	credentialId: number;
	credentialType: AuthCredential["type"];
	/** True when this credential is currently sticky for options.sessionId. */
	selected?: true;
	state: ModelUsageHealthState;
	remainingFraction?: number;
	resetsAt?: number;
}

export interface ModelUsageHealth {
	state: ModelUsageHealthState;
	accounts: ModelUsageAccountHealth[];
}

export interface ModelUsageHealthOptions {
	modelId?: string;
	sessionId?: string;
	baseUrl?: string;
	reserveFraction: number;
	signal?: AbortSignal;
}

export type UsageCacheEntry<T> = {
	value: T;
	expiresAt: number;
};

export interface UsageCache {
	get<T>(key: string): UsageCacheEntry<T> | undefined;
	getStale<T>(key: string): UsageCacheEntry<T> | undefined;
	set<T>(key: string, entry: UsageCacheEntry<T>): void;
	deletePrefix(prefix: string): boolean;
	cleanup?(): void;
}

export type UsageRequestDescriptor = {
	provider: Provider;
	credential: UsageCredential;
	baseUrl?: string;
};

export type ForcedUsageRefresh = {
	all: boolean;
	providers: Set<Provider>;
};

export type OpenAICodexPlanRequirement = "none" | "paid" | "pro";
export type OpenAICodexPlanClass = "free" | "paid" | "pro" | "unknown";

export const OPENAI_CODEX_PRO_PLAN_TOKENS: Record<string, true> = {
	pro: true,
};
export const OPENAI_CODEX_PAID_PLAN_TOKENS: Record<string, true> = {
	plus: true,
	business: true,
	team: true,
	enterprise: true,
	edu: true,
	education: true,
	teacher: true,
	teachers: true,
	health: true,
	gov: true,
	government: true,
};
export const OPENAI_CODEX_FREE_PLAN_TOKENS: Record<string, true> = {
	free: true,
	go: true,
};

/**
 * Account tier needed for model-aware Codex OAuth routing.
 *
 * GPT-5.6 Terra (including its local pro-mode alias) remains available on every
 * plan. Sol and Luna pro-mode aliases inherit their base models' paid tier;
 * only Spark currently has a documented Pro-plan preference in Codex.
 */
export function resolveOpenAICodexPlanRequirement(provider: string, modelId: string | undefined): OpenAICodexPlanRequirement {
	if (provider !== "openai-codex" || typeof modelId !== "string") return "none";
	return (planRequirementFor("openai-codex", modelId) as OpenAICodexPlanRequirement | undefined) ?? "none";
}

export const MODEL_ACCOUNT_POLICY_BLOCK_SCOPE_PREFIX = "model-policy:";
export const MODEL_ACCOUNT_POLICY_PROVIDERS: Readonly<Record<string, true>> = {
	"openai-codex": true,
	cursor: true,
};

export function modelAccountPolicyBlockScope(provider: string, modelId: string | undefined): string | undefined {
	if (!Object.hasOwn(MODEL_ACCOUNT_POLICY_PROVIDERS, provider) || typeof modelId !== "string") return undefined;
	const separator = modelId.lastIndexOf("/");
	const bareModelId = (separator === -1 ? modelId : modelId.slice(separator + 1)).trim().toLowerCase();
	if (!bareModelId || bareModelId.includes("\0")) return undefined;
	return `${MODEL_ACCOUNT_POLICY_BLOCK_SCOPE_PREFIX}${bareModelId}`;
}

export function credentialBlockScopesForRequest(
	provider: string,
	strategy: CredentialRankingStrategy | undefined,
	rankingContext: CredentialRankingContext,
	blockScope: string | undefined,
): readonly string[] {
	const scopes = strategy?.blockScopes?.(rankingContext) ?? (blockScope ? [blockScope] : []);
	const modelPolicyScope = modelAccountPolicyBlockScope(provider, rankingContext.modelId);
	if (!modelPolicyScope || scopes.includes(modelPolicyScope)) return scopes;
	return [...scopes, modelPolicyScope];
}

export function getUsagePlanType(report: UsageReport | null): string | undefined {
	const metadata = report?.metadata;
	if (!metadata) return undefined;
	const planType = metadata.planType;
	if (typeof planType !== "string") return undefined;
	const normalized = planType
		.trim()
		.toLowerCase()
		.replace(/[\s-]+/g, "_");
	return normalized.startsWith("chatgpt_") ? normalized.slice("chatgpt_".length) : normalized;
}

export function classifyOpenAICodexPlan(report: UsageReport | null): OpenAICodexPlanClass {
	const planType = getUsagePlanType(report);
	if (!planType) return "unknown";
	// Pro Lite is a paid Codex tier, but does not imply full Pro-only model access.
	if (planType === "prolite" || planType === "pro_lite") return "paid";
	const tokens = planType.split("_");
	if (tokens.some(token => OPENAI_CODEX_PRO_PLAN_TOKENS[token] === true)) return "pro";
	if (tokens.some(token => OPENAI_CODEX_PAID_PLAN_TOKENS[token] === true)) return "paid";
	if (tokens.some(token => OPENAI_CODEX_FREE_PLAN_TOKENS[token] === true)) return "free";
	return "unknown";
}

export function getOpenAICodexPlanEligibility(
	report: UsageReport | null,
	requirement: OpenAICodexPlanRequirement,
): boolean | undefined {
	if (requirement === "none") return true;
	const planClass = classifyOpenAICodexPlan(report);
	if (planClass === "unknown") return undefined;
	return requirement === "paid" ? planClass !== "free" : planClass === "pro";
}

export function getOpenAICodexPlanPriority(report: UsageReport | null, requirement: OpenAICodexPlanRequirement): number {
	const eligibility = getOpenAICodexPlanEligibility(report, requirement);
	return eligibility === true ? 0 : eligibility === undefined ? 1 : 2;
}

export function compareUsageRankingMetric(left: number, right: number): number {
	if (left === right) return 0;
	if (!Number.isFinite(left) || !Number.isFinite(right)) return left < right ? -1 : 1;
	const delta = left - right;
	const tolerance = Math.max(USAGE_RANKING_METRIC_EPSILON, Math.max(Math.abs(left), Math.abs(right)) * 0.000001);
	return Math.abs(delta) <= tolerance ? 0 : delta;
}

export function resolveDefaultUsageProvider(provider: Provider): UsageProvider | undefined {
	return DEFAULT_USAGE_PROVIDER_MAP.get(provider);
}

export const DEFAULT_RANKING_STRATEGIES = new Map<Provider, CredentialRankingStrategy>([
	["alibaba-token-plan", alibabaTokenPlanRankingStrategy],
	["openai-codex", codexRankingStrategy],
	["anthropic", claudeRankingStrategy],
	["google-antigravity", antigravityRankingStrategy],
	["kimi-code", kimiRankingStrategy],
	["zai", zaiRankingStrategy],
	["opencode-go", opencodeGoRankingStrategy],
]);

export function resolveDefaultRankingStrategy(provider: Provider): CredentialRankingStrategy | undefined {
	return DEFAULT_RANKING_STRATEGIES.get(provider);
}
