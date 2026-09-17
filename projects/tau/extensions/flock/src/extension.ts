/**
 * tau-flock extension entry point.
 *
 * Makes flock (the NVIDIA NIM OpenAI-compatible proxy on 127.0.0.1:8000)
 * first-class inside Tau sessions:
 *
 *   /flock-status             daemon health + config (base URL, key present?)
 *   /flock-models              list models served by the proxy
 *   /flock-chat <prompt> [--model <id>] [--system <text>]
 *                             send a chat completion through flock
 *
 *   flock_status / flock_models / flock_chat (tools) — LLM-callable
 *   equivalents, so the agent reaches for flock instead of shelling
 *   out to curl for NIM completions.
 *
 * Configuration (environment):
 *   FLOCK_BASE_URL   Proxy base URL (default http://127.0.0.1:8000).
 *   FLOCK_API_KEY    Proxy client key (Bearer). Optional; falls back to
 *                    NVIDIA_API_KEY, then NIM_PROXY_API_KEY. Required for
 *                    /v1/models and /v1/chat/completions.
 *   FLOCK_TIMEOUT_MS Per-request timeout (default 60000, clamp 1000..600000).
 *   FLOCK_DISABLED=1 Skip the extension entirely.
 */

import type { ExtensionAPI, ExtensionContext } from "@oh-my-pi/pi-coding-agent";
import { z } from "zod/v4";
import {
	DEFAULT_BASE_URL,
	FlockError,
	flockChat,
	flockHealth,
	flockModels,
	resolveApiKey,
	resolveConfig,
	type EnvLike,
	type FlockModel,
} from "./flock.ts";

const DEBUG = (process.env as EnvLike).FLOCK_DEBUG === "1";
const DISABLED = (process.env as EnvLike).FLOCK_DISABLED === "1";

const STATUS_KEY = "flock";

function debug(...args: unknown[]): void {
	if (DEBUG) {
		// eslint-disable-next-line no-console
		console.error("[tau-flock]", ...args);
	}
}

function emitResult(
	pi: ExtensionAPI,
	customType: string,
	stdout: string,
	stderr: string,
): void {
	const parts = [stdout.trim()];
	const errText = stderr.trim();
	if (errText !== "") {
		parts.push("--- stderr ---");
		parts.push(errText);
	}
	pi.sendMessage({
		customType,
		content: parts.join("\n\n"),
		// @ts-expect-error runtime accepts extra fields
		detail: { customType },
	});
}

function flockErrorEnvelope(err: unknown): {
	content: [{ type: "text"; text: string }];
	details: { httpStatus: number | null; timedOut: boolean };
	isError: true;
} {
	const e = err as FlockError;
	const timedOut = e instanceof FlockError && e.kind === "timeout";
	return {
		content: [
			{
				type: "text" as const,
				text: `flock error [${e instanceof FlockError ? e.kind : "unknown"}]: ${e.message ?? String(err)}`,
			},
		],
		details: {
			httpStatus:
				e instanceof FlockError && typeof e.status === "number"
					? e.status
					: null,
			timedOut,
		},
		isError: true,
	};
}

function resultEnvelope(text: string, httpStatus: number | null = null): {
	content: [{ type: "text"; text: string }];
	details: { httpStatus: number | null; timedOut: boolean };
} {
	return {
		content: [{ type: "text" as const, text }],
		details: { httpStatus, timedOut: false },
	};
}

/**
 * Minimal argv tokenizer for slash-command input: honours double quotes,
 * no glob expansion, no backticks (never executed by a shell anyway).
 * (Same shape as tau-ffs.)
 */
function tokenizeArgs(input: string): string[] {
	const out: string[] = [];
	let cur = "";
	let inQuotes = false;
	for (let i = 0; i < input.length; i++) {
		const ch = input[i] as string;
		if (ch === '"' && (i === 0 || input[i - 1] !== "\\")) {
			inQuotes = !inQuotes;
			continue;
		}
		if (!inQuotes && /\s/.test(ch)) {
			if (cur !== "") {
				out.push(cur);
				cur = "";
			}
			continue;
		}
		cur += ch;
	}
	if (cur !== "") out.push(cur);
	return out;
}

/** Extract `--model <id>` / `--system <text>` flags; returns [flags, rest]. */
function splitFlags(tokens: string[]): [
	{ model?: string; system?: string },
	string[],
] {
	const flags: { model?: string; system?: string } = {};
	const rest: string[] = [];
	for (let i = 0; i < tokens.length; i++) {
		const tok = tokens[i] as string;
		if ((tok === "--model" || tok === "--system") && i + 1 < tokens.length) {
			const key = tok === "--model" ? "model" : "system";
			flags[key] = tokens[++i] as string;
			continue;
		}
		if (tok.startsWith("--model=")) {
			flags.model = tok.slice("--model=".length);
			continue;
		}
		if (tok.startsWith("--system=")) {
			flags.system = tok.slice("--system=".length);
			continue;
		}
		rest.push(tok);
	}
	return [flags, rest];
}

function formatModels(models: FlockModel[]): string {
	const lines = [`${models.length} models:`];
	for (const m of models.slice(0, 200)) {
		const extra = m.owned_by ? ` (by ${m.owned_by})` : "";
		lines.push(`- ${m.id}${extra}`);
	}
	if (models.length > 200) {
		lines.push(`… and ${models.length - 200} more (refine via flock_chat)`);
	}
	return lines.join("\n");
}

export default function flockExtension(pi: ExtensionAPI): void {
	pi.setLabel("flock");
	const env = process.env as EnvLike;

	const refreshStatus = (ctx: ExtensionContext, note: string): void => {
		ctx.ui.setStatus(STATUS_KEY, `flock: ${note}`);
	};

	// ---- Lifecycle ------------------------------------------------------

	pi.on("session_start", async (_event, ctx) => {
		if (DISABLED) {
			ctx.ui.notify("flock: FLOCK_DISABLED=1, extension inactive", "info");
			return;
		}
		try {
			const h = await flockHealth(env);
			const note = h.ok ? "ok" : `unexpected health body: ${h.body}`;
			refreshStatus(ctx, note);
			debug("health probe:", note);
		} catch (err) {
			const msg = (err as Error).message;
			refreshStatus(ctx, `down (${msg})`);
			ctx.ui.notify(`flock: daemon unreachable: ${msg}`, "warning");
		}
	});

	// ---- /flock-status ---------------------------------------------------

	pi.registerCommand("flock-status", {
		description: "Show flock daemon health and client configuration.",
		handler: async (_args, ctx) => {
			const cfg = resolveConfig(env);
			const lines = [
				`base_url: ${cfg.baseUrl}`,
				`api_key: ${cfg.apiKey ? "present" : "absent (set FLOCK_API_KEY)"}`,
				`timeout: ${cfg.timeoutMs}ms (FLOCK_TIMEOUT_MS)`,
			];
			try {
				const h = await flockHealth(env);
				lines.push(`health: ${h.ok ? "ok" : `UNEXPECTED: ${h.body}`}`);
				refreshStatus(ctx, h.ok ? "ok" : "unhealthy");
			} catch (err) {
				lines.push(`health: FAILED — ${(err as Error).message}`);
				refreshStatus(ctx, "down");
			}
			emitResult(pi, "flock-status", lines.join("\n"), "");
		},
	});

	// ---- /flock-models ---------------------------------------------------

	pi.registerCommand("flock-models", {
		description: "List models served by the flock proxy (requires API key).",
		handler: async (_args, ctx) => {
			if (!resolveApiKey(env)) {
				ctx.ui.notify(
					"flock: no proxy API key — set FLOCK_API_KEY (or NVIDIA_API_KEY / NIM_PROXY_API_KEY)",
					"warning",
				);
			}
			try {
				const models = await flockModels(env);
				emitResult(pi, "flock-models", formatModels(models), "");
			} catch (err) {
				ctx.ui.notify(`flock: ${(err as Error).message}`, "error");
			}
		},
	});

	// ---- /flock-chat -----------------------------------------------------

	pi.registerCommand("flock-chat", {
		description:
			"Send a chat completion through flock. Usage: /flock-chat <prompt> [--model <id>] [--system <text>]",
		handler: async (args, ctx) => {
			const tokens = tokenizeArgs(args ?? "");
			const [flags, rest] = splitFlags(tokens);
			const prompt = rest.join(" ").trim();
			if (!prompt) {
				ctx.ui.notify(
					"usage: /flock-chat <prompt> [--model <id>] [--system <text>]",
					"warning",
				);
				return;
			}
			ctx.ui.notify(
				`flock chat: ${flags.model ?? "(default model)"} — sending…`,
				"info",
			);
			try {
				const r = await flockChat(prompt, {
					model: flags.model,
					system: flags.system,
					env,
				});
				const header = [
					`model: ${r.model}`,
					`finish_reason: ${r.finishReason ?? "n/a"}`,
					r.totalTokens !== undefined ? `tokens: ${r.totalTokens}` : null,
				]
					.filter(Boolean)
					.join(" | ");
				emitResult(pi, "flock-chat", `${header}\n\n${r.content}`, "");
			} catch (err) {
				ctx.ui.notify(`flock: ${(err as Error).message}`, "error");
			}
		},
	});

	// ---- LLM tools -------------------------------------------------------

	type ToolExecute = (
		_id: string,
		params: Record<string, unknown>,
		signal: AbortSignal | undefined,
		_onUpdate: unknown,
		ctx: ExtensionContext,
	) => Promise<unknown>;

	const tool = (
		name: string,
		label: string,
		description: string,
		parameters: z.ZodTypeAny,
		execute: ToolExecute,
	): void => {
		const toolDef = { name, label, description, parameters, execute };
		pi.registerTool(toolDef as unknown as Parameters<typeof pi.registerTool>[0]);
	};

	tool(
		"flock_status",
		"flock status",
		"Check flock daemon health (GET /health) and report client config (base URL, key present/absent, timeout). No parameters.",
		z.object({}),
		async (_id, _params, _signal, _onUpdate, ctx) => {
			const cfg = resolveConfig(env);
			const lines = [
				`base_url: ${cfg.baseUrl}`,
				`api_key: ${cfg.apiKey ? "present" : "absent (set FLOCK_API_KEY)"}`,
				`timeout: ${cfg.timeoutMs}ms`,
			];
			try {
				const h = await flockHealth(env);
				lines.push(`health: ${h.ok ? "ok" : `UNEXPECTED: ${h.body}`}`);
				refreshStatus(ctx, h.ok ? "ok" : "unhealthy");
				return resultEnvelope(lines.join("\n"), 200);
			} catch (err) {
				refreshStatus(ctx, "down");
				return flockErrorEnvelope(err);
			}
		},
	);

	tool(
		"flock_models",
		"flock models",
		"List models served by the flock proxy (GET /v1/models). Requires FLOCK_API_KEY (or NVIDIA_API_KEY / NIM_PROXY_API_KEY). No parameters.",
		z.object({}),
		async (_id, _params, _signal, _onUpdate, _ctx) => {
			try {
				const models = await flockModels(env);
				return resultEnvelope(formatModels(models), 200);
			} catch (err) {
				return flockErrorEnvelope(err);
			}
		},
	);

	tool(
		"flock_chat",
		"flock chat",
		"Send a chat completion through the flock NVIDIA NIM proxy. Requires FLOCK_API_KEY. The proxy rejects empty completions — this tool surfaces that as an error instead of a blank result. Params: prompt (string, required), model (string, optional), system (string, optional system prompt), temperature (number, optional), max_tokens (int, optional).",
		z.object({
			prompt: z.string(),
			model: z.string().optional().describe("Model id; see flock_models."),
			system: z.string().optional(),
			temperature: z.number().min(0).max(2).optional(),
			max_tokens: z.number().int().positive().optional(),
		}),
		async (_id, params, signal, _onUpdate, _ctx) => {
			try {
				const r = await flockChat(params.prompt as string, {
					model: params.model as string | undefined,
					system: params.system as string | undefined,
					temperature: params.temperature as number | undefined,
					maxTokens: params.max_tokens as number | undefined,
					signal: signal ?? undefined,
					env,
				});
				const header = [
					`model: ${r.model}`,
					`finish_reason: ${r.finishReason ?? "n/a"}`,
					r.totalTokens !== undefined ? `tokens: ${r.totalTokens}` : null,
				]
					.filter(Boolean)
					.join(" | ");
				return resultEnvelope(`${header}\n\n${r.content}`, 200);
			} catch (err) {
				return flockErrorEnvelope(err);
			}
		},
	);

	debug(`flock extension loaded; base=${DEFAULT_BASE_URL}`);
}
