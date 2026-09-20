/**
 * omp-kimi-auto extension entry point.
 *
 * Zero-config `kimi-auto` alias for Tau/omp sessions: every command and tool
 * routes through the herd surface with `model: "kimi-auto"`, and the shim
 * resolves it to the current best live Kimi endpoint (15-min resolver audit).
 *
 *   /kimi-auto <prompt>   One prompt through the alias; shows resolution first.
 *   /kimi-auto-status      Current resolution + latency + resolver freshness.
 *   /kimi-auto-resolve     Print just the resolved model id (scripting).
 *   kimi_auto_ask (tool)   LLM-callable chat via the alias.
 *   kimi_auto_status (tool) LLM-callable status.
 *
 * Configuration (environment):
 *   KIMI_AUTO_STATE      Resolver state path (default
 *                        ~/.local/share/kimi-auto/state.json).
 *   KIMI_AUTO_HERD       Herd base URL (default http://127.0.0.1:25100).
 *   KIMI_AUTO_TIMEOUT_MS Chat timeout (default 120000).
 *   KIMI_AUTO_MAX_TOKENS Max completion tokens (default 1024).
 *   KIMI_AUTO_DISABLED=1 Skip the extension entirely.
 *
 * The extension loads (with a warning) even when the resolver state is
 * missing; commands fail loud instead of silently no-op'ing.
 */

import type { ExtensionAPI, ExtensionContext } from "@oh-my-pi/pi-coding-agent";
import { z } from "zod/v4";
import { chatOnce, truncateOutput, DEFAULT_MAX_TOKENS, DEFAULT_TIMEOUT_MS } from "./herd.ts";
import {
	defaultHerdUrl,
	defaultStatePath,
	formatStatus,
	isStale,
	readState,
	resolveModel,
	type KimiAutoState,
} from "./resolve.ts";

const DEBUG = process.env.KIMI_AUTO_DEBUG === "1";
const DISABLED = process.env.KIMI_AUTO_DISABLED === "1";
const STALE_AFTER_MS = 15 * 60_000;

function debug(...args: unknown[]): void {
	if (DEBUG) {
		// eslint-disable-next-line no-console
		console.error("[omp-kimi-auto]", ...args);
	}
}

interface AutoState {
	statePath: string;
	herdUrl: string;
	timeoutMs: number;
	maxTokens: number;
	last: KimiAutoState | null;
}

function numEnv(name: string, fallback: number): number {
	const raw = Number(process.env[name] ?? "");
	return Number.isInteger(raw) && raw > 0 ? raw : fallback;
}

async function loadStateFile(path: string): Promise<KimiAutoState> {
	try {
		const raw = await Bun.file(path).text();
		return readState(raw);
	} catch (err) {
		debug("state read failed:", err);
		return readState(""); // parse failure -> unhealthy, never throws
	}
}

function emitResult(pi: ExtensionAPI, customType: string, stdout: string, stderr = ""): void {
	const parts = [truncateOutput(stdout.trim())];
	if (stderr.trim() !== "") {
		parts.push("--- stderr ---");
		parts.push(truncateOutput(stderr.trim()));
	}
	pi.sendMessage(
		{
			customType,
			content: parts.join("\n\n"),
			display: true,
			attribution: "agent",
		},
		{ triggerTurn: false },
	);
}

const askParameters = z.object({
	prompt: z.string().min(1).describe("The prompt to send through the kimi-auto alias."),
	maxTokens: z
		.number()
		.int()
		.min(1)
		.max(32000)
		.optional()
		.describe("Max completion tokens (default from KIMI_AUTO_MAX_TOKENS, 1024)."),
	timeoutMs: z
		.number()
		.int()
		.min(1000)
		.max(600000)
		.optional()
		.describe("Timeout in ms (default from KIMI_AUTO_TIMEOUT_MS, 120000)."),
});

export default function kimiAutoExtension(pi: ExtensionAPI): void {
	pi.setLabel("Kimi Auto");
	const state: AutoState = {
		statePath: defaultStatePath(),
		herdUrl: defaultHerdUrl(),
		timeoutMs: numEnv("KIMI_AUTO_TIMEOUT_MS", DEFAULT_TIMEOUT_MS),
		maxTokens: numEnv("KIMI_AUTO_MAX_TOKENS", DEFAULT_MAX_TOKENS),
		last: null,
	};

	const refresh = async (ctx: ExtensionContext): Promise<KimiAutoState> => {
		const s = await loadStateFile(state.statePath);
		state.last = s;
		const r = resolveModel(s);
		const stale = isStale(s, Date.now(), STALE_AFTER_MS);
		const label =
			"model" in r
				? `kimi-auto: ${r.model}${stale ? " (stale)" : ""}`
				: `kimi-auto: unresolved${stale ? " (stale)" : ""}`;
		ctx.ui.setStatus("kimi-auto", label);
		return s;
	};

	// ---- Lifecycle ----------------------------------------------------------

	pi.on("session_start", async (_event, ctx) => {
		if (DISABLED) {
			ctx.ui.notify("kimi-auto: KIMI_AUTO_DISABLED=1, extension inactive", "info");
			return;
		}
		const s = await refresh(ctx);
		if (!s.healthy) {
			ctx.ui.notify(
				`kimi-auto: no healthy Kimi model right now (${s.reason}) — ` +
					`/kimi-auto-status for detail`,
				"warning",
			);
		}
	});

	// ---- /kimi-auto -----------------------------------------------------------

	pi.registerCommand("kimi-auto", {
		description:
			"Run one prompt through the kimi-auto alias (best live Kimi endpoint, " +
			"auto-resolved by the 15-min resolver audit).",
		handler: async (args, ctx) => {
			const prompt = args.trim();
			if (!prompt) {
				ctx.ui.notify("usage: /kimi-auto <prompt>", "warning");
				return;
			}
			const s = await refresh(ctx);
			const r = resolveModel(s);
			if ("error" in r) {
				ctx.ui.notify(r.error, "error");
				return;
			}
			ctx.ui.notify(`kimi-auto: routing to ${r.model}…`, "info");
			try {
				const out = await chatOnce(prompt, {
					herdUrl: state.herdUrl,
					timeoutMs: state.timeoutMs,
					maxTokens: state.maxTokens,
				});
				emitResult(
					pi,
					"kimi-auto-result",
					`[kimi-auto -> ${out.model}]\n\n${out.text}`,
				);
			} catch (err) {
				ctx.ui.notify(`kimi-auto: ${(err as Error).message}`, "error");
			}
		},
	});

	// ---- /kimi-auto-status ------------------------------------------------------

	pi.registerCommand("kimi-auto-status", {
		description:
			"Show the current kimi-auto resolution: model, probe latency, " +
			"resolver freshness, and candidate table.",
		handler: async (_args, ctx) => {
			const s = await refresh(ctx);
			emitResult(pi, "kimi-auto-status", formatStatus(s, Date.now(), STALE_AFTER_MS));
		},
	});

	// ---- /kimi-auto-resolve -----------------------------------------------------

	pi.registerCommand("kimi-auto-resolve", {
		description: "Print just the model id kimi-auto currently resolves to (scripting-friendly).",
		handler: async (_args, ctx) => {
			const s = await refresh(ctx);
			const r = resolveModel(s);
			if ("error" in r) {
				ctx.ui.notify(r.error, "error");
				return;
			}
			emitResult(pi, "kimi-auto-resolve", r.model);
		},
	});

	// ---- kimi_auto_ask tool -----------------------------------------------------

	const askToolDef = {
		name: "kimi_auto_ask",
		label: "Kimi Auto Ask",
		description:
			"Run one prompt through the kimi-auto alias — the best live Kimi " +
			"endpoint, auto-resolved by the 15-minute resolver audit. Use for a " +
			"second model's take via the Kimi family without pinning a model id. " +
			"Parameters: prompt (string, required), maxTokens (integer 1..32000, " +
			"optional), timeoutMs (integer 1000..600000, optional). Fails loudly " +
			"when no Kimi model is healthy.",
		parameters: askParameters,
		async execute(
			_id: string,
			params: { prompt: string; maxTokens?: number; timeoutMs?: number },
			signal: AbortSignal | undefined,
			_onUpdate: unknown,
			ctx: ExtensionContext,
		) {
			const s = await refresh(ctx);
			const r = resolveModel(s);
			if ("error" in r) {
				return {
					content: [{ type: "text" as const, text: r.error }],
					details: { resolved: null },
					isError: true,
				};
			}
			try {
				const out = await chatOnce(params.prompt, {
					herdUrl: state.herdUrl,
					timeoutMs: params.timeoutMs ?? state.timeoutMs,
					maxTokens: params.maxTokens ?? state.maxTokens,
				});
				void signal;
				return {
					content: [
						{
							type: "text" as const,
							text: `[kimi-auto -> ${out.model}]\n\n${truncateOutput(out.text.trim())}`,
						},
					],
					details: { resolved: out.model, usage: out.usage ?? null },
				};
			} catch (err) {
				return {
					content: [{ type: "text" as const, text: (err as Error).message }],
					details: { resolved: r.model },
					isError: true,
				};
			}
		},
	};
	// Cast through `unknown`: the deeply-recursive zod type does not satisfy
	// the registerTool parameter constraint (same as omp-kimi / omp-kafka).
	pi.registerTool(askToolDef as unknown as Parameters<typeof pi.registerTool>[0]);

	// ---- kimi_auto_status tool ---------------------------------------------------

	const statusToolDef = {
		name: "kimi_auto_status",
		label: "Kimi Auto Status",
		description:
			"Show the current kimi-auto resolution: model id, probe latency, " +
			"resolver freshness, and the candidate table from the shared " +
			"resolver state. No parameters.",
		parameters: z.object({}),
		async execute(
			_id: string,
			_params: Record<string, never>,
			_signal: AbortSignal | undefined,
			_onUpdate: unknown,
			ctx: ExtensionContext,
		) {
			const s = await refresh(ctx);
			return {
				content: [{ type: "text" as const, text: formatStatus(s, Date.now(), STALE_AFTER_MS) }],
				details: {
					model: s.model,
					healthy: s.healthy,
					stale: isStale(s, Date.now(), STALE_AFTER_MS),
				},
			};
		},
	};
	pi.registerTool(statusToolDef as unknown as Parameters<typeof pi.registerTool>[0]);
}
