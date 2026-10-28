/** @typedef {{ id: string; contextWindow?: number; input?: string[] }} ModelCatalogEntry */

export const ROUTER_MODEL_ID = "nvidia-router";
export const ROUTER_TAG = "[nvidia-router]";

export const DEFAULT_ROUTER_CHAIN = [
	"minimaxai/minimax-m3",
	"nvidia/nemotron-3-super-120b-a12b",
	"meta/llama-3.3-70b-instruct",
];

export const DEFAULT_CONTEXT_MARGIN = 1.15;

export function parseFloatEnv(v, fallback) {
	if (!v) return fallback;
	const n = Number.parseFloat(v);
	return Number.isFinite(n) ? n : fallback;
}

/** @param {Record<string, string | undefined>} [env] */
export function readRouterConfig(env = process.env) {
	const chainRaw = env.NVIDIA_ROUTER_CHAIN?.trim();
	const chain = chainRaw
		? chainRaw.split(",").map((s) => s.trim()).filter(Boolean)
		: [...DEFAULT_ROUTER_CHAIN];
	const margin = Math.max(1, parseFloatEnv(env.NVIDIA_ROUTER_MARGIN, DEFAULT_CONTEXT_MARGIN));
	return { chain, contextMargin: margin };
}

/** @param {unknown[]} messages */
export function messagesNeedVision(messages) {
	if (!Array.isArray(messages)) return false;
	for (const msg of messages) {
		const content = msg?.content;
		if (!Array.isArray(content)) continue;
		for (const part of content) {
			if (part?.type === "image" || part?.type === "image_url") return true;
		}
	}
	return false;
}

/** @param {unknown} entry */
function chatMessageFromSessionEntry(entry) {
	if (!entry || typeof entry !== "object") return null;
	const rec = /** @type {Record<string, unknown>} */ (entry);
	if (rec.message && typeof rec.message === "object") {
		return rec.message;
	}
	if (typeof rec.role === "string" && rec.content !== undefined) {
		return { role: rec.role, content: rec.content };
	}
	if (rec.type === "user" || rec.type === "assistant") {
		return {
			role: rec.type,
			content: rec.content ?? rec.text ?? "",
		};
	}
	if (rec.type === "toolResult" || rec.type === "tool_result") {
		return {
			role: "tool",
			content: rec.content ?? rec.text ?? rec.output ?? "",
		};
	}
	return null;
}

/**
 * Session entries from `ctx.sessionManager.buildContextEntries()` / `getEntries()`.
 * @param {unknown} entries
 */
export function messagesFromSessionEntries(entries) {
	if (!Array.isArray(entries)) return [];
	const out = [];
	for (const entry of entries) {
		const rec = entry && typeof entry === "object"
			? /** @type {Record<string, unknown>} */ (entry)
			: null;
		if (rec && (rec.type === "compaction" || rec.type === "branch_summary" || rec.type === "header")) {
			continue;
		}
		const msg = chatMessageFromSessionEntry(entry);
		if (msg) out.push(msg);
	}
	return out;
}

/**
 * Best-effort session messages for `/nim-router` eligibility.
 * Prefers `ctx.messages`, then SessionManager context entries.
 * @param {any} ctx
 */
export function sessionMessagesFromContext(ctx) {
	if (!ctx) return [];
	if (Array.isArray(ctx.messages) && ctx.messages.length > 0) {
		return ctx.messages;
	}
	const sm = ctx.sessionManager;
	if (sm) {
		const entries =
			typeof sm.buildContextEntries === "function"
				? sm.buildContextEntries()
				: typeof sm.getEntries === "function"
					? sm.getEntries()
					: [];
		const fromEntries = messagesFromSessionEntries(entries);
		if (fromEntries.length > 0) return fromEntries;
	}
	return [];
}

/**
 * Prefer Pi's `getContextUsage()` (last assistant usage + trailing estimate).
 * Falls back to a chars/4 estimate that also counts role, tools, and thinking.
 * @param {any} ctx
 * @param {unknown[]} [messages]
 */
export function estimateSessionTokens(ctx, messages) {
	const usage = typeof ctx?.getContextUsage === "function" ? ctx.getContextUsage() : undefined;
	if (usage?.tokens && usage.tokens > 0) return usage.tokens;
	return estimateInputTokens(messages ?? sessionMessagesFromContext(ctx));
}

/** @param {unknown[]} messages */
export function estimateInputTokens(messages) {
	if (!Array.isArray(messages)) return 0;
	let chars = 0;
	for (const msg of messages) {
		const rec = msg && typeof msg === "object" ? /** @type {Record<string, unknown>} */ (msg) : null;
		if (!rec) continue;
		if (typeof rec.role === "string") chars += rec.role.length + 4;
		const content = rec.content;
		if (typeof content === "string") {
			chars += content.length;
		} else if (Array.isArray(content)) {
			for (const part of content) {
				if (part?.type === "text" && typeof part.text === "string") {
					chars += part.text.length;
				} else if (part?.type === "image" || part?.type === "image_url") {
					chars += 2000;
				} else if (part && typeof part === "object") {
					try {
						chars += JSON.stringify(part).length;
					} catch {
						/* ignore */
					}
				}
			}
		}
		if (typeof rec.thinking === "string") chars += rec.thinking.length;
		if (typeof rec.reasoning === "string") chars += rec.reasoning.length;
		if (Array.isArray(rec.tool_calls)) {
			try {
				chars += JSON.stringify(rec.tool_calls).length;
			} catch {
				/* ignore */
			}
		}
	}
	return Math.ceil(chars / 4);
}

/**
 * @param {ModelCatalogEntry} model
 * @param {number} estimatedTokens
 * @param {boolean} needsVision
 * @param {number} margin
 */
export function isModelEligible(model, estimatedTokens, needsVision, margin) {
	if (!model?.id || model.id === ROUTER_MODEL_ID) return false;
	const window = model.contextWindow ?? 131072;
	if (estimatedTokens * margin > window) return false;
	if (needsVision) {
		const inputs = model.input ?? ["text"];
		if (!inputs.includes("image")) return false;
	}
	return true;
}

/**
 * @param {string[]} chain
 * @param {Map<string, ModelCatalogEntry>} catalog
 * @param {number} estimatedTokens
 * @param {boolean} needsVision
 * @param {number} margin
 * @param {Set<string>} [skip]
 */
export function getEligibleChain(chain, catalog, estimatedTokens, needsVision, margin, skip = new Set()) {
	return chain.filter((id) => {
		if (skip.has(id)) return false;
		const model = catalog.get(id);
		if (!model) return false;
		return isModelEligible(model, estimatedTokens, needsVision, margin);
	});
}

/** @param {string | undefined} text */
export function isContextOverflowErrorMessage(text) {
	if (!text) return false;
	const err = text.toLowerCase();
	return (
		err.includes("context length") ||
		err.includes("maximum context") ||
		err.includes("max context") ||
		err.includes("too many tokens") ||
		err.includes("context window") ||
		err.includes("input is too long") ||
		err.includes("token limit")
	);
}

/** @param {string | undefined} errorMessage */
export function isRouterFailoverError(errorMessage) {
	if (!errorMessage) return false;
	return (
		errorMessage.includes("nvidia-nim-retry-budget-exhausted") ||
		errorMessage.includes("nvidia-nim-server-error-exhausted") ||
		isContextOverflowErrorMessage(errorMessage)
	);
}

/**
 * @param {{
 *   chain: string[];
 *   contextMargin: number;
 *   catalog: Map<string, ModelCatalogEntry>;
 *   estimated: number;
 *   needsVision: boolean;
 *   sticky: string | null;
 * }} opts
 */
export function formatRouterStatus({
	chain,
	contextMargin,
	catalog,
	estimated,
	needsVision,
	sticky,
}) {
	const eligible = getEligibleChain(chain, catalog, estimated, needsVision, contextMargin);
	const lines = [
		`NVIDIA Router (${ROUTER_MODEL_ID})`,
		`Sticky: ${sticky ?? "(none)"}`,
		`Chain: ${chain.join(" → ")}`,
		`Context margin: ${contextMargin}x`,
		`Estimated tokens: ${estimated}${needsVision ? " (vision)" : ""}`,
		"",
		"Eligible for current context:",
		...(eligible.length > 0 ? eligible.map((id) => `  ✓ ${id}`) : ["  (none — context too large or no vision support)"]),
	];
	return lines.join("\n");
}

/**
 * Pick starting candidate: sticky if still eligible, else first eligible in chain.
 * @param {string | null} stickyId
 * @param {string[]} eligible
 * @param {string[]} chain
 */
export function pickInitialCandidate(stickyId, eligible, chain) {
	if (stickyId && eligible.includes(stickyId)) return stickyId;
	for (const id of chain) {
		if (eligible.includes(id)) return id;
	}
	return eligible[0] ?? null;
}

/**
 * @param {string} currentId
 * @param {string[]} eligible
 * @param {string[]} chain
 */
export function nextCandidate(currentId, eligible, chain) {
	const order = chain.filter((id) => eligible.includes(id));
	const idx = order.indexOf(currentId);
	if (idx === -1) return order[0] ?? null;
	for (let i = idx + 1; i < order.length; i++) {
		return order[i];
	}
	return null;
}
