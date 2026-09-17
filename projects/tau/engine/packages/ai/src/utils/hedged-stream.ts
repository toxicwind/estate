/**
 * Hedged (redundant) streaming for provider requests.
 *
 * HFT-inspired fail-fast policy: when the leading attempt stalls — no stream
 * events for `hedgeStallMs` (default 5s) — or when no completion arrives
 * within `hedgeAfterMs`, a duplicate of the SAME request (same model, same
 * provider, same route, same body) is fired in parallel. The first completion
 * wins; losers are aborted. In-flight duplicates are capped (`maxInFlight`,
 * default 2) and total attempts per stream are bounded (`maxAttempts`).
 *
 * A duplicate can only take over before the leader commits replay-unsafe
 * output (text / tool calls / images). Thinking/reasoning deltas do NOT
 * commit the hedge: they stream live from the leader, while duplicates buffer
 * their pre-commit events. On promotion the winner's buffer is flushed first
 * so text is never lost; thinking may appear twice across a switch, which
 * matches what sequential retries already do today.
 *
 * Same-model, same-route only: this layer never falls back to another model
 * or switches providers. Backoff retries stay in the session turn-recovery
 * layer; instant pre-commit re-issues stay in withReplaySafeStreamRetry.
 */
import { scheduler } from "node:timers/promises";
import { $env, logger } from "@oh-my-pi/pi-utils";
import type { AssistantMessageEvent } from "../types";
import { AssistantMessageEventStream } from "./event-stream";

/** Tuning knobs for the hedged-stream policy. All have safe defaults. */
export interface HedgePolicy {
	/** Master switch. `PI_STREAM_HEDGE_ENABLED=0` disables hedging entirely. */
	enabled: boolean;
	/** Max concurrent attempts for one stream. `PI_STREAM_HEDGE_MAX_INFLIGHT` (default 2). */
	maxInFlight: number;
	/** Max total attempts per stream (leader + hedges). `PI_STREAM_HEDGE_MAX_ATTEMPTS` (default 4). */
	maxAttempts: number;
	/** Fire a duplicate after this long without leader events (pre-commit only). `PI_STREAM_HEDGE_STALL_MS` (default 5000). */
	stallMs: number;
	/** Fire a duplicate after this long without completion (pre-commit only). `PI_STREAM_HEDGE_AFTER_MS` (default 30000, 0 disables). */
	hedgeAfterMs: number;
}

function parseNonNegativeInt(raw: string | undefined, fallback: number): number {
	if (raw === undefined || raw.trim() === "") return fallback;
	const n = Number(raw);
	return Number.isFinite(n) && n >= 0 ? Math.floor(n) : fallback;
}

/** Resolve the hedged-stream policy from the environment. */
export function resolveHedgePolicy(): HedgePolicy {
	return {
		enabled: ($env.PI_STREAM_HEDGE_ENABLED ?? "1") !== "0",
		maxInFlight: Math.max(1, parseNonNegativeInt($env.PI_STREAM_HEDGE_MAX_INFLIGHT, 2)),
		maxAttempts: Math.max(1, parseNonNegativeInt($env.PI_STREAM_HEDGE_MAX_ATTEMPTS, 4)),
		stallMs: parseNonNegativeInt($env.PI_STREAM_HEDGE_STALL_MS, 5_000),
		hedgeAfterMs: parseNonNegativeInt($env.PI_STREAM_HEDGE_AFTER_MS, 30_000),
	};
}

/** Process-wide counters for hedge effectiveness tuning. */
export interface HedgeStreamStats {
	streams: number;
	/** Streams that launched at least one duplicate. */
	hedgedStreams: number;
	stallTriggers: number;
	afterTriggers: number;
	/** Duplicates that produced the winning completion. */
	hedgeWins: number;
	/** Duplicates promoted after the leader died. */
	promotions: number;
	attempts: number;
	/** Loser attempts aborted after a winner settled. */
	losersAborted: number;
}

const hedgeStats: HedgeStreamStats = {
	streams: 0,
	hedgedStreams: 0,
	stallTriggers: 0,
	afterTriggers: 0,
	hedgeWins: 0,
	promotions: 0,
	attempts: 0,
	losersAborted: 0,
};

/** Snapshot of the process-wide hedge counters. */
export function getHedgeStreamStats(): HedgeStreamStats {
	return { ...hedgeStats };
}

/**
 * An event that commits the attempt: once the consumer sees text, tool calls,
 * or images, the attempt owns the turn and no duplicate may take over.
 */
export function isHedgeCommitEvent(event: AssistantMessageEvent): boolean {
	switch (event.type) {
		case "text_start":
		case "text_delta":
		case "text_end":
		case "toolcall_start":
		case "toolcall_delta":
		case "toolcall_end":
		case "image_end":
			return true;
		default:
			return false;
	}
}

interface HedgeAttempt {
	id: number;
	controller: AbortController;
	lastEventAt: number;
	failed: boolean;
	done: boolean;
	committed: boolean;
	startedAt: number;
	endedAt?: number;
	eventCount: number;
	/** Pre-commit events held back while this attempt is not the leader. */
	buffer: AssistantMessageEvent[];
}

/**
 * Race duplicate same-request attempts; first valid completion wins.
 *
 * @param startAttempt Builds one attempt's event stream for the given signal.
 *   Called with a per-attempt signal linked to `parentSignal`.
 * @param parentSignal Caller cancellation; aborts every attempt.
 * @param modelLabel Model id for log lines.
 */
export function withHedgedStream(
	startAttempt: (signal: AbortSignal | undefined) => AssistantMessageEventStream,
	parentSignal: AbortSignal | undefined,
	modelLabel: string,
): AssistantMessageEventStream {
	const policy = resolveHedgePolicy();
	if (!policy.enabled || policy.maxInFlight < 2) {
		return startAttempt(parentSignal);
	}

	const out = new AssistantMessageEventStream();
	void runHedged();
	return out;

	async function runHedged(): Promise<void> {
		const startMs = Date.now();
		hedgeStats.streams++;
		const attempts = new Map<number, HedgeAttempt>();
		const stallHedgedLeaders = new Set<number>();
		const afterHedgedLeaders = new Set<number>();
		let nextId = 0;
		let leaderId = -1;
		let committed = false;
		let settled = false;
		let launched = 0;
		const streamStats = {
			stallTriggers: 0,
			afterTriggers: 0,
			winnerId: -1,
			hedgeWin: false,
			promoted: false,
		};

		const liveCount = (): number => {
			let n = 0;
			for (const a of attempts.values()) if (!a.failed && !a.done) n++;
			return n;
		};

		const abortLosers = (winnerId: number): void => {
			for (const a of attempts.values()) {
				if (a.id === winnerId || a.failed || a.done) continue;
				a.controller.abort();
				hedgeStats.losersAborted++;
			}
		};

		const logSummary = (): void => {
			logger.debug("hedged stream summary", {
				model: modelLabel,
				durationMs: Date.now() - startMs,
				attempts: launched,
				stallTriggers: streamStats.stallTriggers,
				afterTriggers: streamStats.afterTriggers,
				winnerAttempt: streamStats.winnerId,
				hedgeWin: streamStats.hedgeWin,
				promoted: streamStats.promoted,
				committed,
				cumulative: { ...hedgeStats },
			});
		};

		const settle = (winnerId: number, hedgeWin: boolean): void => {
			if (settled) return;
			settled = true;
			streamStats.winnerId = winnerId;
			streamStats.hedgeWin = hedgeWin;
			if (hedgeWin) hedgeStats.hedgeWins++;
			abortLosers(winnerId);
			logSummary();
		};

		/** Flush a promoted/winning attempt's buffered pre-commit events. */
		const flushBuffer = (a: HedgeAttempt): void => {
			for (const event of a.buffer) {
				if (isHedgeCommitEvent(event)) committed = true;
				out.push(event);
				if (out.done) return;
			}
			a.buffer.length = 0;
		};

		const onTerminal = (a: HedgeAttempt, event?: AssistantMessageEvent, error?: unknown): void => {
			if (settled) return;
			a.endedAt = Date.now();
			if (event?.type === "done") {
				const hedgeWin = a.id !== leaderId;
				if (hedgeWin) flushBuffer(a);
				a.done = true;
				leaderId = a.id;
				out.push(event);
				settle(a.id, hedgeWin);
				return;
			}
			a.failed = true;
			// No leader established yet (synchronous launch failure) counts as a
			// leader failure: surface it instead of hanging the outer stream.
			const isLeader = a.id === leaderId || leaderId < 0;
			if (isLeader && !committed && !(parentSignal?.aborted ?? false)) {
				const replacement = [...attempts.values()].find(o => o.id !== a.id && !o.failed && !o.done);
				if (replacement) {
					leaderId = replacement.id;
					streamStats.promoted = true;
					hedgeStats.promotions++;
					logger.info(
						`hedged stream [${modelLabel}]: leader attempt #${a.id} died after ${a.endedAt - a.startedAt}ms ` +
							`(${a.eventCount} events), promoting duplicate attempt #${replacement.id}`,
					);
					flushBuffer(replacement);
					return;
				}
			}
			if (isLeader) {
				if (event) out.push(event);
				else out.fail(error);
				settle(a.id, false);
				return;
			}
			// A non-leader duplicate died: drop it, the leader still owns the turn.
			try {
				a.controller.abort();
			} catch {}
		};

		const consume = async (a: HedgeAttempt, stream: AssistantMessageEventStream): Promise<void> => {
			try {
				for await (const event of stream) {
					if (settled) return;
					a.lastEventAt = Date.now();
					a.eventCount++;
					if (event.type === "done" || event.type === "error") {
						onTerminal(a, event);
						return;
					}
					if (a.id === leaderId) {
						if (isHedgeCommitEvent(event)) {
							committed = true;
							// The leader owns the turn now: hedged duplicates are losers.
							abortLosers(a.id);
						}
						out.push(event);
						if (out.done) {
							settle(a.id, false);
							return;
						}
					} else {
						// Buffered duplicate: hold pre-commit events back. If this
						// duplicate starts emitting committed output while the
						// leader is stalled, it becomes the leader immediately —
						// it holds the freshest output.
						a.buffer.push(event);
						if (isHedgeCommitEvent(event)) {
							const oldLeader = leaderId;
							leaderId = a.id;
							streamStats.promoted = true;
							hedgeStats.promotions++;
							logger.info(
								`hedged stream [${modelLabel}]: duplicate attempt #${a.id} emitting output while ` +
									`leader #${oldLeader} stalled — promoting it to leader`,
							);
							flushBuffer(a);
						}
					}
				}
				onTerminal(a, undefined, new Error(`hedged attempt #${a.id} stream ended without a terminal event`));
			} catch (error) {
				onTerminal(a, undefined, error);
			}
		};

		const launch = (): HedgeAttempt | undefined => {
			if (settled || launched >= policy.maxAttempts) return undefined;
			const id = nextId++;
			launched++;
			hedgeStats.attempts++;
			const controller = new AbortController();
			if (parentSignal?.aborted) controller.abort();
			const signal =
				parentSignal !== undefined ? AbortSignal.any([parentSignal, controller.signal]) : controller.signal;
			const a: HedgeAttempt = {
				id,
				controller,
				lastEventAt: Date.now(),
				failed: false,
				done: false,
				committed: false,
				startedAt: Date.now(),
				eventCount: 0,
				buffer: [],
			};
			attempts.set(id, a);
			let stream: AssistantMessageEventStream;
			try {
				stream = startAttempt(signal);
			} catch (error) {
				onTerminal(a, undefined, error);
				return undefined;
			}
			logger.debug(`hedged stream [${modelLabel}]: launched attempt #${id}`, {
				inFlight: liveCount(),
				maxInFlight: policy.maxInFlight,
			});
			void consume(a, stream);
			return a;
		};

		// The leader attempt starts immediately.
		const leader = launch();
		if (leader) leaderId = leader.id;
		if (leaderId < 0) return; // synchronous launch failure already settled

		// Hedge monitor: fire duplicates on leader stall or slow completion.
		while (!settled) {
			await scheduler.wait(100);
			if (settled || committed) continue;
			const leaderAttempt = attempts.get(leaderId);
			if (!leaderAttempt || leaderAttempt.failed || leaderAttempt.done) continue;
			if (launched >= policy.maxAttempts || liveCount() >= policy.maxInFlight) continue;
			const now = Date.now();
			const stalledFor = now - leaderAttempt.lastEventAt;
			if (policy.stallMs > 0 && stalledFor >= policy.stallMs && !stallHedgedLeaders.has(leaderId)) {
				stallHedgedLeaders.add(leaderId);
				streamStats.stallTriggers++;
				hedgeStats.stallTriggers++;
				if (launched === 1) hedgeStats.hedgedStreams++;
				logger.info(
					`hedged stream [${modelLabel}]: leader attempt #${leaderId} stalled ${stalledFor}ms without events ` +
						`— firing duplicate of the same request (attempt #${launched}, same model/route)`,
				);
				launch();
			} else if (
				policy.hedgeAfterMs > 0 &&
				now - startMs >= policy.hedgeAfterMs &&
				!afterHedgedLeaders.has(leaderId)
			) {
				afterHedgedLeaders.add(leaderId);
				streamStats.afterTriggers++;
				hedgeStats.afterTriggers++;
				if (launched === 1) hedgeStats.hedgedStreams++;
				logger.info(
					`hedged stream [${modelLabel}]: no completion after ${now - startMs}ms ` +
						`— firing duplicate of the same request (attempt #${launched}, same model/route)`,
				);
				launch();
			}
		}
	}
}
