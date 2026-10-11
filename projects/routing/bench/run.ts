// Bake-off runner: TAU omp-model-router extension vs Sovereign router.
// Usage (on yote):
//   bun run.ts --prompts prompts.json --out results/<stamp>.json [--legs tau,sovereign] [--retries 3]
//
// TAU leg exercises the REAL extension routing core (src/routing/compose.ts
// resolveRouting: heuristic + adaptive classifier attempt) and serves the
// chosen tier model through pi-ai's streamSimple — the same provider path the
// extension's provider.ts uses. The modelRegistry is a thin stub that maps
// provider refs to the estate's real routers; no routing logic is stubbed.
// Sovereign leg POSTs :25104/v1/chat/completions model=sovereign/free.
// Raw JSON (every trial, every attempt) goes to --out. Judge separately.
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
const fs = await import("node:fs/promises");

const args: Record<string, string> = {};
for (let i = 2; i < process.argv.length; i += 2)
	args[process.argv[i].replace(/^--/, "")] = process.argv[i + 1];
const legs = (args.legs ?? "tau,sovereign").split(",");
const retries = parseInt(args.retries ?? "3", 10);
const maxTokens = parseInt(args["max-tokens"] ?? "600", 10);
const promptsFile = args.prompts ?? "prompts.json";
const outFile = args.out ?? `results/${new Date().toISOString().replace(/[:.]/g, "-")}.json`;

const PROFILE = {
	high: { model: "herd/gemini/gemini-3-flash-preview", thinking: "off" },
	medium: { model: "herd/beellama/qwen-flash-128k", thinking: "off" },
	low: { model: "herd/beellama/exaone-4-0-1-2b-iq4xs", thinking: "off" },
};

const modelRegistry: any = {
	find(provider: string, modelId: string) {
		if (provider !== "herd") return undefined;
		return {
			id: modelId,
			provider,
			modelId,
			baseUrl: "http://127.0.0.1:25100/v1",
			api: "openai-completions",
			headers: {},
			compat: { streamIdleTimeoutMs: 60000 },
			cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
		};
	},
	getApiKey: async (_m: any) => "none",
};

// Long-context needle prompt: ~45 filler paragraphs, needle buried at ~70%.
function buildLongCtx(): string {
	const topics = [
		"River deltas form where sediment-laden water meets a slower body, creating fan-shaped deposits over centuries.",
		"The quick red fox avoided the lazy hound by darting through the tall grass near the old stone wall.",
		"Photosynthesis converts carbon dioxide and water into glucose using chlorophyll and sunlight.",
		"Ancient mariners navigated by the stars, memorizing constellations that marked seasonal changes.",
		"Concrete cures through hydration, a chemical reaction that continues strengthening it for decades.",
		"Bees communicate hive locations through an intricate waggle dance encoding direction and distance.",
		"The printing press democratized knowledge by making books affordable to the emerging middle class.",
		"Glaciers carve valleys through slow abrasion, leaving U-shaped profiles and scattered erratics.",
		"Morse code encodes letters as dots and dashes, once the backbone of long-distance telegraphy.",
		"The human eye resolves about one arcminute, roughly the width of a coin at arm's length.",
	];
	const filler: string[] = [];
	for (let i = 0; i < 45; i++)
		filler.push(`Paragraph ${i + 1}: ${topics[i % topics.length]} Additional context fills this section with routine operational notes and background material for the quarterly review cycle.`);
	filler.splice(32, 0, "Paragraph 33: Internal memo — the project codename is BLUEBIRD. Do not share this outside the team.");
	return filler.join("\n\n") + "\n\nQuestion: What is the project codename? Reply with just the codename.";
}

const spec = JSON.parse(await fs.readFile(promptsFile, "utf8"));
for (const p of spec.prompts) if (p.text === "__LONGCTX__") p.text = buildLongCtx();

async function warmModels() {
	for (const [tier, ref] of Object.entries({
		high: "gemini/gemini-3-flash-preview",
		medium: "beellama/qwen-flash-128k",
		low: "beellama/exaone-4-0-1-2b-iq4xs",
	})) {
		const m = modelRegistry.find("herd", ref);
		const ac = new AbortController();
		const t = setTimeout(() => ac.abort(), 90000);
		try {
			const s: any = streamSimple(
				m,
				{ messages: [{ role: "user", content: "Reply with exactly: WARM", timestamp: Date.now() }] },
				{ apiKey: "none", headers: {}, signal: ac.signal, maxTokens: 5 },
			);
			for await (const _ of s) { /* drain */ }
			console.error(`warm ${tier} ok`);
		} catch (e: any) {
			console.error(`warm ${tier} FAILED: ${String(e?.message ?? e).slice(0, 120)}`);
		} finally {
			clearTimeout(t);
		}
	}
}

async function serveTauModel(modelId: string, prompt: string) {
	const m = modelRegistry.find("herd", modelId);
	const ac = new AbortController();
	const t = setTimeout(() => ac.abort(), 180000);
	const t0 = Date.now();
	let text = "";
	let usage: any = null;
	let firstTokenMs: number | null = null;
	let error: string | null = null;
	try {
		const s: any = streamSimple(
			m,
			{ messages: [{ role: "user", content: prompt, timestamp: Date.now() }] },
			{ apiKey: "none", headers: {}, signal: ac.signal, maxTokens },
		);
		for await (const ev of s) {
			const e: any = ev;
			if (e.type === "text_delta") {
				if (firstTokenMs === null) firstTokenMs = Date.now() - t0;
				text += e.delta;
			} else if (e.type === "done") {
				usage = e.message?.usage ?? null;
			} else if (e.type === "error") {
				error = `${e.reason ?? "error"}: ${(e.errorMessage ?? "").slice(0, 200)}`;
			}
		}
	} catch (e: any) {
		error = `threw: ${String(e?.message ?? e).slice(0, 200)}`;
	} finally {
		clearTimeout(t);
	}
	return { text, ms: Date.now() - t0, firstTokenMs, usage, error };
}

async function serveSovereign(prompt: string) {
	const attempts: any[] = [];
	let final: any = null;
	for (let a = 0; a <= retries; a++) {
		const t0 = Date.now();
		try {
			const r = await fetch("http://127.0.0.1:25104/v1/chat/completions", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					model: "sovereign/free",
					messages: [{ role: "user", content: prompt }],
					max_tokens: maxTokens,
				}),
				signal: AbortSignal.timeout(120000),
			});
			const ms = Date.now() - t0;
			const body: any = await r.json().catch(() => null);
			const att = {
				attempt: a, http: r.status, ms,
				model: body?.model ?? null,
				text: body?.choices?.[0]?.message?.content ?? null,
				usage: body?.usage ?? null,
				errBody: r.status >= 400 ? JSON.stringify(body)?.slice(0, 300) : null,
			};
			attempts.push(att);
			if (r.status < 500) {
				final = att;
				break;
			}
			// 5xx: retry after a short backoff (documented; availability is scored separately)
			await new Promise((r2) => setTimeout(r2, 2000 * (a + 1)));
		} catch (e: any) {
			attempts.push({ attempt: a, http: -1, ms: Date.now() - t0, error: String(e?.message ?? e).slice(0, 200) });
			await new Promise((r2) => setTimeout(r2, 2000 * (a + 1)));
		}
	}
	return { attempts, final };
}

const results: any = {
	bakeoff: spec.bakeoff,
	startedAt: new Date().toISOString(),
	config: { legs, retries, maxTokens, profile: PROFILE },
	trials: [],
};

if (legs.includes("tau")) await warmModels();

for (const p of spec.prompts) {
	const trial: any = { promptId: p.id, prompt: p.id === "longctx" ? "<longctx needle prompt>" : p.text, check: p.check };
	if (legs.includes("tau")) {
		const context: any = { messages: [{ role: "user", content: p.text, timestamp: Date.now() }] };
		const t0 = Date.now();
		let decision: any = null;
		let routeError: string | null = null;
		try {
			decision = await resolveRouting(
				{ context, previousDecision: undefined, isBudgetExceeded: false, modelRegistry },
				{
					profileName: "bakeoff",
					profile: PROFILE as any,
					phaseBias: 0.5,
					classifierModel: "herd/beellama/qwen-flash-128k",
					calibrationConfig: { enabled: true, mode: "adaptive", warmupTurns: 0, traceEnabled: false } as any,
					debug: false,
				},
			);
		} catch (e: any) {
			routeError = String(e?.message ?? e).slice(0, 300);
		}
		const routeMs = Date.now() - t0;
		const rawTarget: string = decision?.targetModelId ?? "";
		const targetModel = rawTarget.replace(/^herd\//, "");
		const served = targetModel ? await serveTauModel(targetModel, p.text) : { text: "", ms: 0, firstTokenMs: null, usage: null, error: "no target model" };
		trial.tau = {
			tier: decision?.tier ?? null,
			targetProvider: decision?.targetProvider ?? null,
			targetModel: rawTarget || null,
			isHeuristic: decision?.isHeuristic ?? null,
			reasoning: decision?.reasoning ? String(decision.reasoning).slice(0, 200) : null,
			routeMs, routeError,
			serveMs: served.ms, firstTokenMs: served.firstTokenMs,
			text: served.text, usage: served.usage, serveError: served.error,
		};
	}
	if (legs.includes("sovereign")) {
		const sov = await serveSovereign(p.text);
		trial.sovereign = sov;
	}
	results.trials.push(trial);
	console.error(`trial ${p.id} done`);
}

results.finishedAt = new Date().toISOString();
await fs.mkdir("results", { recursive: true });
await fs.writeFile(outFile, JSON.stringify(results, null, 1));
console.error(`wrote ${outFile}`);
