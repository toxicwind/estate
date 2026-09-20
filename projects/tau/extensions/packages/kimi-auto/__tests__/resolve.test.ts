import { describe, it, expect } from "bun:test";
import {
	formatStatus,
	isStale,
	readState,
	resolveModel,
	type KimiAutoState,
} from "../src/resolve.ts";

const NOW = Date.parse("2026-09-20T06:00:00Z");

function sample(over: Partial<KimiAutoState> = {}): KimiAutoState {
	return {
		model: "kimi-k2",
		healthy: true,
		reason: "kimi-k2 fastest healthy probe (792ms); alternates: kimi-k3-nim (17065ms)",
		updated_at: "2026-09-20T05:55:03Z",
		resolver: "kimi-auto-resolver/1.0",
		secrets_present: ["OPENROUTER_API_KEY", "NVIDIA_API_KEY"],
		secrets_missing: ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
		candidates: [
			{ id: "kimi-k2", ok: true, latency_ms: 792, note: "ok" },
			{ id: "kimi-k3-nim", ok: true, latency_ms: 17065, note: "ok" },
			{ id: "openrouter-kimi/moonshotai/kimi-k2", ok: false, latency_ms: 111, note: "http_401" },
		],
		...over,
	};
}

describe("readState", () => {
	it("parses a full resolver state blob", () => {
		const s = readState(JSON.stringify(sample()));
		expect(s.model).toBe("kimi-k2");
		expect(s.healthy).toBe(true);
		expect(s.candidates).toHaveLength(3);
		expect(s.secrets_present).toContain("NVIDIA_API_KEY");
	});

	it("never throws on garbage; reports unhealthy", () => {
		const s = readState("not json{{{");
		expect(s.healthy).toBe(false);
		expect(s.model).toBeNull();
		expect(s.reason).toMatch(/parse/i);
	});

	it("treats empty model as unhealthy", () => {
		const s = readState(JSON.stringify(sample({ model: "" })));
		expect(s.healthy).toBe(false);
	});
});

describe("resolveModel", () => {
	it("resolves to the healthy best model", () => {
		const r = resolveModel(sample());
		expect(r).toEqual({ model: "kimi-k2" });
	});

	it("fails loud when unhealthy", () => {
		const r = resolveModel(sample({ healthy: false, reason: "no Kimi candidate healthy" }));
		expect("error" in r).toBe(true);
	});

	it("refuses a self-referential alias (no routing loop)", () => {
		const r = resolveModel(sample({ model: "kimi-auto" }));
		expect("error" in r).toBe(true);
		expect((r as { error: string }).error).toMatch(/self/i);
	});
});

describe("isStale", () => {
	it("fresh state is not stale", () => {
		expect(isStale(sample(), NOW, 15 * 60_000)).toBe(false);
	});

	it("state older than maxAge is stale", () => {
		const s = sample({ updated_at: "2026-09-20T05:00:00Z" });
		expect(isStale(s, NOW, 15 * 60_000)).toBe(true);
	});

	it("unparseable timestamp is stale", () => {
		const s = sample({ updated_at: "whenever" });
		expect(isStale(s, NOW, 15 * 60_000)).toBe(true);
	});
});

describe("formatStatus", () => {
	it("shows resolution, latency, freshness and candidate table", () => {
		const text = formatStatus(sample(), NOW);
		expect(text).toMatch(/kimi-k2/);
		expect(text).toMatch(/792ms/);
		expect(text).toMatch(/fresh/);
		expect(text).toMatch(/kimi-k3-nim/);
		expect(text).toMatch(/17065ms/);
		expect(text).toMatch(/http_401/);
	});

	it("flags stale and unhealthy states loudly", () => {
		const text = formatStatus(sample({ healthy: false, reason: "no Kimi candidate healthy" }), NOW);
		expect(text).toMatch(/UNHEALTHY/);
		const stale = formatStatus(sample({ updated_at: "2026-09-20T04:00:00Z" }), NOW);
		expect(stale).toMatch(/STALE/);
	});
});
