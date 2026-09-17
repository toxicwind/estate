/**
 * flock HTTP client — Tau's integration with the flock NVIDIA NIM proxy.
 *
 * flock (renamed 2026-09-17 from nim-proxy) is the local enforcement point
 * for the NVIDIA NIM surface: rate limiting, history, operator dashboard,
 * and an OpenAI-compatible front that forwards upstream to
 * https://integrate.api.nvidia.com/v1. It never serves local models.
 *
 * Configuration (environment):
 *   FLOCK_BASE_URL   Proxy base URL (default http://127.0.0.1:8000).
 *   FLOCK_API_KEY    Proxy client key (Authorization: Bearer). Optional;
 *                    falls back to NVIDIA_API_KEY, then NIM_PROXY_API_KEY.
 *                    Required for /v1/models and /v1/chat/completions.
 *   FLOCK_TIMEOUT_MS Per-request timeout (default 60000, clamp 1000..600000).
 *   FLOCK_DISABLED=1 Skip the extension entirely.
 */

export type EnvLike = Record<string, string | undefined>;

export interface FlockConfig {
	baseUrl: string;
	apiKey: string | null;
	timeoutMs: number;
}

export const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

export function resolveTimeoutMs(env: EnvLike): number {
	const raw = Number(env.FLOCK_TIMEOUT_MS ?? "");
	if (Number.isFinite(raw) && raw >= 1_000 && raw <= 600_000) return raw;
	return 60_000;
}

export function resolveApiKey(env: EnvLike): string | null {
	return (
		env.FLOCK_API_KEY ??
		env.NVIDIA_API_KEY ??
		env.NIM_PROXY_API_KEY ??
		null
	);
}

export function resolveConfig(env: EnvLike): FlockConfig {
	return {
		baseUrl: (env.FLOCK_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/+$/, ""),
		apiKey: resolveApiKey(env),
		timeoutMs: resolveTimeoutMs(env),
	};
}

export type FlockErrorKind =
	| "network"
	| "timeout"
	| "auth"
	| "http"
	| "api"
	| "empty";

export class FlockError extends Error {
	readonly kind: FlockErrorKind;
	readonly status: number | undefined;

	constructor(kind: FlockErrorKind, message: string, status?: number) {
		super(message);
		this.name = "FlockError";
		this.kind = kind;
		this.status = status;
	}
}

function needsKey(cfg: FlockConfig): asserts cfg is FlockConfig & {
	apiKey: string;
} {
	if (!cfg.apiKey) {
		throw new FlockError(
			"auth",
			"flock: no proxy API key. Set FLOCK_API_KEY (or NVIDIA_API_KEY / NIM_PROXY_API_KEY).",
		);
	}
}

async function request(
	cfg: FlockConfig,
	path: string,
	init: RequestInit,
	timeoutMs: number,
	signal?: AbortSignal,
): Promise<{ status: number; body: string }> {
	const ctrl = new AbortController();
	const timer = setTimeout(() => ctrl.abort(), timeoutMs);
	const onOuterAbort = (): void => ctrl.abort();
	if (signal) {
		if (signal.aborted) ctrl.abort();
		else signal.addEventListener("abort", onOuterAbort, { once: true });
	}
	try {
		const res = await fetch(`${cfg.baseUrl}${path}`, {
			...init,
			signal: ctrl.signal,
		});
		const body = await res.text();
		return { status: res.status, body };
	} catch (err) {
		if (ctrl.signal.aborted) {
			throw new FlockError(
				"timeout",
				`flock: request to ${path} timed out after ${timeoutMs}ms`,
			);
		}
		throw new FlockError(
			"network",
			`flock: request to ${path} failed: ${(err as Error).message}`,
		);
	} finally {
		clearTimeout(timer);
		signal?.removeEventListener("abort", onOuterAbort);
	}
}

function authHeaders(cfg: FlockConfig): Record<string, string> {
	return {
		Authorization: `Bearer ${cfg.apiKey}`,
		"Content-Type": "application/json",
	};
}

function parseBody<T>(path: string, status: number, body: string): T {
	try {
		return JSON.parse(body) as T;
	} catch {
		throw new FlockError(
			"http",
			`flock: ${path} returned non-JSON (status ${status}): ${body.slice(0, 200)}`,
			status,
		);
	}
}

function checkError(path: string, status: number, body: string): void {
	if (status === 401 || status === 403) {
		throw new FlockError(
			"auth",
			`flock: ${path} rejected (status ${status}): missing or invalid proxy API key. Set FLOCK_API_KEY.`,
			status,
		);
	}
	if (status === 429) {
		throw new FlockError(
			"api",
			`flock: ${path} rate limited (status 429) by the proxy or upstream.`,
			status,
		);
	}
	if (status < 200 || status >= 300) {
		const msg = body.slice(0, 300);
		throw new FlockError(
			"http",
			`flock: ${path} failed with status ${status}: ${msg}`,
			status,
		);
	}
}

// ---- Public API -----------------------------------------------------------

/** GET /health — the proxy answers "ok" when the daemon is up. */
export async function flockHealth(
	env: EnvLike = process.env as EnvLike,
): Promise<{ ok: boolean; body: string }> {
	const cfg = resolveConfig(env);
	const { status, body } = await request(
		cfg,
		"/health",
		{ method: "GET" },
		cfg.timeoutMs,
	);
	if (status !== 200) {
		throw new FlockError("http", `flock: /health returned ${status}`, status);
	}
	const text = body.trim();
	return { ok: text === "ok", body: text };
}

export interface FlockModel {
	id: string;
	object?: string;
	created?: number;
	owned_by?: string;
}

/** GET /v1/models — OpenAI-compatible model list (requires proxy API key). */
export async function flockModels(
	env: EnvLike = process.env as EnvLike,
): Promise<FlockModel[]> {
	const cfg = resolveConfig(env);
	needsKey(cfg);
	const { status, body } = await request(
		cfg,
		"/v1/models",
		{ method: "GET", headers: authHeaders(cfg) },
		cfg.timeoutMs,
	);
	checkError("/v1/models", status, body);
	const json = parseBody<{ data?: unknown }>("/v1/models", status, body);
	if (!Array.isArray(json.data)) {
		throw new FlockError(
			"api",
			`flock: /v1/models response has no data array: ${body.slice(0, 200)}`,
			status,
		);
	}
	return json.data as FlockModel[];
}

export interface FlockChatOptions {
	model?: string;
	system?: string;
	temperature?: number;
	maxTokens?: number;
	timeoutMs?: number;
	signal?: AbortSignal;
	env?: EnvLike;
}

export interface FlockChatResult {
	model: string;
	content: string;
	finishReason?: string;
	promptTokens?: number;
	completionTokens?: number;
	totalTokens?: number;
}

/** POST /v1/chat/completions — requires proxy API key; rejects empty content. */
export async function flockChat(
	prompt: string,
	opts: FlockChatOptions = {},
): Promise<FlockChatResult> {
	const cfg = resolveConfig(opts.env ?? (process.env as EnvLike));
	needsKey(cfg);
	if (!prompt || prompt.trim() === "") {
		throw new FlockError("api", "flock: prompt must not be empty");
	}
	const timeoutMs =
		opts.timeoutMs !== undefined &&
		Number.isFinite(opts.timeoutMs) &&
		opts.timeoutMs >= 1_000 &&
		opts.timeoutMs <= 600_000
			? opts.timeoutMs
			: cfg.timeoutMs;

	const messages: Array<{ role: string; content: string }> = [];
	if (opts.system) messages.push({ role: "system", content: opts.system });
	messages.push({ role: "user", content: prompt });

	const payload: Record<string, unknown> = {
		model: opts.model ?? "",
		messages,
	};
	if (opts.temperature !== undefined) payload.temperature = opts.temperature;
	if (opts.maxTokens !== undefined) payload.max_tokens = opts.maxTokens;

	const { status, body } = await request(
		cfg,
		"/v1/chat/completions",
		{
			method: "POST",
			headers: authHeaders(cfg),
			body: JSON.stringify(payload),
		},
		timeoutMs,
		opts.signal,
	);
	checkError("/v1/chat/completions", status, body);

	const json = parseBody<{
		model?: string;
		choices?: Array<{
			message?: { content?: unknown };
			finish_reason?: string;
		}>;
		usage?: {
			prompt_tokens?: number;
			completion_tokens?: number;
			total_tokens?: number;
		};
	}>("/v1/chat/completions", status, body);

	const choice = json.choices?.[0];
	const raw = choice?.message?.content;
	const content = typeof raw === "string" ? raw : "";
	if (content.trim() === "") {
		throw new FlockError(
			"empty",
			`flock: ${json.model ?? opts.model ?? "(unknown model)"} returned empty content (finish_reason=${choice?.finish_reason ?? "unknown"})`,
			status,
		);
	}
	return {
		model: json.model ?? opts.model ?? "",
		content,
		finishReason: choice?.finish_reason,
		promptTokens: json.usage?.prompt_tokens,
		completionTokens: json.usage?.completion_tokens,
		totalTokens: json.usage?.total_tokens,
	};
}
