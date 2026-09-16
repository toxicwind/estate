/**
 * Contracts for hedged streaming: stalled leaders trigger a duplicate of the
 * SAME request (same model/route, never a fallback), first completion wins,
 * losers are aborted, and in-flight duplicates are capped. Switching is only
 * allowed before the leader commits replay-unsafe output.
 */
import { afterEach, describe, expect, it } from "bun:test";
import type { AssistantMessage, AssistantMessageEvent, Usage } from "@oh-my-pi/pi-ai/types";
import { AssistantMessageEventStream } from "@oh-my-pi/pi-ai/utils/event-stream";
import { getHedgeStreamStats, withHedgedStream } from "@oh-my-pi/pi-ai/utils/hedged-stream";

const ENV_KEYS = [
	"PI_STREAM_HEDGE_ENABLED",
	"PI_STREAM_HEDGE_MAX_INFLIGHT",
	"PI_STREAM_HEDGE_MAX_ATTEMPTS",
	"PI_STREAM_HEDGE_STALL_MS",
	"PI_STREAM_HEDGE_AFTER_MS",
] as const;

const savedEnv = new Map<string, string | undefined>();
function setEnv(vars: Record<string, string>): void {
	for (const key of ENV_KEYS) {
		if (!savedEnv.has(key)) savedEnv.set(key, process.env[key]);
		if (vars[key] !== undefined) process.env[key] = vars[key];
		else delete process.env[key];
	}
}
afterEach(() => {
	for (const [key, value] of savedEnv) {
		if (value === undefined) delete process.env[key];
		else process.env[key] = value;
	}
	savedEnv.clear();
});

const wait = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

function usage(): Usage {
	return {
		input: 0,
		output: 0,
		cacheRead: 0,
		cacheWrite: 0,
		totalTokens: 0,
		cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
	};
}

function assistant(texts: string[] = []): AssistantMessage {
	return {
		role: "assistant",
		content: texts.map(text => ({ type: "text" as const, text })),
		api: "openai-completions",
		provider: "test",
		model: "test-model",
		timestamp: 1,
		stopReason: "stop",
		usage: usage(),
	};
}

const startEvent = (message: AssistantMessage): AssistantMessageEvent =>
	({ type: "start", partial: message }) as unknown as AssistantMessageEvent;
const thinkingEvent = (message: AssistantMessage): AssistantMessageEvent =>
	({
		type: "thinking_delta",
		contentIndex: 0,
		delta: "hmm",
		partial: message,
	}) as unknown as AssistantMessageEvent;
const textEvent = (message: AssistantMessage, delta = "hi"): AssistantMessageEvent =>
	({
		type: "text_delta",
		contentIndex: 0,
		delta,
		partial: message,
	}) as unknown as AssistantMessageEvent;
const doneEvent = (message: AssistantMessage): AssistantMessageEvent =>
	({ type: "done", reason: "stop", message }) as unknown as AssistantMessageEvent;
const errorEvent = (message: AssistantMessage): AssistantMessageEvent =>
	({ type: "error", reason: "error", error: message }) as unknown as AssistantMessageEvent;

async function drain(stream: AssistantMessageEventStream): Promise<AssistantMessageEvent[]> {
	const events: AssistantMessageEvent[] = [];
	for await (const event of stream) events.push(event);
	return events;
}

describe("withHedgedStream", () => {
	it("passes a healthy stream through with a single attempt", async () => {
		setEnv({ PI_STREAM_HEDGE_STALL_MS: "50", PI_STREAM_HEDGE_AFTER_MS: "0" });
		const message = assistant(["hello"]);
		const inner = new AssistantMessageEventStream();
		let calls = 0;
		const signals: (AbortSignal | undefined)[] = [];
		const outer = withHedgedStream(
			signal => {
				calls++;
				signals.push(signal);
				return inner;
			},
			undefined,
			"test-model",
		);
		const drained = drain(outer);
		inner.push(startEvent(message));
		inner.push(textEvent(message));
		inner.push(doneEvent(message));
		const events = await drained;
		expect(calls).toBe(1);
		expect(events.map(e => e.type)).toEqual(["start", "text_delta", "done"]);
		// Each attempt gets its own abort signal linked to the parent.
		expect(signals[0]).toBeDefined();
	});

	it("hedges a stalled leader and promotes the duplicate when the leader dies", async () => {
		setEnv({ PI_STREAM_HEDGE_STALL_MS: "50", PI_STREAM_HEDGE_AFTER_MS: "0" });
		const before = getHedgeStreamStats();
		const leaderMessage = assistant();
		const dupMessage = assistant(["recovered"]);
		const leaderStream = new AssistantMessageEventStream();
		const dupStream = new AssistantMessageEventStream();
		const streams = [leaderStream, dupStream];
		let calls = 0;
		const outer = withHedgedStream(
			() => streams[calls++]!,
			undefined,
			"test-model",
		);
		const drained = drain(outer);
		// Leader emits thinking, then stalls (no more events).
		leaderStream.push(startEvent(leaderMessage));
		leaderStream.push(thinkingEvent(leaderMessage));
		await wait(300); // stallMs=50, monitor ticks every 100ms
		expect(calls).toBe(2);
		// Duplicate's pre-commit events are buffered while the leader is alive.
		dupStream.push(startEvent(dupMessage));
		dupStream.push(thinkingEvent(dupMessage));
		await wait(50);
		// Leader dies mid-thinking: duplicate is promoted, buffer flushed.
		leaderStream.fail(new Error("stream closed with reason: error"));
		dupStream.push(textEvent(dupMessage));
		dupStream.push(doneEvent(dupMessage));
		const events = await drained;
		const types = events.map(e => e.type);
		expect(types[0]).toBe("start");
		expect(types).toContain("thinking_delta");
		expect(types).toContain("text_delta");
		expect(types[types.length - 1]).toBe("done");
		const after = getHedgeStreamStats();
		expect(after.stallTriggers).toBeGreaterThan(before.stallTriggers);
		expect(after.promotions).toBeGreaterThan(before.promotions);
	});

	it("first completion wins: a buffered duplicate that finishes first settles the stream", async () => {
		setEnv({ PI_STREAM_HEDGE_STALL_MS: "50", PI_STREAM_HEDGE_AFTER_MS: "0" });
		const before = getHedgeStreamStats();
		const leaderStream = new AssistantMessageEventStream();
		const dupStream = new AssistantMessageEventStream();
		const streams = [leaderStream, dupStream];
		const signals: (AbortSignal | undefined)[] = [];
		let calls = 0;
		const outer = withHedgedStream(
			signal => {
				signals.push(signal);
				return streams[calls++]!;
			},
			undefined,
			"test-model",
		);
		const drained = drain(outer);
		const leaderMessage = assistant();
		leaderStream.push(startEvent(leaderMessage));
		leaderStream.push(thinkingEvent(leaderMessage));
		await wait(300);
		expect(calls).toBe(2);
		const dupMessage = assistant(["winner"]);
		dupStream.push(startEvent(dupMessage));
		dupStream.push(thinkingEvent(dupMessage));
		// Duplicate finishes while still buffered (no committed output yet):
		// first completion wins.
		dupStream.push(doneEvent(dupMessage));
		const events = await drained;
		expect(events[events.length - 1]?.type).toBe("done");
		const done = events[events.length - 1];
		if (done?.type === "done") {
			expect(done.message.content).toEqual([{ type: "text", text: "winner" }]);
		} else {
			throw new Error("expected done");
		}
		// The loser (stalled leader) is aborted.
		await wait(50);
		expect(signals[0]?.aborted).toBe(true);
		const after = getHedgeStreamStats();
		expect(after.hedgeWins).toBeGreaterThan(before.hedgeWins);
	});

	it("never switches after the leader commits output: the error is forwarded", async () => {
		setEnv({ PI_STREAM_HEDGE_STALL_MS: "50", PI_STREAM_HEDGE_AFTER_MS: "0" });
		const leaderStream = new AssistantMessageEventStream();
		const dupStream = new AssistantMessageEventStream();
		const streams = [leaderStream, dupStream];
		const signals: (AbortSignal | undefined)[] = [];
		let calls = 0;
		const outer = withHedgedStream(
			signal => {
				signals.push(signal);
				return streams[calls++]!;
			},
			undefined,
			"test-model",
		);
		const drained = drain(outer);
		const message = assistant();
		leaderStream.push(startEvent(message));
		leaderStream.push(textEvent(message, "hello"));
		// Commit aborts any in-flight duplicate immediately.
		await wait(300);
		expect(calls).toBe(1);
		const errMessage = assistant();
		errMessage.stopReason = "error";
		leaderStream.push(errorEvent(errMessage));
		const events = await drained;
		expect(events.map(e => e.type)).toEqual(["start", "text_delta", "error"]);
	});

	it("caps in-flight duplicates at maxInFlight", async () => {
		setEnv({
			PI_STREAM_HEDGE_STALL_MS: "50",
			PI_STREAM_HEDGE_AFTER_MS: "0",
			PI_STREAM_HEDGE_MAX_INFLIGHT: "2",
			PI_STREAM_HEDGE_MAX_ATTEMPTS: "4",
		});
		const mk = (): AssistantMessageEventStream => new AssistantMessageEventStream();
		const streams = [mk(), mk(), mk(), mk()];
		let calls = 0;
		const outer = withHedgedStream(
			() => streams[calls++]!,
			undefined,
			"test-model",
		);
		const drained = drain(outer);
		const message = assistant();
		// Leader stalls; both attempts stay alive but silent.
		streams[0]!.push(startEvent(message));
		await wait(350);
		expect(calls).toBe(2);
		await wait(300);
		expect(calls).toBe(2); // capped: no third attempt while two are live
		// Kill the leader: duplicate promoted, still stalled -> one more hedge allowed.
		streams[0]!.fail(new Error("leader died"));
		await wait(350);
		expect(calls).toBe(3);
		streams[2]!.push(doneEvent(assistant(["ok"])));
		const events = await drained;
		expect(events[events.length - 1]?.type).toBe("done");
	});

	it("disabled hedging is a transparent passthrough", async () => {
		setEnv({ PI_STREAM_HEDGE_ENABLED: "0" });
		const inner = new AssistantMessageEventStream();
		const parent = new AbortController().signal;
		const outer = withHedgedStream(() => inner, parent, "test-model");
		expect(outer).toBe(inner);
	});

	it("surfaces a synchronous launch failure instead of hanging", async () => {
		setEnv({});
		const outer = withHedgedStream(
			() => {
				throw new Error("no api key");
			},
			undefined,
			"test-model",
		);
		await expect(drain(outer)).rejects.toThrow("no api key");
	});

	it("never switches providers: duplicates use the same startAttempt factory", async () => {
		setEnv({ PI_STREAM_HEDGE_STALL_MS: "50", PI_STREAM_HEDGE_AFTER_MS: "0" });
		const models: string[] = [];
		const mk = (): AssistantMessageEventStream => new AssistantMessageEventStream();
		const streams = [mk(), mk()];
		let calls = 0;
		const outer = withHedgedStream(
			() => {
				models.push("same-model/same-route");
				return streams[calls++]!;
			},
			undefined,
			"test-model",
		);
		const drained = drain(outer);
		streams[0]!.push(startEvent(assistant()));
		await wait(300);
		expect(calls).toBe(2);
		expect(models).toEqual(["same-model/same-route", "same-model/same-route"]);
		streams[1]!.push(doneEvent(assistant(["ok"])));
		await drained;
	});
});
