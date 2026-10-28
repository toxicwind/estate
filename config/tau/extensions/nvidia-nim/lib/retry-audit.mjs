import { appendFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

export const DEFAULT_AUDIT_LOG = join(homedir(), ".pi", "nvidia-nim-retry.log");

/** @typedef {"session_start" | "request_start" | "429_retry" | "5xx_retry" | "recovered" | "exhausted" | "server_error_exhausted" | "surfaced_error" | "aborted" | "provider_response"} AuditEventType */

/**
 * @typedef {object} SessionRetryStats
 * @property {number} requests
 * @property {number} rateLimitHits
 * @property {number} serverErrorHits
 * @property {number} recoveries
 * @property {number} exhaustions
 * @property {number} serverErrorExhaustions
 * @property {number} surfacedErrors
 * @property {string | null} lastModel
 * @property {string | null} lastError
 * @property {string | null} lastRequestId
 * @property {string | null} lastEventAt
 * @property {number | null} lastBackoffMs
 */

/** @type {SessionRetryStats} */
const sessionStats = {
	requests: 0,
	rateLimitHits: 0,
	serverErrorHits: 0,
	recoveries: 0,
	exhaustions: 0,
	serverErrorExhaustions: 0,
	surfacedErrors: 0,
	lastModel: null,
	lastError: null,
	lastRequestId: null,
	lastEventAt: null,
	lastBackoffMs: null,
};

let auditLogPath = DEFAULT_AUDIT_LOG;
let auditEnabled = true;
/** @type {string | null} */
let lastProviderRequestId = null;

export function setLastProviderRequestId(requestId) {
	lastProviderRequestId =
		typeof requestId === "string" && requestId.length > 0 ? requestId : null;
}

export function getLastProviderRequestId() {
	return lastProviderRequestId;
}

export function consumeLastProviderRequestId() {
	const id = lastProviderRequestId;
	lastProviderRequestId = null;
	return id;
}

function nowIso() {
	return new Date().toISOString();
}

function resolveAuditEnabled(env = process.env) {
	const raw = env.NVIDIA_RETRY_AUDIT?.trim().toLowerCase();
	if (raw === "0" || raw === "false" || raw === "off") return false;
	return true;
}

export function configureRetryAudit(env = process.env) {
	auditEnabled = resolveAuditEnabled(env);
	if (env.NVIDIA_RETRY_AUDIT_LOG?.trim()) {
		auditLogPath = env.NVIDIA_RETRY_AUDIT_LOG.trim();
	} else {
		auditLogPath = DEFAULT_AUDIT_LOG;
	}
}

configureRetryAudit();

/**
 * @param {AuditEventType} event
 * @param {Record<string, unknown>} [details]
 */
export function recordRetryAudit(event, details = {}) {
	const ts = nowIso();
	sessionStats.lastEventAt = ts;

	if (details.model && typeof details.model === "string") {
		sessionStats.lastModel = details.model;
	}
	if (typeof details.backoffMs === "number") {
		sessionStats.lastBackoffMs = details.backoffMs;
	}
	if (typeof details.error === "string") {
		sessionStats.lastError = details.error;
	}
	if (typeof details.requestId === "string") {
		sessionStats.lastRequestId = details.requestId;
	}

	switch (event) {
		case "session_start":
			resetSessionRetryStats();
			break;
		case "request_start":
			sessionStats.requests += 1;
			break;
		case "429_retry":
			sessionStats.rateLimitHits += 1;
			break;
		case "5xx_retry":
			sessionStats.serverErrorHits += 1;
			break;
		case "recovered":
			sessionStats.recoveries += 1;
			break;
		case "exhausted":
			sessionStats.exhaustions += 1;
			break;
		case "server_error_exhausted":
			sessionStats.serverErrorExhaustions += 1;
			break;
		case "surfaced_error":
			sessionStats.surfacedErrors += 1;
			break;
		case "provider_response":
			break;
		default:
			break;
	}

	if (!auditEnabled) return;

	const line = JSON.stringify({ ts, event, ...details });
	try {
		mkdirSync(dirname(auditLogPath), { recursive: true });
		appendFileSync(auditLogPath, `${line}\n`, "utf8");
	} catch {
		// never break retry path for logging failures
	}
}

export function resetSessionRetryStats() {
	sessionStats.requests = 0;
	sessionStats.rateLimitHits = 0;
	sessionStats.serverErrorHits = 0;
	sessionStats.recoveries = 0;
	sessionStats.exhaustions = 0;
	sessionStats.serverErrorExhaustions = 0;
	sessionStats.surfacedErrors = 0;
	sessionStats.lastModel = null;
	sessionStats.lastError = null;
	sessionStats.lastRequestId = null;
	sessionStats.lastEventAt = null;
	sessionStats.lastBackoffMs = null;
}

export function getSessionRetryStats() {
	return { ...sessionStats };
}

export function getAuditLogPath() {
	return auditLogPath;
}

/**
 * @param {object} config
 * @param {number} config.maxAttempts
 * @param {number} config.baseMs
 * @param {number} config.capMs
 * @param {number} config.jitter
 */
export function formatRetryStatus(config) {
	const stats = getSessionRetryStats();
	const lines = [
		"NVIDIA rate-limit retry (this session)",
		`Audit log: ${getAuditLogPath()}${auditEnabled ? "" : " (disabled via NVIDIA_RETRY_AUDIT=0)"}`,
		`Config: max ${config.maxAttempts}, base ${config.baseMs}ms, cap ${config.capMs}ms, jitter ${config.jitter * 100}%`,
		"",
		`Requests wrapped: ${stats.requests}`,
		`429 retry events: ${stats.rateLimitHits}`,
		`5xx retry events: ${stats.serverErrorHits}`,
		`Recovered after retry: ${stats.recoveries}`,
		`429 exhausted (gave up): ${stats.exhaustions}`,
		`5xx exhausted (gave up): ${stats.serverErrorExhaustions}`,
		`Non-retryable / leaked errors: ${stats.surfacedErrors}`,
		"",
		`Last model: ${stats.lastModel ?? "(none)"}`,
		`Last event: ${stats.lastEventAt ?? "(none)"}`,
	];

	if (stats.lastBackoffMs != null) {
		lines.push(`Last backoff: ${stats.lastBackoffMs}ms`);
	}
	if (stats.lastError) {
		lines.push(`Last error: ${stats.lastError}`);
	}
	if (stats.lastRequestId) {
		lines.push(`Last request ID: ${stats.lastRequestId}`);
	}

	lines.push("");
	lines.push("Subcommands: /nim-retry-status reset");
	return lines.join("\n");
}
