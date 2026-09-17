/**
 * ffs binary resolution + process runner.
 * Mirrors the omp-kimi runner shape: spawn, enforce timeout, never swallow errors.
 */

export type EnvLike = Record<string, string | undefined>;

export const INSTALL_HINT =
	"ffs (fast_file_search) not found. Install: cargo install --git https://github.com/quangdang46/fast_file_search (or place the binary at ~/bin/ffs).";

export const STATUS_KEY = "ffs";

export interface FfsRunResult {
	stdout: string;
	stderr: string;
	exitCode: number;
	timedOut: boolean;
}

/** Candidate binary locations, first hit wins. */
export function binaryCandidates(env: EnvLike, home: string): string[] {
	const out: string[] = [];
	if (env.FFS_BINARY) out.push(env.FFS_BINARY);
	out.push("ffs");
	if (home) {
		out.push(`${home}/bin/ffs`);
		out.push(`${home}/.local/bin/ffs`);
	}
	return out;
}

function isExecutable(path: string): boolean {
	try {
		if (path.includes("/")) {
			const f = Bun.file(path);
			return f.size >= 0;
		}
		return Bun.which(path) !== null;
	} catch {
		return false;
	}
}

export function pickBinary(candidates: string[]): string | null {
	for (const c of candidates) {
		if (isExecutable(c)) return c.includes("/") ? c : (Bun.which(c) ?? c);
	}
	return null;
}

export function parseVersion(output: string): string | null {
	const m = output.match(/(\d+\.\d+\.\d+)/);
	return m ? (m[1] ?? null) : null;
}

export function resolveTimeoutMs(env: EnvLike): number {
	const raw = Number(env.FFS_TIMEOUT_MS ?? "");
	if (Number.isFinite(raw) && raw >= 1_000 && raw <= 600_000) return raw;
	return 60_000;
}

const MAX_OUTPUT = 60_000;

export function truncateOutput(s: string): string {
	if (s.length <= MAX_OUTPUT) return s;
	return (
		s.slice(0, MAX_OUTPUT) +
		`\n… [truncated ${s.length - MAX_OUTPUT} chars; refine the query]`
	);
}

export interface RunOpts {
	cwd: string;
	env?: Record<string, string | undefined>;
	timeoutMs: number;
	signal?: AbortSignal;
}

/** Spawn ffs, enforce timeout, collect output. Throws on spawn failure. */
export async function runFfs(
	binary: string,
	args: string[],
	opts: RunOpts,
): Promise<FfsRunResult> {
	const proc = Bun.spawn([binary, ...args], {
		cwd: opts.cwd,
		env: { ...process.env, ...(opts.env ?? {}) } as Record<string, string>,
		stdout: "pipe",
		stderr: "pipe",
	});

	let timedOut = false;
	const timer = setTimeout(() => {
		timedOut = true;
		try {
			proc.kill();
		} catch {
			/* already gone */
		}
	}, opts.timeoutMs);
	if (opts.signal) {
		opts.signal.addEventListener(
			"abort",
			() => {
				try {
					proc.kill();
				} catch {
					/* already gone */
				}
			},
			{ once: true },
		);
	}

	const [stdout, stderr, exitCode] = await Promise.all([
		new Response(proc.stdout as ReadableStream<Uint8Array>).text(),
		new Response(proc.stderr as ReadableStream<Uint8Array>).text(),
		proc.exited,
	]);
	clearTimeout(timer);
	return { stdout, stderr, exitCode, timedOut };
}

/**
 * Minimal argv tokenizer for slash-command input: honours double quotes,
 * no glob expansion, no backticks (never executed by a shell anyway).
 */
export function tokenizeArgs(input: string): string[] {
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

/** Split `--root <dir>` out of a token list; returns [root, rest]. */
export function splitRoot(tokens: string[]): [string | null, string[]] {
	const rest: string[] = [];
	let root: string | null = null;
	for (let i = 0; i < tokens.length; i++) {
		const tok = tokens[i] as string;
		if (tok === "--root" && i + 1 < tokens.length) {
			root = tokens[++i] as string;
			continue;
		}
		if (tok.startsWith("--root=")) {
			root = tok.slice("--root=".length);
			continue;
		}
		rest.push(tok);
	}
	return [root, rest];
}

/** Build the argv prefix: [--root <dir>] <subcommand>. */
export function argvFor(
	subcommand: string,
	root: string | null,
	rest: string[],
): string[] {
	const argv: string[] = [];
	if (root) argv.push("--root", root);
	argv.push(subcommand, ...rest);
	return argv;
}
