import { afterAll, describe, expect, it } from "bun:test";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import {
	appendLedger,
	formatEvent,
	normalizeBurnPath,
	parseBurnCli,
	parseDuration,
	SessionTracker,
	type BurnEvent,
	type BurnThresholds,
} from "./burn";

const THRESHOLDS: BurnThresholds = {
	burnRateTokPerMin: 1_000_000, // high so it never fires in these tests unless wanted
	burnWindowMs: 10 * 60_000,
	readLoopN: 3,
	readLoopWindowMs: 15 * 60_000,
	editChurnN: 3,
	editChurnWindowMs: 15 * 60_000,
	errorStormN: 3,
	bloatTokens: 500,
	stalledRequests: 4,
};

describe("parseDuration", () => {
	it("maps unit suffixes to milliseconds", () => {
		expect(parseDuration("30s")).toBe(30_000);
		expect(parseDuration("10m")).toBe(600_000);
		expect(parseDuration("2h")).toBe(7_200_000);
		expect(parseDuration("3d")).toBe(3 * 86_400_000);
		expect(parseDuration("1w")).toBe(7 * 86_400_000);
		expect(parseDuration("m")).toBe(60_000);
	});
	it("rejects unparseable durations", () => {
		expect(() => parseDuration("soon")).toThrow();
		expect(() => parseDuration("5x")).toThrow();
	});
});

describe("normalizeBurnPath", () => {
	it("strips line/raw selectors but keeps URL schemes intact", () => {
		expect(normalizeBurnPath("src/foo.ts:50-200")).toBe("src/foo.ts");
		expect(normalizeBurnPath("src/foo.ts:raw")).toBe("src/foo.ts");
		expect(normalizeBurnPath("artifact://37:50-100")).toBe("artifact://37");
		expect(normalizeBurnPath("docs/readme.md")).toBe("docs/readme.md");
	});
});

describe("parseBurnCli", () => {
	it("applies defaults", () => {
		const o = parseBurnCli([]);
		expect(o.once).toBe(false);
		expect(o.intervalMs).toBe(5_000);
		expect(o.burnRateTokPerMin).toBe(30_000);
		expect(o.bloatTokens).toBe(20_000);
	});
	it("honors explicit flags", () => {
		const o = parseBurnCli(["--once", "--since", "3d", "--burn-rate", "1000", "--quiet"]);
		expect(o.once).toBe(true);
		expect(o.sinceMs).toBe(3 * 86_400_000);
		expect(o.burnRateTokPerMin).toBe(1_000);
		expect(o.quiet).toBe(true);
	});
});

// ---------------------------------------------------------------------------
// Synthetic transcript builders

const T0 = 1_750_000_000_000;
const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "burn-test-"));
afterAll(() => fs.rm(tmpDir, { recursive: true, force: true }));

let callSeq = 0;
function toolCall(
	name: string,
	args: Record<string, unknown>,
): { id: string; block: Record<string, unknown> } {
	const id = `call-${++callSeq}`;
	return { id, block: { type: "toolCall", id, name, arguments: args } };
}

function asst(
	ts: number,
	opts: {
		usage?: { input?: number; output?: number; cacheRead?: number; cacheWrite?: number; cost?: number };
		calls?: { id: string; block: Record<string, unknown> }[];
	} = {},
): string {
	return JSON.stringify({
		type: "message",
		message: {
			role: "assistant",
			model: "test-model",
			timestamp: ts,
			stopReason: "toolUse",
			usage: {
				input: opts.usage?.input ?? 100,
				output: opts.usage?.output ?? 50,
				cacheRead: opts.usage?.cacheRead ?? 0,
				cacheWrite: opts.usage?.cacheWrite ?? 0,
				cost: { total: opts.usage?.cost ?? 0 },
			},
			content: (opts.calls ?? []).map(c => c.block),
		},
	});
}

function toolResult(callId: string, name: string, text: string, isError = false): string {
	return JSON.stringify({
		type: "message",
		message: {
			role: "toolResult",
			toolCallId: callId,
			toolName: name,
			timestamp: T0,
			isError,
			content: [{ type: "text", text }],
		},
	});
}

function tracker(id = "sess-test"): SessionTracker {
	return new SessionTracker(id, path.join(tmpDir, `${id}.jsonl`), THRESHOLDS);
}

function readPair(t: SessionTracker, ts: number, filePath: string): BurnEvent[] {
	const c = toolCall("read", { path: filePath });
	const events = t.ingest(asst(ts, { calls: [c] }));
	return events.concat(t.ingest(toolResult(c.id, "read", "x".repeat(40))));
}

function editPair(t: SessionTracker, ts: number, filePath: string, ok: boolean): BurnEvent[] {
	const c = toolCall("edit", { path: filePath, oldText: "a", newText: "b" });
	const events = t.ingest(asst(ts, { calls: [c] }));
	return events.concat(t.ingest(toolResult(c.id, "edit", ok ? "done" : "no match", !ok)));
}

// ---------------------------------------------------------------------------
// Detector contracts

describe("read-loop detector", () => {
	it("fires once the same file is read N times with no intervening edit", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		for (let i = 0; i < 2; i++) all = all.concat(readPair(t, T0 + i * 1000, "src/a.ts"));
		expect(all.some(e => e.kind === "read-loop")).toBe(false);
		all = all.concat(readPair(t, T0 + 2000, "src/a.ts"));
		const hit = all.filter(e => e.kind === "read-loop");
		expect(hit.length).toBe(1);
		expect(hit[0].detail).toContain("src/a.ts");
	});

	it("does not re-fire for the same path until a successful edit breaks the loop", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		for (let i = 0; i < 4; i++) all = all.concat(readPair(t, T0 + i * 1000, "src/b.ts"));
		expect(all.filter(e => e.kind === "read-loop").length).toBe(1);
		// a successful edit breaks the loop; the next loop fires again
		all = all.concat(editPair(t, T0 + 5000, "src/b.ts", true));
		for (let i = 0; i < 3; i++) all = all.concat(readPair(t, T0 + 6000 + i * 1000, "src/b.ts"));
		expect(all.filter(e => e.kind === "read-loop").length).toBe(2);
	});

	it("does not fire when an edit lands between reads", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		all = all.concat(readPair(t, T0, "src/c.ts"));
		all = all.concat(readPair(t, T0 + 1000, "src/c.ts"));
		all = all.concat(editPair(t, T0 + 2000, "src/c.ts", true));
		all = all.concat(readPair(t, T0 + 3000, "src/c.ts"));
		all = all.concat(readPair(t, T0 + 4000, "src/c.ts"));
		expect(all.some(e => e.kind === "read-loop")).toBe(false);
	});

	it("treats :line selectors as the same file", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		all = all.concat(readPair(t, T0, "src/d.ts:1-50"));
		all = all.concat(readPair(t, T0 + 1000, "src/d.ts:51-100"));
		all = all.concat(readPair(t, T0 + 2000, "src/d.ts:raw"));
		expect(all.filter(e => e.kind === "read-loop").length).toBe(1);
	});
});

describe("edit-churn detector", () => {
	it("fires after N failed edits against the same file", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		for (let i = 0; i < 2; i++) all = all.concat(editPair(t, T0 + i * 1000, "src/e.ts", false));
		expect(all.some(e => e.kind === "edit-churn")).toBe(false);
		all = all.concat(editPair(t, T0 + 2000, "src/e.ts", false));
		const hit = all.filter(e => e.kind === "edit-churn");
		expect(hit.length).toBe(1);
		expect(hit[0].detail).toContain("src/e.ts");
	});

	it("stays quiet for successful edits", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		for (let i = 0; i < 5; i++) all = all.concat(editPair(t, T0 + i * 1000, "src/f.ts", true));
		expect(all.some(e => e.kind === "edit-churn")).toBe(false);
	});
});

describe("error-storm detector", () => {
	it("fires after N consecutive failing tool calls and re-arms", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		for (let i = 0; i < 2; i++) {
			const c = toolCall("bash", { command: "boom" });
			all = all.concat(t.ingest(asst(T0 + i * 1000, { calls: [c] })));
			all = all.concat(t.ingest(toolResult(c.id, "bash", "exit 1", true)));
		}
		expect(all.some(e => e.kind === "error-storm")).toBe(false);
		const c = toolCall("bash", { command: "boom" });
		all = all.concat(t.ingest(asst(T0 + 2000, { calls: [c] })));
		all = all.concat(t.ingest(toolResult(c.id, "bash", "exit 1", true)));
		expect(all.filter(e => e.kind === "error-storm").length).toBe(1);
	});

	it("resets the streak on a success", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		for (let i = 0; i < 2; i++) {
			const c = toolCall("bash", { command: "boom" });
			all = all.concat(t.ingest(asst(T0 + i * 1000, { calls: [c] })));
			all = all.concat(t.ingest(toolResult(c.id, "bash", "exit 1", true)));
		}
		const ok = toolCall("bash", { command: "true" });
		all = all.concat(t.ingest(asst(T0 + 2000, { calls: [ok] })));
		all = all.concat(t.ingest(toolResult(ok.id, "bash", "ok", false)));
		for (let i = 0; i < 2; i++) {
			const c = toolCall("bash", { command: "boom" });
			all = all.concat(t.ingest(asst(T0 + 3000 + i * 1000, { calls: [c] })));
			all = all.concat(t.ingest(toolResult(c.id, "bash", "exit 1", true)));
		}
		expect(all.some(e => e.kind === "error-storm")).toBe(false);
	});
});

describe("bloat detector", () => {
	it("fires on a result above the token threshold and stays quiet below it", () => {
		const t = tracker();
		const small = toolCall("read", { path: "src/g.ts" });
		let all: BurnEvent[] = [];
		all = all.concat(t.ingest(asst(T0, { calls: [small] })));
		all = all.concat(t.ingest(toolResult(small.id, "read", "x".repeat(400)))); // ~100 tok
		expect(all.some(e => e.kind === "bloat")).toBe(false);
		const big = toolCall("read", { path: "src/h.ts" });
		all = all.concat(t.ingest(asst(T0 + 1000, { calls: [big] })));
		all = all.concat(t.ingest(toolResult(big.id, "read", "y".repeat(4000)))); // ~1000 tok
		const hit = all.filter(e => e.kind === "bloat");
		expect(hit.length).toBe(1);
		expect(hit[0].tokens).toBeGreaterThanOrEqual(500);
	});
});

describe("cost-budget detector", () => {
	it("fires once per ladder rung crossed and never repeats a rung", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		all = all.concat(t.ingest(asst(T0, { usage: { cost: 0.6 } })));
		expect(all.some(e => e.kind === "cost-budget")).toBe(false);
		all = all.concat(t.ingest(asst(T0 + 1000, { usage: { cost: 0.5 } }))); // total 1.1
		const first = all.filter(e => e.kind === "cost-budget");
		expect(first.length).toBe(1);
		expect(first[0].detail).toContain("$1");
		all = all.concat(t.ingest(asst(T0 + 2000, { usage: { cost: 0.2 } }))); // total 1.3, no new rung
		expect(all.filter(e => e.kind === "cost-budget").length).toBe(1);
		all = all.concat(t.ingest(asst(T0 + 3000, { usage: { cost: 4 } }))); // total 5.3 → $5 rung
		expect(all.filter(e => e.kind === "cost-budget").length).toBe(2);
	});
});

describe("burn-rate detector", () => {
	it("fires when the trailing-window rate exceeds the threshold", () => {
		const t2 = new SessionTracker("sess-burn", path.join(tmpDir, "sess-burn.jsonl"), {
			...THRESHOLDS,
			burnRateTokPerMin: 10_000,
		});
		let all: BurnEvent[] = [];
		// 4 requests × 30k tokens within 10 minutes → ~12k tok/min
		for (let i = 0; i < 4; i++) {
			all = all.concat(
				t2.ingest(asst(T0 + i * 60_000, { usage: { input: 25_000, output: 5_000 } })),
			);
		}
		const hit = all.filter(e => e.kind === "burn-rate");
		expect(hit.length).toBe(1);
		expect(hit[0].severity).toBe("critical");
	});

	it("re-arms when the session cools down", () => {
		const t2 = new SessionTracker("sess-cool", path.join(tmpDir, "sess-cool.jsonl"), {
			...THRESHOLDS,
			burnRateTokPerMin: 10_000,
		});
		let all: BurnEvent[] = [];
		all = all.concat(t2.ingest(asst(T0, { usage: { input: 100_000, output: 10_000 } })));
		expect(all.filter(e => e.kind === "burn-rate").length).toBe(1);
		// one more request 30 minutes later — old sample is outside the window
		all = all.concat(t2.ingest(asst(T0 + 30 * 60_000, { usage: { input: 100, output: 50 } })));
		expect(all.filter(e => e.kind === "burn-rate").length).toBe(1);
	});
});

describe("stalled detector", () => {
	it("fires after N consecutive tool-less requests with no progress signal", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		for (let i = 0; i < 3; i++) all = all.concat(t.ingest(asst(T0 + i * 60_000)));
		expect(all.some(e => e.kind === "stalled")).toBe(false);
		all = all.concat(t.ingest(asst(T0 + 3 * 60_000)));
		expect(all.filter(e => e.kind === "stalled").length).toBe(1);
	});

	it("a progress tool resets the stall counter", () => {
		const t = tracker();
		let all: BurnEvent[] = [];
		for (let i = 0; i < 3; i++) all = all.concat(t.ingest(asst(T0 + i * 60_000)));
		const c = toolCall("bash", { command: "echo hi" });
		all = all.concat(t.ingest(asst(T0 + 3 * 60_000, { calls: [c] })));
		all = all.concat(t.ingest(toolResult(c.id, "bash", "hi", false)));
		all = all.concat(t.ingest(asst(T0 + 4 * 60_000)));
		expect(all.some(e => e.kind === "stalled")).toBe(false);
	});
});

describe("compaction", () => {
	it("emits a compaction event with a context-reset detail", () => {
		const t = tracker();
		const events = t.ingest(JSON.stringify({ type: "compaction", timestamp: new Date(T0).toISOString() }));
		expect(events.length).toBe(1);
		expect(events[0].kind).toBe("compaction");
		expect(t.compactionCount).toBe(1);
	});
});

describe("ledger", () => {
	it("appends one JSONL line per event", async () => {
		const ledger = path.join(tmpDir, "ledger.jsonl");
		const events: BurnEvent[] = [
			{
				at: T0,
				kind: "bloat",
				severity: "warn",
				sessionId: "s1",
				sessionPath: "/x/s1.jsonl",
				ts: T0,
				detail: "test",
				tokens: 42,
			},
		];
		await appendLedger(ledger, events);
		await appendLedger(ledger, []);
		const text = await fs.readFile(ledger, "utf8");
		const lines = text.trim().split("\n");
		expect(lines.length).toBe(1);
		expect(JSON.parse(lines[0]).kind).toBe("bloat");
	});

	it("formats events as one-line human alerts", () => {
		const s = formatEvent({
			at: T0,
			kind: "read-loop",
			severity: "warn",
			sessionId: "sess-abc",
			sessionPath: "/x",
			ts: T0,
			detail: "d",
			tokens: 0,
		});
		expect(s).toContain("[read-loop]");
		expect(s).toContain("sess-abc");
	});
});

describe("robustness", () => {
	it("ignores torn tail lines and malformed JSON without throwing", () => {
		const t = tracker();
		expect(t.ingest('{"type":"message"').length).toBe(0);
		expect(t.ingest("not json at all").length).toBe(0);
		expect(t.ingest("").length).toBe(0);
		expect(t.requestCount).toBe(0);
	});
});
