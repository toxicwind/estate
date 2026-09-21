// Failure injection: TAU extension with a dead primary tier model.
// Configures the LOW tier to a nonexistent model and observes whether the
// extension fails over, errors, or degrades. (Recon says: no failover.)
import { plugin } from "bun";
plugin({
	name: "gavel-stub",
	setup(build) {
		build.onResolve(
			{ filter: /^@oh-my-pi\/pi-coding-agent(\/.*)?$/ },
			(args) => ({ path: args.path, namespace: "gavel-stub" }),
		);
		build.onLoad({ filter: /.*/, namespace: "gavel-stub" }, () => ({
			contents: `export const getAgentDir = () => "/tmp/bakeoff-agent-stub";\nexport default {};`,
			loader: "ts",
		}));
	},
});
const EXT = "/home/toxic/sovereign/tau-extensions/omp-model-router";
const { resolveRouting } = await import(`${EXT}/src/routing/compose.ts`);
const { streamSimple } = await import(`${EXT}/node_modules/@oh-my-pi/pi-ai`);

const PROFILE = {
	high: { model: "herd/gemini/gemini-3-flash-preview", thinking: "off" },
	medium: { model: "herd/beellama/qwen-flash-128k", thinking: "off" },
	low: { model: "herd/nonexistent-model-xyz", thinking: "off" }, // DEAD
};
const registry: any = {
	find(p: string, id: string) {
		if (p !== "herd") return undefined;
		return {
			id, provider: p, modelId: id, baseUrl: "http://127.0.0.1:25100/v1",
			api: "openai-completions", headers: {},
			compat: { streamIdleTimeoutMs: 60000 },
			cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
		};
	},
	getApiKey: async () => "none",
};
const context: any = {
	messages: [{ role: "user", content: "Reply with exactly the word DONE and nothing else.", timestamp: Date.now() }],
};
const d: any = await resolveRouting(
	{ context, previousDecision: undefined, isBudgetExceeded: false, modelRegistry: registry },
	{ profileName: "bakeoff", profile: PROFILE as any, phaseBias: 0.5 },
);
console.log("DECISION:", JSON.stringify({ tier: d.tier, targetModel: d.targetModelId, isHeuristic: d.isHeuristic }));
// Now serve it the way provider.ts would — does anything catch the 404?
const m = registry.find("herd", String(d.targetModelId).replace(/^herd\//, ""));
const ac = new AbortController();
const t = setTimeout(() => ac.abort(), 30000);
try {
	const s: any = streamSimple(m,
		{ messages: [{ role: "user", content: "Reply with exactly the word DONE and nothing else.", timestamp: Date.now() }] },
		{ apiKey: "none", headers: {}, signal: ac.signal, maxTokens: 10 });
	let text = "";
	for await (const ev of s) {
		const e: any = ev;
		if (e.type === "text_delta") text += e.delta;
		else if (e.type === "error") console.log("SERVE_ERROR_EVENT:", (e.errorMessage ?? "").slice(0, 160), "status=", e.errorStatus);
	}
	console.log("SERVE_TEXT:", JSON.stringify(text));
} catch (e: any) {
	console.log("SERVE_THREW:", String(e?.message ?? e).slice(0, 200));
} finally {
	clearTimeout(t);
}
console.log("FAILOVER_PROBE_DONE");
