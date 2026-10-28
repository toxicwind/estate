/** @typedef {{ provider?: string; api?: string; id?: string }} ModelLike */

export const NVIDIA_PROVIDER_IDS = new Set(["nvidia", "nvidia-nim"]);
export const RETRY_TAG = "[nvidia-rate-limit-retry]";
export const EXHAUSTION_MARKER = "nvidia-nim-retry-budget-exhausted";
export const SERVER_ERROR_EXHAUSTION_MARKER = "nvidia-nim-server-error-exhausted";

export function parseIntEnv(v, fallback) {
	if (!v) return fallback;
	const n = Number.parseInt(v, 10);
	return Number.isFinite(n) && n > 0 ? n : fallback;
}

export function parseFloatEnv(v, fallback) {
	if (!v) return fallback;
	const n = Number.parseFloat(v);
	return Number.isFinite(n) ? n : fallback;
}

export function isRateLimitErrorMessage(text) {
	if (!text) return false;
	const err = text.toLowerCase();
	return (
		err.includes("429") ||
		err.includes("rate limit") ||
		err.includes("too many requests") ||
		err.includes("throttl") ||
		err.includes("please wait")
	);
}

/** @param {string | undefined} text */
export function isServerErrorMessage(text) {
	if (!text || isRateLimitErrorMessage(text)) return false;
	const err = text.toLowerCase();
	return (
		err.includes("internal server error") ||
		err.includes("server error") ||
		err.includes("service unavailable") ||
		err.includes("bad gateway") ||
		err.includes("gateway timeout") ||
		/\b5\d{2}\b/.test(err)
	);
}

/** @param {string | undefined} errorMessage */
export function isServerErrorExhaustionMessage(errorMessage) {
	return Boolean(errorMessage?.includes(SERVER_ERROR_EXHAUSTION_MARKER));
}

/**
 * @param {unknown} error
 * @returns {string | undefined}
 */
export function extractRequestId(error) {
	if (!error || typeof error !== "object") return undefined;
	const rec = /** @type {Record<string, unknown>} */ (error);
	if (typeof rec.requestId === "string") return rec.requestId;
	if (typeof rec.request_id === "string") return rec.request_id;
	const headers = rec.headers;
	if (headers && typeof headers === "object") {
		const h = /** @type {Record<string, string | undefined>} */ (headers);
		return h["x-request-id"] ?? h["x-nvca-request-id"];
	}
	return undefined;
}

/** @param {ModelLike | null | undefined} model */
export function isNvidiaCall(model) {
	if (!model) return false;
	if (model.provider && NVIDIA_PROVIDER_IDS.has(model.provider)) return true;
	if (model.api === "openai-completions" && typeof model.id === "string") {
		return model.id.toLowerCase().startsWith("nvidia/");
	}
	return false;
}

/** @param {string | undefined} errorMessage */
export function isExhaustionMessage(errorMessage) {
	return Boolean(errorMessage?.includes(EXHAUSTION_MARKER));
}

/**
 * 429/5xx are only retried before the first forwarded token.
 * Mid-stream errors must not restart the request (would corrupt the TUI).
 * @param {{ forwardedContent?: boolean; is429?: boolean; is5xx?: boolean }} opts
 */
export function canRetryNvidiaTransportError({ forwardedContent, is429, is5xx }) {
	if (forwardedContent) return false;
	return Boolean(is429 || is5xx);
}

export function computeBackoffMs(attempt, baseMs, capMs, jitter, random = Math.random) {
	const ideal = Math.min(capMs, baseMs * 2 ** Math.max(0, attempt - 1));
	const jitterRange = ideal * jitter;
	const offset = (random() * 2 - 1) * jitterRange;
	return Math.max(0, Math.round(ideal + offset));
}

export function backoffMs(attempt, baseMs, capMs, jitter, abortSignal) {
	const delay = computeBackoffMs(attempt, baseMs, capMs, jitter);
	return new Promise((resolve, reject) => {
		if (abortSignal?.aborted) {
			reject(new Error("aborted"));
			return;
		}
		const onAbort = () => {
			clearTimeout(timer);
			reject(new Error("aborted"));
		};
		const onTimer = () => {
			abortSignal?.removeEventListener("abort", onAbort);
			resolve();
		};
		const timer = setTimeout(onTimer, delay);
		abortSignal?.addEventListener("abort", onAbort, { once: true });
	});
}

export function readRetryConfig(env = process.env) {
	return {
		maxAttempts: parseIntEnv(env.NVIDIA_RETRY_MAX, 20),
		baseMs: parseIntEnv(env.NVIDIA_RETRY_BASE_MS, 2_000),
		capMs: parseIntEnv(env.NVIDIA_RETRY_CAP_MS, 60_000),
		jitter: Math.max(
			0,
			Math.min(1, parseFloatEnv(env.NVIDIA_RETRY_JITTER, 0.2)),
		),
		serverErrorMaxAttempts: parseIntEnv(env.NVIDIA_RETRY_SERVER_ERROR_MAX, 3),
		serverErrorBaseMs: parseIntEnv(env.NVIDIA_RETRY_SERVER_ERROR_BASE_MS, 2_000),
		serverErrorCapMs: parseIntEnv(env.NVIDIA_RETRY_SERVER_ERROR_CAP_MS, 15_000),
		testInject429: parseIntEnv(env.NVIDIA_RETRY_TEST_INJECT_429, 0),
		testInject500: parseIntEnv(env.NVIDIA_RETRY_TEST_INJECT_500, 0),
		testInjectModel: env.NVIDIA_RETRY_TEST_INJECT_MODEL?.trim() ?? "",
	};
}

const RETRYABLE_PROVIDER_ERROR_PATTERN =
	/rate.?limit|429|too many requests|overloaded|5\d{2}|service.?unavailable|server.?error|internal.?error|timeout|socket hang up|fetch failed|network|econnreset|enotfound/i;

const NON_RETRYABLE_PROVIDER_LIMIT_ERROR_PATTERN =
	/insufficient_quota|billing|credit|payment|exceeded.*quota|usage limit/i;

export function matchesPiRetryablePattern(text) {
	return RETRYABLE_PROVIDER_ERROR_PATTERN.test(text);
}

export function matchesPiNonRetryableLimitPattern(text) {
	return NON_RETRYABLE_PROVIDER_LIMIT_ERROR_PATTERN.test(text);
}
