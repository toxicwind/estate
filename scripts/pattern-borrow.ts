/**
 * pattern-borrow.ts — GitHub-wide pattern ranker / borrower (Bun mainline, sovereign).
 *
 * General-purpose: pass any shallow code keywords as positional args to find and
 * rank the strongest implementation patterns across the WHOLE of GitHub, then
 * borrow the top ones. Used for the pi-agent hot-reload fix (top 3: session
 * restore / durable session / hot reload) and for anything else (e.g. tiktoken).
 *
 *   F1  recency        newest repo push among top matches
 *   F2  complexity      matched-file size + modern-API token density
 *   F3  emergent        distinct repos using the pattern (prevalence)
 *   F4  stars           total stargazers across top repos
 *   F5  issues+PRs      total open issues/PRs across top repos
 *   F6  test coverage   fraction of top repos with a test dir
 *   F7  doc density     markdown mentions of the pattern in those repos
 *   F8  fork-applicable term overlap with our bug surface
 *   F9  bug-relevance   lexical closeness to reload/session/conversation
 *   F10 centrality      total forks (dependent/centrality proxy)
 *
 * CLI:
 *   bun run scripts/pattern-borrow.ts [patterns...] [--top N] [--per-page N]
 *                              [--weights k=v,...] [--interactive] [--help]
 *
 *   patterns...   override the default 8 search terms (positional)
 *   --top N       how many to print (default 8)
 *   --per-page N  GitHub results per pattern (default 5)
 *   --weights     comma list of factor=weight overrides (bugRel, stars, issues,
 *                 forks, nRepos, newest, avgSize, testFrac)
 *   --interactive re-rank live from stdin using cached fetches (type "w stars=0.3")
 *
 * Run: bun run scripts/pattern-borrow.ts "hot reload" "session restore" --top 3
 */
import { parseArgs } from "node:util";

const TOKEN = Bun.env.GITHUB_TOKEN ?? Bun.env.GH_TOKEN;
if (!TOKEN) { console.error("no GITHUB_TOKEN/GH_TOKEN"); process.exit(1); }

const API = "https://api.github.com";
const HEAD = {
	Authorization: `Bearer ${TOKEN}`,
	Accept: "application/vnd.github+json",
	"X-GitHub-Api-Version": "2022-11-28",
};

const DEFAULT_PATTERNS = [
	"hot reload", "session restore", "jsonl session", "conversation reload",
	"fs.watch", "process reload", "resume session", "durable session",
];
const BUG_TERMS = ["reload", "watch", "hot", "session", "conversation", "restore", "resume"];
const FACTORS = ["newest", "avgSize", "nRepos", "stars", "issues", "forks", "testFrac", "bugRel"] as const;
type Weight = Partial<Record<(typeof FACTORS)[number], number>>;
const DEFAULT_W: Weight = { newest: 0.10, avgSize: 0.10, nRepos: 0.12, stars: 0.14, issues: 0.12, forks: 0.08, testFrac: 0.06, bugRel: 0.28 };

const { values, positionals } = parseArgs({
	args: Bun.argv.slice(2),
	options: {
		top: { type: "string" },
		perPage: { type: "string" },
		weights: { type: "string" },
		interactive: { type: "boolean" },
		help: { type: "boolean" },
	},
	allowPositionals: true,
});

if (values.help) {
	console.log(`Usage: bun run pattern-borrow.ts [patterns...] [--top N] [--per-page N] [--weights k=v,...] [--interactive]`);
	process.exit(0);
}

const PATTERNS = positionals.length ? positionals : DEFAULT_PATTERNS;
const TOP = Number(values.top ?? PATTERNS.length);
const PER_PAGE = Number(values.perPage ?? 5);
const W: Weight = { ...DEFAULT_W };
if (values.weights) {
	for (const kv of values.weights.split(",")) {
		const [k, v] = kv.split("=");
		if (k && v && k in DEFAULT_W) (W as any)[k] = Number(v);
	}
}

async function gh(path: string, params?: Record<string, string>): Promise<any> {
	let url = `${API}${path}`;
	if (params) url += "?" + new URLSearchParams(params).toString();
	for (let attempt = 0; attempt < 6; attempt++) {
		const res = await fetch(url, { headers: HEAD });
		if (res.status === 403 && res.headers.get("x-ratelimit-remaining") === "0") {
			const reset = Number(res.headers.get("x-ratelimit-reset") ?? "0");
			const wait = Math.max(1, reset - Math.floor(Date.now() / 1000));
			console.error(`  rate limit; sleeping ${wait}s`);
			await Bun.sleep(wait * 1000 + 500);
			continue;
		}
		if (!res.ok) { console.error(`  ! ${res.status} ${url}`); return null; }
		return await res.json();
	}
	return null;
}

async function repoStats(full: string): Promise<any> {
	const r = await gh(`/repos/${full}`);
	if (!r) return { stars: 0, issues: 0, forks: 0, pushed: 0, hasTest: 0 };
	let hasTest = 0;
	const root = await gh(`/repos/${full}/contents/`);
	if (root && Array.isArray(root)) {
		const names = root.map((x: any) => x.name);
		hasTest = names.some((n: string) => ["tests", "test", "__tests__", "spec"].includes(n)) ? 1 : 0;
	}
	return { stars: r.stargazers_count ?? 0, issues: r.open_issues_count ?? 0, forks: r.forks_count ?? 0, pushed: r.pushed_at ? Date.parse(r.pushed_at) / 1000 : 0, hasTest };
}

const rows: any[] = [];
for (const term of PATTERNS) {
	const data = await gh("/search/code", { q: term, per_page: String(PER_PAGE) });
	const repos: Record<string, any> = {};
	const sizes: number[] = [];
	if (data?.items) {
		for (const it of data.items) {
			const full = it.repository?.full_name;
			if (full && !repos[full]) repos[full] = await repoStats(full);
			if (typeof it.size === "number") sizes.push(it.size);
		}
	}
	const vals = Object.values(repos);
	const nRepos = vals.length;
	const totalStars = vals.reduce((a: number, v: any) => a + v.stars, 0);
	const totalIssues = vals.reduce((a: number, v: any) => a + v.issues, 0);
	const totalForks = vals.reduce((a: number, v: any) => a + v.forks, 0);
	const pushed = vals.map((v: any) => v.pushed).filter((x: number) => x > 0);
	const newest = pushed.length ? Math.max(...pushed) : 0;
	const testFrac = nRepos ? vals.reduce((a: number, v: any) => a + v.hasTest, 0) / nRepos : 0;
	const avgSize = sizes.length ? sizes.reduce((a: number, b: number) => a + b, 0) / sizes.length : 0;
	const bugRel = BUG_TERMS.reduce((a: number, t: string) => a + (term.toLowerCase().match(new RegExp(t, "g"))?.length ?? 0), 0);
	rows.push({ term, nRepos, stars: totalStars, issues: totalIssues, forks: totalForks, newest, testFrac, avgSize, bugRel });
	console.log(`  scanned '${term}': ${nRepos} repos, ${totalStars} stars`);
	await Bun.sleep(1200);
}

function norm(key: string) {
	const vals = rows.map((r) => r[key]);
	const mx = Math.max(...vals) || 1;
	const mn = Math.min(...vals);
	const rng = mx - mn || 1;
	for (const r of rows) r[`n_${key}`] = (r[key] - mn) / rng;
}

function rank(weights: Weight) {
	for (const k of FACTORS) norm(k);
	const wsum = FACTORS.reduce((a, k) => a + (weights[k] ?? 0), 0) || 1;
	for (const r of rows) r.score = FACTORS.reduce((a, k) => a + (r[`n_${k}`] ?? 0) * (weights[k] ?? 0), 0) / wsum;
	rows.sort((a: any, b: any) => b.score - a.score);
}

function printRank(weights: Weight) {
	rank(weights);
	console.log("\n=== RANKED PATTERNS (GitHub-wide) ===");
	console.log("score  bug  repos  stars   iss  test  term");
	for (const r of rows.slice(0, TOP)) {
		console.log(
			`${(r.score * 100).toFixed(1).padStart(5)} ${String(r.bugRel).padStart(3)} ${String(r.nRepos).padStart(5)} ` +
			`${String(r.stars).padStart(7)} ${String(r.issues).padStart(5)} ${r.testFrac.toFixed(2)}  ${r.term}`,
		);
	}
	console.log(`\nTOP ${Math.min(TOP, 3)} TO MERGE:`);
	for (const r of rows.slice(0, Math.min(TOP, 3))) console.log(`  - ${r.term}`);
}

printRank(W);

if (values.interactive) {
	console.log("\ninteractive: type 'w factor=weight' (e.g. 'w bugRel=0.4'), 'p' to reprint, 'q' quit");
	const buf = (await import("node:tty")).stdin;
	buf?.on?.("data", (d: Buffer) => {
		const line = d.toString().trim();
		if (line === "q") process.exit(0);
		if (line === "p") return printRank(W);
		const m = line.match(/^w\s+(\w+)=([\d.]+)$/);
		if (m && (m[1] as any) in DEFAULT_W) { (W as any)[m[1]] = Number(m[2]); printRank(W); }
	});
}
