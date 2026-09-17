/**
 * tau-ffs extension entry point.
 *
 * Makes fast_file_search (ffs) first-class inside Tau sessions:
 *
 *   /ffs-status              binary location + version
 *   /ffs-find <pat> [--root <dir>]     find files by name (replaces find/fd)
 *   /ffs-grep <pat> [--root <dir>]     search contents (replaces grep/rg)
 *   /ffs-read <file> [--budget N] [--full] [--root <dir>]   token-budget read (replaces cat)
 *   /ffs-outline <file>      structural outline (tree-sitter)
 *   /ffs-symbol <name>       symbol definition lookup
 *   /ffs-refs <name>         definitions + usages in one shot
 *   /ffs-map [--root <dir>]  workspace tree w/ file counts + tokens
 *   /ffs-index [--root <dir>] rebuild on-disk indexes
 *
 *   ffs_find / ffs_grep / ffs_read / ffs_outline / ffs_symbol / ffs_refs /
 *   ffs_impact (tools) — LLM-callable equivalents, so the agent reaches for
 *   ffs instead of shelling out to fd/rg/grep/glob/cat.
 *
 * Configuration (environment):
 *   FFS_BINARY     Explicit path to the ffs binary (default: PATH, ~/bin/ffs,
 *                  ~/.local/bin/ffs).
 *   FFS_TIMEOUT_MS Per-run timeout (default 60000, clamp 1000..600000).
 *   FFS_DISABLED=1 Skip the extension entirely.
 */

import type { ExtensionAPI, ExtensionContext } from "@oh-my-pi/pi-coding-agent";
import { z } from "zod/v4";
import {
	INSTALL_HINT,
	STATUS_KEY,
	argvFor,
	binaryCandidates,
	parseVersion,
	pickBinary,
	resolveTimeoutMs,
	runFfs,
	splitRoot,
	tokenizeArgs,
	truncateOutput,
	type EnvLike,
	type FfsRunResult,
} from "./ffs.ts";

const DEBUG = (process.env as EnvLike).FFS_DEBUG === "1";
const DISABLED = (process.env as EnvLike).FFS_DISABLED === "1";

function debug(...args: unknown[]): void {
	if (DEBUG) {
		// eslint-disable-next-line no-console
		console.error("[tau-ffs]", ...args);
	}
}

interface FfsState {
	binary: string | null;
	version: string | null;
}

function emitResult(
	pi: ExtensionAPI,
	customType: string,
	stdout: string,
	stderr: string,
): void {
	const parts = [truncateOutput(stdout.trim())];
	const errText = stderr.trim();
	if (errText !== "") {
		parts.push("--- stderr ---");
		parts.push(truncateOutput(errText));
	}
	pi.sendMessage({
		customType,
		content: parts.join("\n\n"),
		// @ts-expect-error runtime accepts extra fields
		detail: { customType },
	});
}

function resultEnvelope(r: FfsRunResult): {
	content: [{ type: "text"; text: string }];
	details: { exitCode: number; timedOut: boolean };
	isError?: boolean;
} {
	const text = truncateOutput(r.stdout.trim());
	if (r.timedOut || r.exitCode !== 0) {
		const err = truncateOutput(r.stderr.trim() || r.stdout.trim());
		return {
			content: [
				{
					type: "text" as const,
					text:
						`ffs ${r.timedOut ? "timed out" : `exited with code ${r.exitCode}`}\n` +
						err,
				},
			],
			details: { exitCode: r.exitCode, timedOut: r.timedOut },
			isError: true,
		};
	}
	return {
		content: [{ type: "text" as const, text }],
		details: { exitCode: 0, timedOut: false },
	};
}

export default function ffsExtension(pi: ExtensionAPI): void {
	pi.setLabel("ffs");
	const env = process.env as EnvLike;
	const state: FfsState = { binary: null, version: null };

	const detectBinary = (): void => {
		const home = env.HOME ?? env.USERPROFILE ?? "";
		state.binary = pickBinary(binaryCandidates(env, home));
		debug("binary picked:", state.binary);
	};

	const requireBinary = (): string => {
		if (!state.binary) {
			detectBinary();
			if (!state.binary) throw new Error(`ffs: ${INSTALL_HINT}`);
		}
		return state.binary;
	};

	const refreshStatus = (ctx: ExtensionContext): void => {
		ctx.ui.setStatus(
			STATUS_KEY,
			state.binary
				? `ffs: ${state.version ?? "unknown version"}`
				: "ffs: not installed",
		);
	};

	// ---- Lifecycle ------------------------------------------------------

	pi.on("session_start", async (_event, ctx) => {
		if (DISABLED) {
			ctx.ui.notify("ffs: FFS_DISABLED=1, extension inactive", "info");
			return;
		}
		detectBinary();
		if (state.binary) {
			try {
				const r = await runFfs(state.binary, ["--version"], {
					cwd: ctx.cwd,
					timeoutMs: 10_000,
				});
				state.version = parseVersion(r.stdout + r.stderr);
			} catch (err) {
				debug("version probe failed:", err);
			}
		} else {
			ctx.ui.notify(`ffs: ${INSTALL_HINT}`, "warning");
		}
		refreshStatus(ctx);
	});

	// ---- Shared command runner ------------------------------------------

	const runCommand = async (
		subcommand: string,
		rawArgs: string,
		ctx: ExtensionContext,
		customType: string,
		joinRest = false,
	): Promise<void> => {
		let binary: string;
		try {
			binary = requireBinary();
		} catch (err) {
			ctx.ui.notify((err as Error).message, "error");
			return;
		}
		const tokens = tokenizeArgs(rawArgs ?? "");
		const [root, rest] = splitRoot(tokens);
		if (subcommand !== "map" && subcommand !== "index" && rest.length === 0) {
			ctx.ui.notify(
				`usage: /ffs-${subcommand} <args> [--root <dir>]`,
				"warning",
			);
			return;
		}
		ctx.ui.notify(`ffs ${subcommand}: running…`, "info");
		try {
			const finalRest = joinRest ? [rest.join(" ")] : rest;
			const r = await runFfs(binary, argvFor(subcommand, root, finalRest), {
				cwd: ctx.cwd,
				timeoutMs: resolveTimeoutMs(env),
			});
			emitResult(pi, customType, r.stdout, r.stderr);
		} catch (err) {
			ctx.ui.notify(`ffs: ${(err as Error).message}`, "error");
		}
	};

	// ---- /ffs-status -----------------------------------------------------

	pi.registerCommand("ffs-status", {
		description: "Show ffs binary location and version.",
		handler: async (_args, ctx) => {
			const lines = [
				`binary: ${state.binary ?? "(not found)"}`,
				`version: ${state.version ?? "(unknown)"}`,
				`timeout: ${resolveTimeoutMs(env)}ms (FFS_TIMEOUT_MS)`,
			];
			if (!state.binary) lines.push("", INSTALL_HINT);
			emitResult(pi, "ffs-status", lines.join("\n"), "");
			refreshStatus(ctx);
		},
	});

	// ---- Finder commands -------------------------------------------------

	const COMMANDS: Array<[string, string, string, boolean?]> = [
		["ffs-find", "find", "Find files by name (replaces find/fd)."],
		["ffs-grep", "grep", "Search file contents (replaces grep/rg).", true],
		["ffs-read", "read", "Read a file, token-budget aware (replaces cat)."],
		["ffs-outline", "outline", "Structural outline of a file (tree-sitter)."],
		["ffs-symbol", "symbol", "Look up symbol definitions (tree-sitter AST)."],
		["ffs-refs", "refs", "Definitions + usages of a symbol in one shot."],
		["ffs-map", "map", "Workspace tree annotated with file counts/tokens."],
		["ffs-index", "index", "Build/refresh ffs on-disk indexes."],
	];
	for (const [name, sub, description, join] of COMMANDS) {
		pi.registerCommand(name, {
			description: `${description} Flags: --root <dir>.`,
			handler: async (args, ctx) => {
				await runCommand(sub, args, ctx, name, join ?? false);
			},
		});
	}

	// ---- LLM tools -------------------------------------------------------

	const rootField = z
		.string()
		.optional()
		.describe("Workspace root; defaults to the session cwd.");

	const tool = (
		name: string,
		label: string,
		description: string,
		parameters: z.ZodTypeAny,
		subcommand: string,
		buildArgs: (params: Record<string, unknown>) => string[],
	) => {
		const toolDef = {
			name,
			label,
			description,
			parameters,
			async execute(
				_id: string,
				params: Record<string, unknown>,
				signal: AbortSignal | undefined,
				_onUpdate: unknown,
				ctx: ExtensionContext,
			) {
				const binary = state.binary ?? pickBinary(binaryCandidates(env, env.HOME ?? ""));
				if (!binary) {
					return {
						content: [{ type: "text" as const, text: `ffs: ${INSTALL_HINT}` }],
						details: { exitCode: 127, timedOut: false },
						isError: true,
					};
				}
				state.binary = binary;
				const root = (params.root as string | undefined) ?? null;
				const r = await runFfs(
					binary,
					argvFor(subcommand, root, buildArgs(params)),
					{ cwd: ctx.cwd, timeoutMs: resolveTimeoutMs(env), signal },
				);
				return resultEnvelope(r);
			},
		};
		pi.registerTool(toolDef as unknown as Parameters<typeof pi.registerTool>[0]);
	};

	tool(
		"ffs_find",
		"ffs find",
		"Find files by name with ffs (replaces find/fd/glob). Params: pattern (string, required), root (string, optional).",
		z.object({ pattern: z.string(), root: rootField }),
		"find",
		(p) => [p.pattern as string],
	);

	tool(
		"ffs_grep",
		"ffs grep",
		"Search file contents with ffs (replaces grep/rg). Params: pattern (string, required), root (string, optional).",
		z.object({ pattern: z.string(), root: rootField }),
		"grep",
		(p) => [p.pattern as string],
	);

	tool(
		"ffs_read",
		"ffs read",
		"Read a file with token-budget aware truncation (replaces cat). Params: file (string, required), budget (int, optional token budget), full (bool, optional whole-file raw mode), root (string, optional).",
		z.object({
			file: z.string(),
			budget: z.number().int().optional(),
			full: z.boolean().optional(),
			root: rootField,
		}),
		"read",
		(p) => {
			const a = [p.file as string];
			if (p.budget !== undefined) a.push("--budget", String(p.budget));
			if (p.full) a.push("--full");
			return a;
		},
	);

	tool(
		"ffs_outline",
		"ffs outline",
		"Render a file's structural outline — functions, classes, etc. (tree-sitter). Params: file (string, required), root (string, optional).",
		z.object({ file: z.string(), root: rootField }),
		"outline",
		(p) => [p.file as string],
	);

	tool(
		"ffs_symbol",
		"ffs symbol",
		"Look up symbol definitions via tree-sitter AST. Params: name (string, required), expand (bool, optional inline bodies + callees), root (string, optional).",
		z.object({
			name: z.string(),
			expand: z.boolean().optional(),
			root: rootField,
		}),
		"symbol",
		(p) => {
			const a = [p.name as string];
			if (p.expand) a.push("--expand");
			return a;
		},
	);

	tool(
		"ffs_refs",
		"ffs refs",
		"List definitions and usages of a symbol in one shot. Params: name (string, required), root (string, optional).",
		z.object({ name: z.string(), root: rootField }),
		"refs",
		(p) => [p.name as string],
	);

	tool(
		"ffs_impact",
		"ffs impact",
		"Rank files by how much they'd be affected if a symbol changed. Params: symbol (string, required), root (string, optional).",
		z.object({ symbol: z.string(), root: rootField }),
		"impact",
		(p) => [p.symbol as string],
	);
}
