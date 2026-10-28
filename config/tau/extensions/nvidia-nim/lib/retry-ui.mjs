import { RETRY_TAG } from "./retry-helpers.mjs";

const VERBOSE_CONSOLE = process.env.NVIDIA_RETRY_VERBOSE_CONSOLE === "1";

export function isRetryVerboseConsole() {
	return VERBOSE_CONSOLE;
}

/** @typedef {"429" | "5xx"} RetryKind */

/**
 * @typedef {object} RetryEntry
 * @property {string} modelId
 * @property {RetryKind} [kind]
 * @property {number} [attempt]
 * @property {number} [max]
 * @property {boolean} [waiting]
 * @property {number} [backoffEndsAt]
 */

/** @type {{ setWorkingMessage: (message?: string) => void }} */
let uiRef = {
	setWorkingMessage: () => {},
};

/** @type {Map<string, RetryEntry>} */
const entries = new Map();

/** @type {ReturnType<typeof setInterval> | null} */
let countdownTimer = null;

/**
 * @param {{ setWorkingMessage?: (message?: string) => void }} ui
 */
export function bindRetryUi(ui) {
	uiRef = {
		setWorkingMessage: (message) => ui?.setWorkingMessage?.(message),
	};
}

export function resetRetryUi() {
	entries.clear();
	stopCountdown();
	clearRetryUi();
}

export function clearRetryUi() {
	uiRef.setWorkingMessage(undefined);
}

function shortModelId(modelId) {
	const parts = modelId.split("/");
	return parts[parts.length - 1] ?? modelId;
}

function renderWorkingMessage() {
	const waiting = [...entries.values()].filter((entry) => entry.waiting);
	if (waiting.length === 0) {
		return null;
	}

	if (waiting.length === 1) {
		const entry = waiting[0];
		const seconds = Math.max(
			0,
			Math.ceil(((entry.backoffEndsAt ?? Date.now()) - Date.now()) / 1000),
		);
		const label = entry.kind === "5xx" ? "Server error" : "Rate limited";
		return `${label} — ${shortModelId(entry.modelId)} retry ${entry.attempt}/${entry.max} in ${seconds}s…`;
	}

	const maxAttempt = Math.max(...waiting.map((entry) => entry.attempt ?? 0));
	const maxMax = Math.max(...waiting.map((entry) => entry.max ?? 0));
	return `Rate limited — ${waiting.length} requests retrying (max ${maxAttempt}/${maxMax})…`;
}

function pushWorkingMessage() {
	const message = renderWorkingMessage();
	if (message) {
		uiRef.setWorkingMessage(message);
	} else if (entries.size === 0) {
		clearRetryUi();
	}
}

function startCountdown() {
	if (countdownTimer) {
		return;
	}
	countdownTimer = setInterval(() => {
		if ([...entries.values()].some((entry) => entry.waiting)) {
			pushWorkingMessage();
		} else {
			stopCountdown();
		}
	}, 1000);
}

function stopCountdown() {
	if (countdownTimer) {
		clearInterval(countdownTimer);
		countdownTimer = null;
	}
}

function logVerbose(modelId, kind, attempt, max, backoffMs, requestId) {
	if (!VERBOSE_CONSOLE) {
		return;
	}
	const kindLabel = kind === "5xx" ? "5xx" : "429";
	const requestNote = requestId ? ` (request ID: ${requestId})` : "";
	console.log(
		`${RETRY_TAG} ${modelId} — ${kindLabel} on attempt ${attempt}/${max}; ` +
		`retrying after ${backoffMs}ms${requestNote}.`,
	);
}

/**
 * @param {string} queueKey
 * @param {{ modelId: string }} details
 */
export function trackRetryStart(queueKey, { modelId }) {
	entries.set(queueKey, { modelId, waiting: false });
}

/**
 * @param {string} queueKey
 * @param {{ modelId: string, kind: RetryKind, attempt: number, max: number, backoffMs: number, requestId?: string }} details
 */
export function trackRetryWait(queueKey, { modelId, kind, attempt, max, backoffMs, requestId }) {
	entries.set(queueKey, {
		modelId,
		kind,
		attempt,
		max,
		waiting: true,
		backoffEndsAt: Date.now() + backoffMs,
	});
	logVerbose(modelId, kind, attempt, max, backoffMs, requestId);
	pushWorkingMessage();
	startCountdown();
}

/**
 * @param {string} queueKey
 */
export function trackRetryEnd(queueKey) {
	entries.delete(queueKey);
	if (entries.size === 0) {
		stopCountdown();
		clearRetryUi();
	} else {
		pushWorkingMessage();
	}
}
