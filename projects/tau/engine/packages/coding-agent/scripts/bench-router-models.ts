#!/usr/bin/env bun
/**
 * Router chat-completion model benchmark (nightly suite 6).
 *
 * Sends 5 small fixed prompts (deterministic checkable answers) to each of
 * ~6 representative models through the Sovereign Router (:25104), streaming
 * so we can measure time-to-first-token plus total latency.
 *
 * Model selection honors the budget rule: FREE models first (local
 * llama-swap lanes + :free cloud pool), paid only via ROUTER_BENCH_MODELS
 * override where they add real coverage signal.
 *
 * Output is parseable, one line per model:
 *   MODEL <id> via=<provider/model> ttft_ms=… total_ms=… nonempty=x/y correct=a/b
 *   MODEL <id> SKIP <reason>
 * (`via` is the X-Routed-Via header: the provider/model that actually served
 * the request — the router may substitute, and the benchmark shows it.)
 * A JSON report is written to --out for run-over-run comparison.
 *
 * Graceful degradation: unreachable router or failing models record SKIP,
 * never a hard failure — the nightly harness stays green.
 *
 * Usage:
 *   bun scripts/bench-router-models.ts
 *   bun scripts/bench-router-models.ts --out /home/toxic/bench-router-models-latest.json
 *   ROUTER_BENCH_MODELS="fast,openai/gpt-oss-20b:free" bun scripts/bench-router-models.ts
 *   ROUTER_URL=http://127.0.0.1:25104 bun scripts/bench-router-models.ts
 */
import * as os from "node:os";
import * as path from "node:path";

const ROUTER_URL = process.env.ROUTER_URL ?? "http://127.0.0.1:25104";
// Free-first default set: 3 local llama-swap lanes (always free) + 3 diverse
// :free cloud models. Paid models can be added via ROUTER_BENCH_MODELS when
// they add coverage the free set cannot provide.
const DEFAULT_MODELS = [
	"fast",
	"quality",
	"longctx",
	"inclusionai/ling-3.0-flash-fin:free",
	"openai/gpt-oss-20b:free",
	"moonshotai/kimi-k2:free",
];

interface BenchPrompt {
	id: string;
	text: string;
	/** expected answer, matched case-insensitively as a substring */
	expect: string;
}

const PROMPTS: BenchPrompt[] = [
	{ id: "arith", text: "What is 17 * 23? Reply with just the number.", expect: "391" },
	{
		id: "reverse",
		text: "Reverse this string and reply with only the reversed string: tokamak",
		expect: "kamakot",
	},
	{
		id: "echo",
		text: "Reply with exactly this word and nothing else: QUARTZ",
		expect: "quartz",
	},
	{
		id: "capital",
		text: "What is the capital of Australia? Reply with just the city name.",
		expect: "canberra",
	},
	{
		id: "vowels",
		text: 'How many vowels (a, e, i, o, u) are in the word "benchmarking"? Reply with just the number.',
		expect: "3",
	},
];

const REQUEST_TIMEOUT_MS = 90_000;
const MAX_TOKENS = 64;

interface Sample {
	promptId: string;
	ttftMs: number | null;
	totalMs: number;
	text: string;
	/** X-Routed-Via header: the provider/model that actually served the request */
	via: string | null;
	nonempty: boolean;
	correct: boolean;
	error?: string;
}

interface ModelResult {
	model: string;
	samples: Sample[];
	skipped?: string;
}

/** POST one streaming chat completion; returns per-sample timing + text. */
async function runSample(model: string, prompt: BenchPrompt): Promise<Sample> {
	const started = performance.now();
	let ttftMs: number | null = null;
	let text = "";
	let via: string | null = null;
	let error: string | undefined;
	try {
		const resp = await fetch(new URL("/v1/chat/completions", ROUTER_URL), {
			method: "POST",
			headers: { "content-type": "application/json" },
			body: JSON.stringify({
				model,
				messages: [{ role: "user", content: prompt.text }],
				max_tokens: MAX_TOKENS,
				temperature: 0,
				stream: true,
			}),
			signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
		});
		if (!resp.ok || !resp.body) {
			const bodyText = await resp.text().catch(() => "");
			error = `http_${resp.status} ${bodyText.slice(0, 160)}`;
		} else {
			via = resp.headers.get("x-routed-via");
			const reader = resp.body.getReader();
			const decoder = new TextDecoder();
			let buf = "";
			for (;;) {
				const { done, value } = await reader.read();
				if (done) break;
				buf += decoder.decode(value, { stream: true });
				let idx: number;
				while ((idx = buf.indexOf("\n\n")) >= 0) {
					const chunk = buf.slice(0, idx);
					buf = buf.slice(idx + 2);
					for (const line of chunk.split("\n")) {
						const t = line.trim();
						if (!t.startsWith("data:")) continue;
						const payload = t.slice(5).trim();
						if (payload === "[DONE]") continue;
						try {
							const evt = JSON.parse(payload);
							const delta: string =
								evt?.choices?.[0]?.delta?.content ??
								evt?.choices?.[0]?.message?.content ??
								"";
							if (delta) {
								if (ttftMs === null) ttftMs = performance.now() - started;
								text += delta;
							}
						} catch {
							/* ignore malformed SSE frames */
						}
					}
				}
			}
		}
	} catch (e) {
		error = e instanceof Error ? `${e.name}: ${e.message.slice(0, 160)}` : String(e).slice(0, 160);
	}
	const totalMs = performance.now() - started;
	const trimmed = text.trim();
	return {
		promptId: prompt.id,
		ttftMs: error ? null : ttftMs,
		totalMs: Math.round(totalMs),
		text: trimmed,
		via,
		nonempty: trimmed.length > 0,
		correct: !error && trimmed.toLowerCase().includes(prompt.expect),
		...(error ? { error } : {}),
	};
}

function parseArgs(argv: string[]): {
	models: string[];
	outPath: string;
	deadlineS: number;
} {
	const get = (flag: string): string | undefined => {
		const i = argv.indexOf(flag);
		return i >= 0 ? argv[i + 1] : undefined;
	};
	const stamp = new Date().toISOString().replace(/[:.]/g, "-");
	const envModels = (process.env.ROUTER_BENCH_MODELS ?? "")
		.split(",")
		.map((m) => m.trim())
		.filter(Boolean);
	return {
		models: envModels.length > 0 ? envModels : DEFAULT_MODELS,
		outPath: get("--out") ?? path.join(os.tmpdir(), `router-bench-${stamp}.json`),
		deadlineS: Number(get("--deadline-s") ?? 720),
	};
}

async function routerAlive(): Promise<boolean> {
	try {
		const r = await fetch(new URL("/health", ROUTER_URL), {
			signal: AbortSignal.timeout(10_000),
		});
		if (!r.ok) return false;
		const d = (await r.json()) as { status?: string };
		return d.status === "ok";
	} catch {
		return false;
	}
}

async function main(): Promise<void> {
	const { models, outPath, deadlineS } = parseArgs(Bun.argv.slice(2));
	const results: ModelResult[] = [];
	let deadlineHit = false;
	const deadline = setTimeout(() => {
		deadlineHit = true;
	}, deadlineS * 1000);

	const alive = await routerAlive();
	if (!alive) {
		console.info(`ROUTER_MODELS SKIP router-unreachable ${ROUTER_URL}`);
		for (const m of models) console.info(`MODEL ${m} SKIP router-unreachable`);
		return;
	}

	for (const model of models) {
		if (deadlineHit) {
			results.push({ model, samples: [], skipped: "deadline-exceeded" });
			console.info(`MODEL ${model} SKIP deadline-exceeded`);
			continue;
		}
		const samples: Sample[] = [];
		let modelFailed: string | null = null;
		for (const prompt of PROMPTS) {
			if (deadlineHit) break;
			const s = await runSample(model, prompt);
			samples.push(s);
			if (s.error && samples.filter((x) => x.error).length >= 3) {
				// 3 prompt-level errors in a row for this model: stop hammering it.
				modelFailed = s.error;
				break;
			}
		}
		if (modelFailed && samples.every((s) => s.error)) {
			results.push({ model, samples, skipped: modelFailed });
			console.info(`MODEL ${model} SKIP ${modelFailed}`);
			continue;
		}
		const good = samples.filter((s) => !s.error);
		const nonempty = samples.filter((s) => s.nonempty).length;
		const correct = samples.filter((s) => s.correct).length;
		const ttfts = good.map((s) => s.ttftMs).filter((t): t is number => t !== null);
		const totals = good.map((s) => s.totalMs);
		const mean = (xs: number[]): number =>
			xs.length === 0 ? 0 : Math.round(xs.reduce((a, b) => a + b, 0) / xs.length);
		const vias = good.map((s) => s.via).filter((v): v is string => !!v);
		const viaTop =
			vias.length === 0
				? "n/a"
				: [...vias.reduce((m, v) => m.set(v, (m.get(v) ?? 0) + 1), new Map<string, number>()).entries()].sort(
						(a, b) => b[1] - a[1],
					)[0][0];
		results.push({ model, samples });
		console.info(
			`MODEL ${model} via=${viaTop} ttft_ms=${mean(ttfts)} total_ms=${mean(totals)} nonempty=${nonempty}/${samples.length} correct=${correct}/${samples.length}`,
		);
		for (const s of samples) {
			if (s.error) console.info(`  [${s.promptId}] ERROR ${s.error}`);
		}
	}

	clearTimeout(deadline);
	const report = {
		generatedAt: new Date().toISOString(),
		router: ROUTER_URL,
		models,
		prompts: PROMPTS,
		results,
	};
	await Bun.write(outPath, JSON.stringify(report, null, 2));
	console.info(`Wrote ${outPath}`);
}

await main();
