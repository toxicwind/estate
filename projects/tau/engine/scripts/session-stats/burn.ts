#!/usr/bin/env bun
/**
 * Session burn radar — LIVE token-efficiency monitoring over the omp session
 * corpus (~/.omp/agent/sessions/).
 *
 * Unlike scripts/session-stats/audit.ts (post-hoc batch scan), burn.ts tails
 * session transcripts in real time and fires waste-signature alerts while the
 * session is still running, so a human or an autopilot can intervene mid-flight
 * instead of discovering the waste a week later in an audit report.
 *
 * Live waste-signature detectors:
 *   read-loop    — same file read N times inside the window with no intervening
 *                    edit/write to that file (the agent is going in circles)
 *   edit-churn   — N failed edits against the same file inside the window
 *   error-storm  — N consecutive failing tool calls
 *   bloat        — a single tool result above the bloat token threshold
 *   burn-rate    — trailing-window tokens/minute above the burn threshold
 *   cost-budget  — cumulative session cost crosses a budget ladder rung
 *   stalled      — high burn with no progress signals (edits/writes/execs/spawns)
 *   compaction   — context compaction happened (context reset, noteworthy)
 *
 * Usage:
 *   bun run stats:burn                          # watch all active sessions (live)
 *   bun run stats:burn -- --once                # one-shot report over recent sessions
 *   bun run stats:burn -- --once --since 3d --json /tmp/burn.json
 *   bun run stats:burn -- --interval 2s --folder Projects-pi --burn-rate 20000
 *
 * Env:
 *   OMP_SESSIONS_ROOT  override of ~/.omp/agent/sessions (also: --sessions-root)
 *
 * Alert ledger: append-only JSONL at --ledger (default ~/.omp/session-burn-ledger.jsonl).
 * Every firing detector appends one line; `--once` prints summaries to stdout.
 */

import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { parseArgs } from "node:util";

// --------------------------------------------------------------------------
// CLI

export interface BurnCliOptions {
	sessionsRoot: string;
	sinceMs: number;
	intervalMs: number;
	folder?: string;
	once: boolean;
	ledger: string;
	burnRateTokPerMin: number;
	burnWindowMs: number;
	readLoopN: number;
	readLoopWindowMs: number;
	editChurnN: number;
	editChurnWindowMs: number;
	errorStormN: number;
	bloatTokens: number;
	stalledRequests: number;
	quiet: boolean;
}

const DEFAULT_ROOT = path.join(os.homedir(), ".omp", "agent", "sessions");
const DEFAULT_LEDGER = path.join(os.homedir(), ".omp", "session-burn-ledger.jsonl");
const COST_LADDER = [1, 5, 25, 100, 500];

export function parseDuration(raw: string): number {
	const m = /^(\d+)?\s*(s|m|h|d|w)$/.exec(raw.trim());
	if (!m) throw new Error(`invalid duration "${raw}" (use e.g. 30s, 10m, 3h, 1d, 1w)`);
	const n = m[1] ? Number.parseInt(m[1], 10) : 1;
	switch (m[2]) {
		case "s":
			return n * 1000;
		case "m":
			return n * 60 * 1000;
		case "h":
			return n * 3_600_000;
		case "d":
			return n * 24 * 3_600_000;
		default:
			return n * 7 * 24 * 3_600_000;
	}
}

export function parseBurnCli(argv: string[]): BurnCliOptions {
	const { values } = parseArgs({
		args: argv,
		options: {
			"sessions-root": { type: "string" },
			since: { type: "string", default: "1h" },
			interval: { type: "string", default: "5s" },
			folder: { type: "string" },
			once: { type: "boolean", default: false },
			ledger: { type: "string" },
			"burn-rate": { type: "string", default: "30000" },
			"burn-window": { type: "string", default: "10m" },
			"read-loop-n": { type: "string", default: "5" },
			"read-loop-window": { type: "string", default: "15m" },
			"edit-churn-n": { type: "string", default: "3" },
			"edit-churn-window": { type: "string", default: "15m" },
			"error-storm-n": { type: "string", default: "6" },
			bloat: { type: "string", default: "20000" },
			"stalled-requests": { type: "string", default: "8" },
			quiet: { type: "boolean", default: false },
			"no-ledger": { type: "boolean", default: false },
			help: { type: "boolean", default: false },
		},
	});
	if (values.help) {
		console.log(
			`session burn radar — live token-efficiency watch over session transcripts\n\n` +
				`  --once                    one-shot report over recent sessions, then exit\n` +
				`  --since <dur>             sessions touched within dur (default 1h)\n` +
				`  --interval <dur>          watch poll interval (default 5s)\n` +
				`  --sessions-root <dir>     transcript root (default ~/.omp/agent/sessions)\n` +
				`  --folder <substr>         only sessions whose path contains substr\n` +
				`  --ledger <file>           append-only alert ledger (default ~/.omp/session-burn-ledger.jsonl)\n` +
				`  --no-ledger               disable the alert ledger\n` +
				`  --burn-rate <n>           tokens/min firing the burn-rate detector (default 30000)\n` +
				`  --burn-window <dur>       trailing window for burn-rate (default 10m)\n` +
				`  --read-loop-n <n>         reads firing read-loop (default 5)\n` +
				`  --read-loop-window <dur>  read-loop lookback (default 15m)\n` +
				`  --edit-churn-n <n>        failed edits firing edit-churn (default 3)\n` +
				`  --edit-churn-window <dur> edit-churn lookback (default 15m)\n` +
				`  --error-storm-n <n>       consecutive errors firing error-storm (default 6)\n` +
				`  --bloat <n>               result tokens firing bloat (default 20000)\n` +
				`  --stalled-requests <n>    tool-less requests firing stalled (default 8)\n` +
				`  --quiet                   alerts only, no dashboard lines\n`,
		);
		process.exit(0);
	}
	return {
		sessionsRoot: values["sessions-root"] ?? process.env.OMP_SESSIONS_ROOT ?? DEFAULT_ROOT,
		sinceMs: parseDuration(values.since),
		intervalMs: parseDuration(values.interval),
		folder: values.folder,
		once: values.once,
		ledger: values["no-ledger"] ? "" : (values.ledger ?? DEFAULT_LEDGER),
		burnRateTokPerMin: Number.parseInt(values["burn-rate"], 10),
		burnWindowMs: parseDuration(values["burn-window"]),
		readLoopN: Number.parseInt(values["read-loop-n"], 10),
		readLoopWindowMs: parseDuration(values["read-loop-window"]),
		editChurnN: Number.parseInt(values["edit-churn-n"], 10),
		editChurnWindowMs: parseDuration(values["edit-churn-window"]),
		errorStormN: Number.parseInt(values["error-storm-n"], 10),
		bloatTokens: Number.parseInt(values.bloat, 10),
		stalledRequests: Number.parseInt(values["stalled-requests"], 10),
		quiet: values.quiet,
	};
}

// --------------------------------------------------------------------------
// Event model

export type BurnKind =
	| "read-loop"
	| "edit-churn"
	| "error-storm"
	| "bloat"
	| "burn-rate"
	| "cost-budget"
	| "stalled"
	| "compaction";

export interface BurnEvent {
	/** UTC epoch ms of the ledger append. */
	at: number;
	kind: BurnKind;
	severity: "warn" | "critical";
	sessionId: string;
	sessionPath: string;
	/** UTC epoch ms of the transcript event that triggered the detector. */
	ts: number;
	detail: string;
	tokens: number;
}

export interface BurnThresholds {
	burnRateTokPerMin: number;
	burnWindowMs: number;
	readLoopN: number;
	readLoopWindowMs: number;
	editChurnN: number;
	editChurnWindowMs: number;
	errorStormN: number;
	bloatTokens: number;
	stalledRequests: number;
}

function estTokens(text: string): number {
	return Math.ceil(text.length / 4);
}

/** Same normalization contract as audit.ts: keep `scheme://` URLs intact and
 * strip trailing line/raw selectors (`:50-200`, `:raw`, …). */
export function normalizeBurnPath(p: string): string {
	let out = p;
	for (;;) {
		const next = out.replace(/:(?:raw|conflicts|[0-9][0-9+\-,]*)$/i, "");
		if (next === out) return out;
		out = next;
	}
}

function contentText(content: unknown): string {
	if (typeof content === "string") return content;
	if (!Array.isArray(content)) return "";
	let out = "";
	for (const item of content) {
		if (item && typeof item === "object" && (item as { type?: string }).type === "text") {
			out += (item as { text?: string }).text ?? "";
		}
	}
	return out;
}

const PROGRESS_TOOLS = new Set(["edit", "write", "bash", "task"]);

interface PendingCall {
	name: string;
	args: Record<string, unknown> | undefined;
	requestIndex: number;
	ts: number;
}

interface ReadHit {
	path: string;
	ts: number;
}

interface EditHit {
	path: string;
	ts: number;
	failed: boolean;
}

interface UsageSample {
	ts: number;
	tokens: number;
}

// --------------------------------------------------------------------------
// SessionTracker — incremental, per-transcript detector engine

export class SessionTracker {
	readonly id: string;
	readonly filePath: string;
	#thresholds: BurnThresholds;

	#requestCount = 0;
	#cost = 0;
	#tokensTotal = 0;
	#budgetFired = new Set<number>();
	#title?: string;

	#pending = new Map<string, PendingCall>();
	#reads: ReadHit[] = [];
	#edits: EditHit[] = [];
	#readLoopFired = new Set<string>();
	#editChurnFired = new Set<string>();
	#errorStreak = 0;
	#burnRateFired = false;
	#stalledFired = false;
	#noToolRequests = 0;
	#lastProgressRequest = 0;
	#usageWindow: UsageSample[] = [];
	#lastTs = 0;
	#toolCalls = 0;
	#toolErrors = 0;
	#compactions = 0;

	constructor(id: string, filePath: string, thresholds: BurnThresholds) {
		this.id = id;
		this.filePath = filePath;
		this.#thresholds = thresholds;
	}

	get requestCount(): number {
		return this.#requestCount;
	}
	get cost(): number {
		return this.#cost;
	}
	get tokensTotal(): number {
		return this.#tokensTotal;
	}
	get title(): string | undefined {
		return this.#title;
	}
	get lastTs(): number {
		return this.#lastTs;
	}
	get compactionCount(): number {
		return this.#compactions;
	}

	/** Rolling tokens/min over the configured burn window ending at `now`. */
	burnRate(now: number): number {
		const t = this.#thresholds;
		const cut = now - t.burnWindowMs;
		let sum = 0;
		for (const s of this.#usageWindow) if (s.ts >= cut) sum += s.tokens;
		return sum / (t.burnWindowMs / 60000);
	}

	#emit(
		kind: BurnKind,
		severity: BurnEvent["severity"],
		ts: number,
		detail: string,
		tokens: number,
	): BurnEvent {
		return {
			at: Date.now(),
			kind,
			severity,
			sessionId: this.id,
			sessionPath: this.filePath,
			ts,
			detail,
			tokens,
		};
	}

	ingest(line: string): BurnEvent[] {
		const events: BurnEvent[] = [];
		if (!line) return events;
		let entry: Record<string, unknown>;
		try {
			entry = JSON.parse(line);
		} catch {
			return events; // torn tail line from a crashed writer
		}
		const type = entry.type;
		if (type === "session") {
			if (typeof entry.title === "string") this.#title = entry.title;
			return events;
		}
		if (type === "compaction") {
			this.#compactions++;
			const ts = Date.parse((entry.timestamp as string) ?? "") || Date.now();
			this.#lastTs = Math.max(this.#lastTs, ts);
			events.push(this.#emit("compaction", "warn", ts, "context compaction — context reset", 0));
			return events;
		}
		if (type !== "message") return events;
		const msg = entry.message as Record<string, unknown> | undefined;
		if (!msg) return events;
		const ts = typeof msg.timestamp === "number" ? msg.timestamp : Date.now();
		if (ts > 0) this.#lastTs = Math.max(this.#lastTs, ts);
		const t = this.#thresholds;
		const role = msg.role;

		if (role === "assistant") {
			this.#requestCount++;
			const usage = msg.usage as Record<string, unknown> | undefined;
			const toks =
				((usage?.input as number) || 0) +
				((usage?.output as number) || 0) +
				((usage?.cacheRead as number) || 0) +
				((usage?.cacheWrite as number) || 0);
			this.#tokensTotal += toks;
			this.#usageWindow.push({ ts, tokens: toks });
			const cut = ts - t.burnWindowMs;
			while (this.#usageWindow.length > 0 && this.#usageWindow[0].ts < cut) this.#usageWindow.shift();
			// Bound detector histories to the largest lookback any detector needs.
			const readCut = ts - t.readLoopWindowMs;
			while (this.#reads.length > 0 && this.#reads[0].ts < readCut) this.#reads.shift();
			const editCut = ts - Math.max(t.editChurnWindowMs, t.readLoopWindowMs);
			while (this.#edits.length > 0 && this.#edits[0].ts < editCut) this.#edits.shift();
			const costTotal = (usage?.cost as { total?: number } | undefined)?.total || 0;
			this.#cost += costTotal;

			for (const rung of COST_LADDER) {
				if (this.#cost >= rung && !this.#budgetFired.has(rung)) {
					this.#budgetFired.add(rung);
					events.push(
						this.#emit(
							"cost-budget",
							rung >= 25 ? "critical" : "warn",
							ts,
							`session cost crossed $${rung} (now $${this.#cost.toFixed(2)})`,
							0,
						),
					);
				}
			}

			const rate = this.burnRate(ts);
			if (rate >= t.burnRateTokPerMin && !this.#burnRateFired) {
				this.#burnRateFired = true;
				events.push(
					this.#emit(
						"burn-rate",
						"critical",
						ts,
						`burn rate ${Math.round(rate).toLocaleString()} tok/min over trailing ${Math.round(t.burnWindowMs / 60000)}m (threshold ${t.burnRateTokPerMin.toLocaleString()})`,
						Math.round(rate),
					),
				);
			} else if (rate < t.burnRateTokPerMin * 0.7) {
				this.#burnRateFired = false; // re-arm when the session cools down
			}

			const content = Array.isArray(msg.content) ? msg.content : [];
			let hadTool = false;
			for (const block of content) {
				const b = block as Record<string, unknown>;
				if (b.type !== "toolCall") continue;
				hadTool = true;
				const name = (b.name as string) ?? "?";
				const args = b.arguments as Record<string, unknown> | undefined;
				const callId = (b.id as string) ?? "";
				this.#toolCalls++;
				this.#pending.set(callId, { name, args, requestIndex: this.#requestCount, ts });
				if (PROGRESS_TOOLS.has(name)) this.#lastProgressRequest = this.#requestCount;
				if (name === "read") {
					const p = typeof args?.path === "string" ? normalizeBurnPath(args.path as string) : "";
					if (p) {
						this.#reads.push({ path: p, ts });
						const winCut = ts - t.readLoopWindowMs;
						const same = this.#reads.filter(r => r.path === p && r.ts >= winCut);
						const editedSince = this.#edits.some(
							e => e.path === p && !e.failed && e.ts >= winCut && e.ts >= (same[0]?.ts ?? ts),
						);
						if (same.length >= t.readLoopN && !editedSince && !this.#readLoopFired.has(p)) {
							this.#readLoopFired.add(p);
							events.push(
								this.#emit(
									"read-loop",
									"warn",
									ts,
									`read-loop on ${p}: ${same.length} reads in ${Math.round(t.readLoopWindowMs / 60000)}m with no intervening edit`,
									0,
								),
							);
						}
					}
				}
			}

			if (hadTool) {
				this.#noToolRequests = 0;
			} else {
				this.#noToolRequests++;
				if (
					this.#noToolRequests >= t.stalledRequests &&
					!this.#stalledFired &&
					this.#requestCount - this.#lastProgressRequest >= t.stalledRequests
				) {
					this.#stalledFired = true;
					events.push(
						this.#emit(
							"stalled",
							"warn",
							ts,
							`${this.#noToolRequests} consecutive tool-less requests with no progress signal (edit/write/exec/spawn)`,
							0,
						),
					);
				}
			}
			return events;
		}

		if (role === "toolResult") {
			const callId = (msg.toolCallId as string) ?? "";
			const call = this.#pending.get(callId);
			const name = call?.name ?? (msg.toolName as string) ?? "?";
			const textBlob = contentText(msg.content);
			const toks = estTokens(textBlob);
			const failed = msg.isError === true;
			if (failed) {
				this.#toolErrors++;
				this.#errorStreak++;
				if (this.#errorStreak >= t.errorStormN) {
					this.#errorStreak = 0; // re-arm: each storm of N fires once
					events.push(
						this.#emit(
							"error-storm",
							"critical",
							ts,
							`${t.errorStormN} consecutive failing tool calls (latest: ${name})`,
							0,
						),
					);
				}
			} else {
				this.#errorStreak = 0;
			}
			if (toks >= t.bloatTokens) {
				events.push(
					this.#emit(
						"bloat",
						toks >= t.bloatTokens * 5 ? "critical" : "warn",
						ts,
						`${name} result is ${toks.toLocaleString()} tok — will sit in context for the rest of the session`,
						toks,
					),
				);
			}
			if (name === "edit" && call?.args && typeof call.args.path === "string") {
				const p = normalizeBurnPath(call.args.path as string);
				this.#edits.push({ path: p, ts, failed });
				if (failed) {
					const winCut = ts - t.editChurnWindowMs;
					const same = this.#edits.filter(e => e.path === p && e.failed && e.ts >= winCut);
					const key = `${p}`;
					if (same.length >= t.editChurnN && !this.#editChurnFired.has(key)) {
						this.#editChurnFired.add(key);
						events.push(
							this.#emit(
								"edit-churn",
								"warn",
								ts,
								`edit-churn on ${p}: ${same.length} failed edits in ${Math.round(t.editChurnWindowMs / 60000)}m`,
								0,
							),
						);
					}
				} else {
					// A successful edit resets the per-path detector context: the read
					// loop is broken and prior failures no longer count as churn.
					this.#readLoopFired.delete(p);
					this.#editChurnFired.delete(`${p}`);
					this.#reads = this.#reads.filter(r => r.path !== p);
					this.#edits = this.#edits.filter(e => e.path !== p);
					this.#stalledFired = false;
					this.#noToolRequests = 0;
					this.#lastProgressRequest = this.#requestCount;
				}
			}
			if (name === "write" && call?.args && typeof call.args.path === "string") {
				const p = normalizeBurnPath(call.args.path as string);
				this.#edits.push({ path: p, ts, failed: false });
				this.#readLoopFired.delete(p);
				this.#reads = this.#reads.filter(r => r.path !== p);
				this.#stalledFired = false;
				this.#noToolRequests = 0;
				this.#lastProgressRequest = this.#requestCount;
			}
			if (name === "bash" && !failed) {
				this.#stalledFired = false;
				this.#noToolRequests = 0;
				this.#lastProgressRequest = this.#requestCount;
			}
			if (name === "task" && !failed) {
				this.#stalledFired = false;
				this.#noToolRequests = 0;
				this.#lastProgressRequest = this.#requestCount;
			}
			this.#pending.delete(callId);
			return events;
		}

		return events;
	}

	/** One-line dashboard row for this session. */
	dashboardRow(now: number): string {
		const rate = Math.round(this.burnRate(now)).toLocaleString();
		const title = this.#title ? ` ${this.#title.slice(0, 40)}` : "";
		return `${this.id.slice(0, 24).padEnd(24)} req=${String(this.#requestCount).padStart(5)} tok/min=${rate.padStart(9)} cost=$${this.#cost.toFixed(2).padStart(7)} tools=${this.#toolCalls}${title}`;
	}
}

// --------------------------------------------------------------------------
// Driver: incremental file tail + poll loop

interface TailState {
	offset: number;
	mtime: number;
}

async function listSessionFiles(root: string, folder: string | undefined): Promise<string[]> {
	const out: string[] = [];
	const walk = async (dir: string): Promise<void> => {
		let entries;
		try {
			entries = await fs.readdir(dir, { withFileTypes: true });
		} catch {
			return;
		}
		for (const e of entries) {
			const full = path.join(dir, e.name);
			if (e.isDirectory()) await walk(full);
			else if (e.isFile() && e.name.endsWith(".jsonl")) {
				if (!folder || full.includes(folder)) out.push(full);
			}
		}
	};
	await walk(root);
	return out;
}

function sessionIdFor(filePath: string): string {
	return path.basename(filePath, ".jsonl");
}

/** Tail newly appended lines from every known file; discover new files. */
async function pollOnce(
	opts: BurnCliOptions,
	thresholds: BurnThresholds,
	trackers: Map<string, SessionTracker>,
	tails: Map<string, TailState>,
	sinceCut: number,
	onEvents: (events: BurnEvent[]) => void | Promise<void>,
): Promise<void> {
	const files = await listSessionFiles(opts.sessionsRoot, opts.folder);
	for (const f of files) {
		let st;
		try {
			st = await fs.stat(f);
		} catch {
			continue;
		}
		if (st.mtimeMs < sinceCut && !trackers.has(f)) continue;
		let tracker = trackers.get(f);
		if (!tracker) {
			tracker = new SessionTracker(sessionIdFor(f), f, thresholds);
			trackers.set(f, tracker);
			tails.set(f, { offset: 0, mtime: 0 });
		}
		const tail = tails.get(f)!;
		if (st.size < tail.offset) tail.offset = 0; // file rotated/truncated
		if (st.size === tail.offset && st.mtimeMs <= tail.mtime) continue;
		const fh = await fs.open(f, "r");
		try {
			const buf = Buffer.alloc(st.size - tail.offset);
			await fh.read(buf, 0, buf.length, tail.offset);
			tail.offset = st.size;
			tail.mtime = st.mtimeMs;
			const text = buf.toString("utf8");
			for (const line of text.split("\n")) {
				if (!line) continue;
				const events = tracker.ingest(line);
				if (events.length > 0) await onEvents(events);
			}
		} finally {
			await fh.close();
		}
	}
}

export async function appendLedger(ledgerPath: string, events: BurnEvent[]): Promise<void> {
	if (!ledgerPath || events.length === 0) return;
	const lines = events.map(e => JSON.stringify(e)).join("\n") + "\n";
	await fs.appendFile(ledgerPath, lines, "utf8");
}

export function formatEvent(e: BurnEvent): string {
	const sev = e.severity === "critical" ? "🔥" : "⚠️";
	const when = new Date(e.ts).toISOString();
	return `${sev} [${e.kind}] ${e.sessionId}${e.detail ? ` — ${e.detail}` : ""} (${when})`;
}

// --------------------------------------------------------------------------
// main

async function main(): Promise<void> {
	const opts = parseBurnCli(process.argv.slice(2));
	const thresholds: BurnThresholds = {
		burnRateTokPerMin: opts.burnRateTokPerMin,
		burnWindowMs: opts.burnWindowMs,
		readLoopN: opts.readLoopN,
		readLoopWindowMs: opts.readLoopWindowMs,
		editChurnN: opts.editChurnN,
		editChurnWindowMs: opts.editChurnWindowMs,
		errorStormN: opts.errorStormN,
		bloatTokens: opts.bloatTokens,
		stalledRequests: opts.stalledRequests,
	};
	const trackers = new Map<string, SessionTracker>();
	const tails = new Map<string, TailState>();
	const sinceCut = Date.now() - opts.sinceMs;
	const seen = new Set<string>();

	const onEvents = async (events: BurnEvent[]): Promise<void> => {
		for (const e of events) {
			const key = `${e.sessionId}:${e.kind}:${e.ts}:${e.detail}`;
			if (seen.has(key)) continue;
			seen.add(key);
			console.log(formatEvent(e));
		}
		await appendLedger(opts.ledger, events).catch(err => {
			console.error(`ledger append failed: ${(err as Error).message}`);
		});
	};

	if (opts.once) {
		await pollOnce(opts, thresholds, trackers, tails, sinceCut, onEvents);
		const now = Date.now();
		console.log(`\n=== burn radar report (${trackers.size} sessions, since ${new Date(sinceCut).toISOString()}) ===`);
		const rows = [...trackers.values()]
			.map(t => ({ t, rate: t.burnRate(now) }))
			.sort((a, b) => b.rate - a.rate);
		for (const { t } of rows) console.log(t.dashboardRow(now));
		return;
	}

	if (!opts.quiet) console.log(`burn radar watching ${opts.sessionsRoot} every ${opts.intervalMs}ms`);
	for (;;) {
		await pollOnce(opts, thresholds, trackers, tails, sinceCut, onEvents);
		if (!opts.quiet) {
			const now = Date.now();
			const rows = [...trackers.values()]
				.map(t => ({ t, rate: t.burnRate(now) }))
				.sort((a, b) => b.rate - a.rate)
				.slice(0, 10);
			console.log(`\n--- ${new Date(now).toISOString()} (${trackers.size} sessions) ---`);
			for (const { t } of rows) console.log(t.dashboardRow(now));
		}
		await Bun.sleep(opts.intervalMs);
	}
}

if (import.meta.main) {
	await main();
}
