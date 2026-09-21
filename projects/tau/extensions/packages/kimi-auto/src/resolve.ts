/**
 * kimi-auto state resolution — pure functions shared by the omp extension.
 *
 * Reads the resolver's shared state file (~/.local/share/kimi-auto/state.json),
 * written by the kimi-auto-resolver pitchfork daemon (event-driven, 15-min
 * backstop). The single source of truth for "which model is best right now"
 * lives in the shim (herd surface); these helpers expose the same resolution
 * for Tau sessions without duplicating selection logic.
 */

export interface KimiCandidate {
	id: string;
	ok: boolean;
	latency_ms: number;
	note: string;
}

export interface KimiAutoState {
	model: string | null;
	healthy: boolean;
	reason: string;
	updated_at: string | null;
	resolver: string | null;
	secrets_present: string[];
	secrets_missing: string[];
	candidates: KimiCandidate[];
}

const DEFAULT_STATE: KimiAutoState = {
	model: null,
	healthy: false,
	reason: "no state loaded",
	updated_at: null,
	resolver: null,
	secrets_present: [],
	secrets_missing: [],
	candidates: [],
};

function asStringArray(v: unknown): string[] {
	return Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : [];
}

function asCandidates(v: unknown): KimiCandidate[] {
	if (!Array.isArray(v)) return [];
	return v
		.filter((c): c is Record<string, unknown> => typeof c === "object" && c !== null)
		.map((c) => ({
			id: typeof c.id === "string" ? c.id : "(unknown)",
			ok: c.ok === true,
			latency_ms: typeof c.latency_ms === "number" ? c.latency_ms : -1,
			note: typeof c.note === "string" ? c.note : "",
		}));
}

/** Parse a state.json blob. Never throws — garbage yields unhealthy state. */
export function readState(raw: string): KimiAutoState {
	let data: unknown;
	try {
		data = JSON.parse(raw);
	} catch (err) {
		return { ...DEFAULT_STATE, reason: `state parse failed: ${(err as Error).message}` };
	}
	if (typeof data !== "object" || data === null) {
		return { ...DEFAULT_STATE, reason: "state is not a JSON object" };
	}
	const d = data as Record<string, unknown>;
	const model = typeof d.model === "string" && d.model !== "" ? d.model : null;
	const healthy = d.healthy === true && model !== null;
	return {
		model,
		healthy,
		reason: typeof d.reason === "string" && d.reason !== "" ? d.reason : "unknown",
		updated_at: typeof d.updated_at === "string" ? d.updated_at : null,
		resolver: typeof d.resolver === "string" ? d.resolver : null,
		secrets_present: asStringArray(d.secrets_present),
		secrets_missing: asStringArray(d.secrets_missing),
		candidates: asCandidates(d.candidates),
	};
}

export type Resolution = { model: string } | { error: string };

/**
 * Resolve the alias to a concrete model id, or fail loud.
 * Mirrors shim.py resolve_target: model-agnostic, no silent fallback, and
 * never routes the alias back into itself (routing-loop guard).
 */
export function resolveModel(state: KimiAutoState): Resolution {
	if (!state.healthy || !state.model) {
		return {
			error:
				`kimi-auto: no healthy model available (${state.reason}). ` +
				`Provide API keys (e.g. MOONSHOT_API_KEY, OPENROUTER_API_KEY) so the ` +
				`resolver has healthy candidates to select from.`,
		};
	}
	if (state.model.toLowerCase() === "kimi-auto") {
		return {
			error:
				"kimi-auto: resolver state points at the kimi-auto alias itself " +
				"(self-reference refused; check the resolver).",
		};
	}
	return { model: state.model };
}

/** True when the state is older than maxAgeMs or has no parseable timestamp. */
export function isStale(state: KimiAutoState, nowMs: number, maxAgeMs: number): boolean {
	if (!state.updated_at) return true;
	const ts = Date.parse(state.updated_at);
	if (Number.isNaN(ts)) return true;
	return nowMs - ts > maxAgeMs;
}

/** Human-readable status: resolution, latency, freshness, candidate table. */
export function formatStatus(state: KimiAutoState, nowMs: number, maxAgeMs = 15 * 60_000): string {
	const lines: string[] = [];
	const stale = isStale(state, nowMs, maxAgeMs);
	const healthTag = state.healthy ? "HEALTHY" : "UNHEALTHY";
	const freshTag = stale ? "STALE" : "fresh";
	lines.push(`kimi-auto [${healthTag}, ${freshTag}]`);
	lines.push(`  resolves to : ${state.model ?? "(none)"}`);
	if (state.updated_at) lines.push(`  updated at  : ${state.updated_at}`);
	if (stale) {
		lines.push(
			`  STALE: resolver has not written state within ${Math.round(maxAgeMs / 60000)}m ` +
				`(check the kimi-auto-resolver pitchfork daemon).`,
		);
	}
	if (!state.healthy) lines.push(`  reason      : ${state.reason}`);
	const missing = state.secrets_missing;
	if (missing.length > 0) lines.push(`  missing keys: ${missing.join(", ")}`);
	if (state.candidates.length > 0) {
		lines.push("  candidates  :");
		for (const c of state.candidates) {
			const mark = c.ok ? "ok " : "FAIL";
			lines.push(`    [${mark}] ${c.id} ${c.latency_ms}ms (${c.note})`);
		}
	}
	return lines.join("\n");
}

/** Default state path, honoring KIMI_AUTO_STATE. */
export function defaultStatePath(env: NodeJS.ProcessEnv = process.env): string {
	if (env.KIMI_AUTO_STATE) return env.KIMI_AUTO_STATE;
	const home = env.HOME ?? env.USERPROFILE ?? "";
	return `${home}/.local/share/kimi-auto/state.json`;
}

/** Default herd base URL, honoring KIMI_AUTO_HERD. */
export function defaultHerdUrl(env: NodeJS.ProcessEnv = process.env): string {
	return env.KIMI_AUTO_HERD ?? "http://127.0.0.1:25100";
}
