/**
 * forge — one CLI over every leg. `forge help` is the whole surface.
 *
 * Subcommands map 1:1 onto the doctrine:
 *   retrieve  find the code you already own        (ast-bm25-racer + ast_indexer)
 *   race      run contenders, first valid wins     (hft-latency race.py)
 *   bench     nanosecond leaderboard               (code_racer.py)
 *   borrow    free-first literature + code search  (emergent-enrich route.py)
 *   mcts      search patch candidates              (mcts_engine.py)
 *   subgraph  traceback -> files that matter       (dynamic_subgraph_inducer.py)
 *   audit     verify claims against the AST          (ast-grep; merged 2026-10-02)
 *   paths     what this build resolves to          (non-hardcoded path proof)
 *   doctor    verify every leg still runs
 *   hf        HuggingFace model finder + zero-shot classifier
 *             (search/models | classify | find-classifier) — raw Bun, pure-Bun
 *             offline fallback when HF serverless is 402-gated
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { Bm25Index } from "./bm25";
import { buildIndex, collectFiles } from "./repo-index";
import { CODE_EXTS, PY_EXTS, extract } from "./extract";
import { CodeRacer } from "./code-racer";
import { CircuitBreaker } from "./circuit-breaker";
import { SWEMcts, type PatchAction } from "./mcts";
import { DynamicSubgraphInducer, extractTracebackFrames } from "./subgraph";
import { borrow, renderBorrow, type SourceName } from "./borrow";
import { audit, renderAudit, resolveAstGrep, type AuditOptions } from "./audit";
import { leadWithWinner, loadStrategies, logWinners, runRace, setEmitter, type Strategy } from "./concurrent";
import { CodeItem, PaperItem } from "./providers";
import * as P from "./paths";
import * as hf from "./hf";

type Args = { _: string[]; flags: Map<string, string | boolean> };

function parseArgs(argv: readonly string[]): Args {
  const _: string[] = [];
  const flags = new Map<string, string | boolean>();
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i]!;
    if (!token.startsWith("--")) {
      _.push(token);
      continue;
    }
    const key = token.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) {
      flags.set(key, true);
    } else {
      flags.set(key, next);
      i++;
    }
  }
  return { _, flags };
}

const num = (flags: Args["flags"], key: string, fallback: number): number => {
  const raw = flags.get(key);
  const parsed = typeof raw === "string" ? Number(raw) : NaN;
  return Number.isFinite(parsed) ? parsed : fallback;
};

const str = (flags: Args["flags"], key: string, fallback: string): string => {
  const raw = flags.get(key);
  return typeof raw === "string" ? raw : fallback;
};

const list = (flags: Args["flags"], key: string): string[] => {
  const raw = flags.get(key);
  return typeof raw === "string" && raw ? raw.split(",").map((s) => s.trim()).filter(Boolean) : [];
};

function writeOut(flags: Args["flags"], payload: unknown, rendered: string): void {
  const out = flags.get("out");
  if (typeof out === "string" && out) {
    mkdirSync(dirname(resolve(out)), { recursive: true });
    writeFileSync(out, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
    process.stderr.write(`wrote ${out}\n`);
  }
  if (flags.get("quiet") === true) return;
  process.stdout.write(`${rendered}\n`);
}

async function cmdRetrieve(args: Args): Promise<number> {
  const root = resolve(str(args.flags, "root", args._[0] ?? P.RANCH));
  const query = str(args.flags, "query", args._[1] ?? "");
  if (!query) {
    process.stderr.write("retrieve needs a query: forge retrieve --root <dir> --query 'symbols or words'\n");
    return 2;
  }
  const topK = num(args.flags, "top", 10);
  const t0 = performance.now();
  const { index, stats } = await buildIndex(root, { maxFiles: num(args.flags, "max-files", 60_000) });
  const buildMs = performance.now() - t0;

  const t1 = performance.now();
  const hits = index.hybrid(query, topK);
  const queryMs = performance.now() - t1;

  const width = Math.max(...hits.map((h) => h.path.length), 10);
  const lines = [
    `=== Retrieve: ${stats.files} files / ${(stats.bytes / 1e6).toFixed(1)} MB in ${buildMs.toFixed(0)}ms ` +
      `(walked ${stats.dirsWalked} dirs, pruned ${stats.dirsPruned}${stats.truncated ? ", TRUNCATED (raise --max-files)" : ""}) ===`,
    `=== query "${query}" in ${queryMs.toFixed(2)}ms ===`,
  ];
  for (const [i, hit] of hits.entries()) {
    lines.push(`${String(i + 1).padStart(2)}. ${hit.path.padEnd(width)}  ${hit.hybrid.toFixed(2)}  bm25=${hit.bm25.toFixed(2)}`);
    if (hit.symbols.length) lines.push(`    ${hit.symbols.slice(0, 8).join(", ")}`);
  }
  if (!hits.length) lines.push("  (no matches)");
  writeOut(args.flags, { root, query, buildMs, queryMs, stats, hits }, lines.join("\n"));
  return 0;
}

async function cmdRace(args: Args): Promise<number> {
  const specPath = str(args.flags, "strategies", args._[0] ?? "");
  if (!specPath || !existsSync(specPath)) {
    process.stderr.write('race needs a strategies file: forge race --strategies r.json --tag mytag\n  e.g. {"strategies":[{"name":"a","cmd":["bun","run","a.ts"],"match":"OK"}]}\n');
    return 2;
  }
  const strategies = loadStrategies(specPath);
  const tag = str(args.flags, "tag", "default");
  const timeoutS = num(args.flags, "timeout", 60);
  const raceTimeoutS = num(args.flags, "race-timeout", timeoutS + 5);
  const hedgeMs = num(args.flags, "hedge-ms", 0);

  if (args.flags.get("lead") === true) {
    const ranked = leadWithWinner(tag, strategies);
    process.stdout.write(`=== lead-with-winner: ${tag} ===\n`);
    for (const [i, row] of ranked.ranked.entries()) {
      process.stdout.write(`${String(i + 1).padStart(2)}. ${row.name}  wins=${row.wins}  median=${row.medianLatencyS.toFixed(3)}s\n`);
    }
    return 0;
  }

  const raceId = `${tag}-${Date.now().toString(36)}`;
  const outcome = await runRace(strategies, { raceId, tag, timeoutS, raceTimeoutS, hedgeMs });
  const latency: Record<string, { latency_s: number }> = {};
  for (const [name, r] of Object.entries(outcome.results)) latency[name] = { latency_s: r.latencyS };
  if (outcome.winner) logWinners(tag, outcome.winner, latency);

  const lines = [`=== Race ${raceId} (tag=${tag}, hedge=${hedgeMs}ms) ===`];
  for (const [name, r] of Object.entries(outcome.results)) {
    lines.push(`  ${name.padEnd(16)} ${r.valid ? "VALID  " : "invalid"} ${r.latencyS.toFixed(3)}s${r.error ? `  ${r.error}` : ""}`);
  }
  for (const name of strategies.map((s) => s.name)) {
    if (!outcome.results[name]) lines.push(`  ${name.padEnd(16)} cancelled (lost the race)`);
  }
  lines.push(outcome.winner ? `winner: ${outcome.winner}` : "winner: none — every contestant failed or timed out");
  if (outcome.winner && args.flags.get("stdout") === true) lines.push("", outcome.winnerOutput);

  writeOut(args.flags, { raceId, tag, hedgeMs, winner: outcome.winner, results: outcome.results }, lines.join("\n"));
  return outcome.winner ? 0 : 1;
}

async function cmdBench(args: Args): Promise<number> {
  const warmup = num(args.flags, "warmup", 5);
  const runs = num(args.flags, "runs", 50);
  const racer = new CodeRacer(warmup, runs);

  let candidates: Array<{ name: string; impl: () => unknown }>;
  const candFile = args.flags.get("candidates");
  if (typeof candFile === "string" && candFile) {
    let parsed: unknown;
    try {
      parsed = await Bun.file(candFile).json();
    } catch (e) {
      process.stderr.write(`bench: cannot read --candidates file '${candFile}': ${(e as Error).message}\n`);
      return 2;
    }
    const rows = (parsed as { candidates?: Array<{ name?: unknown; code?: unknown }> })?.candidates;
    if (!Array.isArray(rows) || rows.length === 0) {
      process.stderr.write(`bench: --candidates file must be {"candidates":[{"name","code"},...]}\n`);
      return 2;
    }
    candidates = [];
    for (const row of rows) {
      if (typeof row.name !== "string" || typeof row.code !== "string" || !row.name || !row.code) {
        process.stderr.write(`bench: skipping malformed candidate ${JSON.stringify(row).slice(0, 80)}\n`);
        continue;
      }
      let impl: () => unknown;
      try {
        impl = new Function(`"use strict"; return (${row.code});`) as () => unknown;
      } catch (e) {
        process.stderr.write(`bench: skipping candidate '${row.name}': code does not compile: ${(e as Error).message}\n`);
        continue;
      }
      candidates.push({ name: row.name, impl });
    }
    if (!candidates.length) {
      process.stderr.write("bench: no usable candidates after validation\n");
      return 2;
    }
  } else {
    candidates = [
      { name: "array-index-of", impl: (): number => [1, 2, 3, 4, 5].indexOf(4) },
      { name: "includes", impl: (): boolean => [1, 2, 3, 4, 5].includes(4) },
      { name: "find", impl: (): number | undefined => [1, 2, 3, 4, 5].find((n) => n === 4) },
      { name: "sort", impl: (): number[] => [5, 4, 3, 2, 1].sort((a, b) => a - b) },
      { name: "tokenize-100", impl: (): number => "aBcDeFgHiJ".toLowerCase().split(/[_]|(?<=[a-z0-9])(?=[A-Z])/).length },
    ];
  }
  const result = racer.race(candidates);
  const rendered = racer.printLeaderboard(result);
  writeOut(args.flags, result, rendered);
  return 0;
}

async function cmdBorrow(args: Args): Promise<number> {
  const query = str(args.flags, "query", args._[0] ?? "");
  if (!query) {
    process.stderr.write('borrow needs a query: forge borrow "agent memory eviction"\n');
    return 2;
  }
  const skip = new Set<SourceName>(list(args.flags, "skip") as SourceName[]);
  const result = await borrow(query, {
    perSource: num(args.flags, "per-source", 5),
    skip,
    exaApiKey: str(args.flags, "exa-key", ""),
  });
  const rendered = renderBorrow(result, num(args.flags, "top", 10));
  writeOut(args.flags, result, rendered);
  return 0;
}

async function cmdSubgraph(args: Args): Promise<number> {
  const root = str(args.flags, "root", process.cwd());
  const trace = str(args.flags, "trace", "");
  if (!trace) {
    process.stderr.write("subgraph needs --trace <file> holding a python traceback\n");
    return 2;
  }
  const frames = extractTracebackFrames(readFileSync(trace, "utf8"));
  const inducer = new DynamicSubgraphInducer(root);
  const graph = inducer.induce(frames, { maxDepth: num(args.flags, "depth", 3) });
  const width = Math.max(...graph.nodes.map((n) => n.path.length), 10);
  const lines = [`=== Subgraph: ${frames.length} frames -> ${graph.nodes.length} files, ${graph.edges.length} edges (root ${root}) ===`];
  for (const node of graph.nodes) {
    const inFan = graph.fanIn.get(node.path) ?? 0;
    lines.push(`${node.inTraceback ? "*" : " "} d${node.depth} ${node.path.padEnd(width)} fanIn=${inFan}${node.symbols.length ? `  ${node.symbols.slice(0, 5).join(", ")}` : ""}`);
  }
  writeOut(args.flags, graph, lines.join("\n"));
  return 0;
}

async function cmdMcts(args: Args): Promise<number> {
  // Candidates are verification commands. Inline: --candidates "a,b,c"
  // (whitespace-split). File: --candidates-file c.json as
  // {"candidates":[{"name":"t","cmd":["bun","test","t.ts"]},...]}.
  type Cand = { name: string; cmd: string[] };
  let cands: Cand[] = [];
  const candFile = args.flags.get("candidates-file");
  if (typeof candFile === "string" && candFile) {
    let parsed: unknown;
    try {
      parsed = await Bun.file(candFile).json();
    } catch (e) {
      process.stderr.write(`mcts: cannot read --candidates-file '${candFile}': ${(e as Error).message}\n`);
      return 2;
    }
    const rows = (parsed as { candidates?: Array<{ name?: unknown; cmd?: unknown }> })?.candidates;
    if (!Array.isArray(rows)) {
      process.stderr.write(`mcts: --candidates-file must be {"candidates":[{"name","cmd":[...]},...]}\n`);
      return 2;
    }
    for (const row of rows) {
      if (typeof row.name === "string" && Array.isArray(row.cmd) && row.cmd.every((c) => typeof c === "string")) {
        cands.push({ name: row.name, cmd: row.cmd });
      } else {
        process.stderr.write(`mcts: skipping malformed candidate ${JSON.stringify(row).slice(0, 80)}\n`);
      }
    }
  } else {
    const names = list(args.flags, "candidates");
    cands = names.map((n) => ({ name: n, cmd: n.split(/\s+/).filter(Boolean) }));
  }
  cands = cands.filter((c) => c.cmd.length > 0);
  if (!cands.length) {
    process.stderr.write("mcts needs --candidates a,b,c or --candidates-file c.json\n");
    return 2;
  }
  const actions: PatchAction[] = cands.map((c) => ({ actionId: c.name, patch: JSON.stringify(c.cmd) }));
  const real = args.flags.get("real") === true;
  const timeoutS = num(args.flags, "timeout", 60);
  const engine = new SWEMcts(num(args.flags, "depth", 4), num(args.flags, "timeout", 60));
  const result = await engine.search(
    async () => actions,
    async (node) => {
      if (!real) return node.stateId === "root" ? 0 : 1;
      if (!node.action) return 0;
      let cmd: string[];
      try {
        cmd = JSON.parse(node.action.patch) as string[];
      } catch {
        cmd = node.action.actionId.split(/\s+/).filter(Boolean);
      }
      return await runRealTest(cmd, timeoutS);
    },
  );
  const lines = [
    `=== MCTS: ${result.iterations} iterations, ${result.nodesExplored} nodes, ${result.elapsedS.toFixed(3)}s${result.timedOut ? " (timed out)" : ""} ===`,
    `best: ${result.bestPatch ?? "(none)"} via ${result.bestStateId ?? "-"}`,
  ];
  writeOut(args.flags, result, lines.join("\n"));
  return 0;
}

async function cmdAudit(args: Args): Promise<number> {
  const opts: AuditOptions = {
    root: args.flags.get("root") as string || process.cwd(),
    globs: list(args.flags, "globs"),
    top: num(args.flags, "top", 10),
    claim: args.flags.get("claim") as string | undefined,
    pattern: args.flags.get("pattern") as string | undefined,
    lang: args.flags.get("lang") as string | undefined,
    rule: args.flags.get("rule") as string | undefined,
  };
  const result = audit(opts);
  const rendered = renderAudit(result);
  writeOut(args.flags, result, rendered);
  return result.verdict === "VERIFIED" ? 0 : result.verdict === "NOT-FOUND" ? 1 : 2;
}

/** Reward from a real verification command; +1 pass, -1 fail, -1 timeout. */
async function runRealTest(cmd: readonly string[], timeoutS: number): Promise<number> {
  const [bin, ...argv] = cmd;
  if (!bin) return -1;
  try {
    const proc = Bun.spawn([bin, ...argv], {
      stdout: "ignore",
      stderr: "ignore",
      stdin: "ignore",
      timeout: timeoutS * 1000,
      killSignal: "SIGKILL",
    });
    return (await proc.exited) === 0 ? 1 : -1;
  } catch {
    return -1;
  }
}

function cmdPaths(_args: Args): number {
  const rows: [string, string][] = [
    ["ESTATE", P.ESTATE], ["RANCH", P.RANCH], ["VENDORED", P.VENDORED], ["VAR", P.VAR],
    ["MANOR", P.MANOR], ["SKILLS_HOME", P.SKILLS_HOME], ["TAU_DIR", P.TAU_DIR],
    ["PORTS_ENV", P.PORTS_ENV], ["KNOWLEDGEBASE", P.KNOWLEDGEBASE],
  ];
  const width = Math.max(...rows.map(([k]) => k.length));
  const lines = ["=== resolved paths (env override -> skill-marker discovery -> candidate probe -> honest miss) ==="];
  for (const [key, value] of rows) {
    const rendered = value === ""
      ? "(unset — no estate checkout on this host)"
      : `${value}  ${existsSync(value) ? "" : "(MISSING)"}`;
    lines.push(`${key.padEnd(width)}  ${rendered}`);
  }
  lines.push("--- estate candidate probe ---");
  for (const r of P.probeEstate()) {
    lines.push(`  ${r.candidate}  ${r.exists ? "exists" : "missing"}${r.selected ? "  [selected]" : ""}`);
  }
  process.stdout.write(`${lines.join("\n")}\n`);
  return rows.every(([, v]) => existsSync(v)) ? 0 : 1;
}

async function cmdDoctor(args: Args): Promise<number> {
  const checks: { name: string; ok: boolean; detail: string }[] = [];

  // Doctor speaks in its own summary lines. Leg telemetry (mcts_expand,
  // source_done, ...) would drown them — silence the emitter for the
  // duration of the checks, then restore the default stderr writer.
  setEmitter(() => {});
  try {
    const files = collectFiles(P.SKILL_DIR, { extensions: [...CODE_EXTS] }).files;
    checks.push({ name: "scan skill dir", ok: files.length > 0, detail: `${files.length} code files under ${P.SKILL_DIR}` });

    const { index, stats } = await buildIndex(P.SKILL_DIR);
    const hits = index.hybrid("race first valid winner hedge", 3);
    checks.push({ name: "retrieve", ok: hits.length > 0, detail: `${stats.files} indexed, top=${hits[0]?.path ?? "none"}` });

    const racer = new CodeRacer(2, 5);
    const raced = racer.race([{ name: "noop", impl: () => 1 }, { name: "boom", impl: (): never => { throw new Error("expected"); } }]);
    checks.push({ name: "bench", ok: raced.winner === "noop", detail: `winner=${raced.winner} rows=${raced.rows.length}` });

    const py = collectFiles(P.SKILL_DIR, { extensions: [...PY_EXTS] }).files;
    const frames = extractTracebackFrames('  File "/x/y.py", line 3, in boom\nTraceback (most recent call last):');
    checks.push({ name: "subgraph parse", ok: frames.length === 1, detail: `frames=${frames.length} pyFiles=${py.length}` });

    const mcts = new SWEMcts(2, 5);
    const searched = await mcts.search(async () => [{ actionId: "a", patch: "p" }], async () => 1);
    checks.push({ name: "mcts", ok: searched.bestPatch === "p", detail: `${searched.iterations} iters best=${searched.bestStateId}` });

    const estateOk = P.ESTATE === "" || existsSync(P.ESTATE);
    checks.push({
      name: "paths",
      ok: estateOk,
      detail: P.ESTATE === ""
        ? "no estate checkout on this host — resolver reported the miss honestly (no blessed stale dir)"
        : `ESTATE=${P.ESTATE} (probed: ${P.probeEstate().map((r) => `${r.candidate}=${r.exists ? "exists" : "missing"}${r.selected ? " [selected]" : ""}`).join(", ")})`,
    });

    const sgBin = resolveAstGrep();
    checks.push({ name: "audit (ast-grep)", ok: sgBin !== null, detail: sgBin ?? "ast-grep missing from PATH (set AST_GREP_BIN)" });

    if (args.flags.get("borrow") === true) {
      const borrowed = await borrow("mcts planning", { perSource: 1, skip: new Set(["exa"]) });
      const okCount = Object.values(borrowed.sources).filter((s) => s?.ok).length;
      checks.push({ name: "borrow (network)", ok: okCount > 0, detail: `${okCount} sources ok in ${borrowed.timingMs.toFixed(0)}ms` });
    }
  } finally {
    setEmitter((line) => process.stderr.write(`${line}\n`));
  }

  const width = Math.max(...checks.map((c) => c.name.length));
  const lines = ["=== doctor ==="];
  for (const check of checks) {
    lines.push(`${check.ok ? "PASS" : "FAIL"}  ${check.name.padEnd(width)}  ${check.detail}`);
  }
  process.stdout.write(`${lines.join("\n")}\n`);
  return checks.every((c) => c.ok) ? 0 : 1;
}

async function cmdHf(args: Args): Promise<number> {
  const sub = args._[0] ?? "search";
  const REST = args._.slice(1);

  // search <query> | models [--sort downloads] [--task zero-shot]
  if (sub === "search" || sub === "models") {
    const query = REST.join(" ");
    const sort = String(args.flags.get("sort") ?? "downloads");
    const dir = String(args.flags.get("direction") ?? "-1");
    const limit = Number(args.flags.get("limit") ?? 12);
    const task = String(args.flags.get("task") ?? "");
    const lib = String(args.flags.get("library") ?? "");
    try {
      const rows = await hf.hfSearch(query, { sort, direction: dir, limit, task, library: lib });
      if (!rows.length) {
        process.stdout.write(`HF: no models for '${query}'\n`);
        return 1;
      }
      const ranked = hf.sortByRank(rows);
      process.stdout.write(`HF search '${query}' (sort=${sort}) -> top ${rows.length} by rank:\n`);
      for (const m of ranked) {
        const score = hf.rankModel(m).toFixed(1);
        process.stdout.write(`  ${score.padStart(5)}  ${String((m.downloads ?? 0)).padStart(10)}dl ${String(m.likes ?? 0).padStart(4)}♡ ${(m.task ?? "?").padEnd(20)} ${m.id}\n`);
      }
      return 0;
    } catch (e: any) {
      process.stdout.write(`HF search failed: ${e?.message ?? e}\n`);
      return 1;
    }
  }

  // classify <text> --labels a,b,c [--models m1,m2,m3]
  if (sub === "classify") {
    const text = REST.join(" ");
    const labels = String(args.flags.get("labels") ?? "").split(",").filter(Boolean);
    const explicit = String(args.flags.get("models") ?? "").split(",").filter(Boolean);
    if (!text || !labels.length) {
      process.stdout.write(`usage: forge hf classify "<text>" --labels repo,tool,mcp,vendor --models id1,id2\n`);
      return 2;
    }
    const winners = await hf.bestClassifyModels(explicit, labels);
    let { winner, candidates, agreed } = await hf.classifyRace({ text, labels }, winners, 3);
    const okCount = candidates.filter((c) => c.verdict?.ok).length;
    if (!winner || okCount === 0) {
      const local = hf.localZeroShot(text, labels);
      process.stdout.write(`HF classify "${text.slice(0, 60)}"\n`);
      process.stdout.write(`  (serverless zero-shot 402-gated/offline — using pure-Bun local fallback; set --models to a free-inference id)\n`);
      for (const l of local) {
        process.stdout.write(`  ✓ ${l.label.padEnd(60)} ${l.score.toFixed(3)}\n`);
      }
      return local.length ? 0 : 1;
    }
    process.stdout.write(`HF classify "${text.slice(0, 60)}"\n`);
    for (const c of candidates) {
      const short = c.model.slice(0, 60);
      process.stdout.write(`  ${c.verdict?.ok ? "✓" : "✗"} ${short.padEnd(62)} ${c.verdict?.label ?? "err"}=${c.verdict?.score?.toFixed(3) ?? "―"} ${c.verdict?.ms ?? 0}ms${c.verdict?.error ? ` [${c.verdict.error}]` : ""}\n`);
    }
    process.stdout.write(`\n  consensus: ${winner || "none"} (${agreed}/${candidates.filter((c) => c.verdict?.ok).length} agree)\n`);
    return winner ? 0 : 1;
  }

  // find-classifier <text> --labels a,b [--probe "<real input>" --task zero-shot]
  if (sub === "find-classifier" || sub === "find") {
    const text = REST.join(" ");
    const labels = String(args.flags.get("labels") ?? "").split(",").filter(Boolean);
    const probe = String(args.flags.get("probe") ?? text);
    const task = String(args.flags.get("task") ?? "zero-shot");
    const pool = await hf.findClassifierCandidates(probe, labels, task, Number(args.flags.get("limit") ?? 8));
    if (!pool.length) {
      process.stdout.write("find-classifier: no candidate classifiers from HF Hub\n");
      return 1;
    }
    const winners = pool.map((m) => m.model);
    const race = await hf.classifyRace({ text: probe, labels }, winners, 3);
    let winner = race.winner;
    if (!winner) {
      const local = hf.localZeroShot(probe, labels);
      winner = local[0]?.label ?? "";
      process.stdout.write(`find-classifier: ${pool.length} candidates all 402-gated; pure-Bun fallback selects '${winner}' (score ${local[0]?.score?.toFixed(3) ?? "―"})\n`);
      for (const l of local) process.stdout.write(`  ✓ ${l.label.padEnd(12)} ${l.score.toFixed(3)}\n`);
      return winner ? 0 : 1;
    }
    process.stdout.write(`find-classifier: raced ${pool.length} candidate zero-shot models on '${probe.slice(0, 50)}'\n`);
    for (const c of race.candidates.sort((a, b) => (b.verdict?.score ?? 0) - (a.verdict?.score ?? 0))) {
      const rank = pool.find((m) => m.model === c.model)?.rank ?? 0;
      process.stdout.write(`  ${c.verdict?.ok ? "✓" : "✗"} rank${rank.toFixed(0).padStart(2)} ${c.verdict?.label?.padEnd(12)} ${(c.verdict?.score ?? 0).toFixed(3)} ${c.model}${c.verdict?.error ? ` [${c.verdict.error}]` : ""}\n`);
    }
    process.stdout.write(`\n  recommended: ${winner}\n`);
    return winner ? 0 : 1;
  }

  process.stdout.write(`forge hf subcommands: search | classify | find-classifier\n`);
  return 2;
}

const HELP = `forge — pattern-forge: retrieve, race, borrow, search. Pure Bun.

  forge retrieve --root <dir> --query <q> [--top N] [--max-files N]
  forge race --strategies <file.json> [--tag t] [--timeout S] [--race-timeout S]
              [--hedge-ms MS] [--lead] [--stdout]
  forge bench [--candidates <file.json>] [--warmup N] [--runs N]
  forge borrow <query> [--per-source N] [--skip a,b] [--top N] [--exa-key K] [--skip a,b]
  forge mcts (--candidates a,b,c | --candidates-file <c.json>) [--depth N] [--timeout S] [--real]
  forge subgraph --root <dir> --trace <file> [--depth N]
  forge hf search <query> [--sort downloads|likes|trendingScore] [--task zero-shot|embed|gen] [--limit N]
  forge hf classify <text> --labels a,b,c [--models m1,m2,m3]
  forge hf find-classifier <text> --labels a,b,c [--task zero-shot] [--limit N]
  forge audit --root <dir> --claim "<claim>" [--globs a,b] [--top N]
  forge audit --root <dir> --pattern '<ast-grep pattern>' [--lang ts] [--globs a,b]
  forge audit --root <dir> --rule <rule.yml>
  forge paths
  forge doctor [--borrow]

Strategies JSON:
  {"strategies":[{"name":"fast","cmd":["bun","run","fast.ts"],"match":"^OK"}]}

Global: --out <file> writes the JSON payload, --quiet suppresses stdout,
        --verbose restores JSONL telemetry on stderr (default: quiet).

Bench candidates JSON:
  {"candidates":[{"name":"includes","code":"\"abc\".includes(\"b\")"}]}
MCTS candidates JSON:
  {"candidates":[{"name":"t","cmd":["bun","test","t.ts"]}]}`

async function main(argv: readonly string[]): Promise<number> {
  const parsed = parseArgs(argv);
  const command = parsed._[0] ?? "help";
  // Telemetry is opt-in: --json (machine JSONL) or --verbose/FORGE_VERBOSE=1.
  // Default runs stay quiet — leg events drowned real output at MCTS scale.
  const loud =
    parsed.flags.get("json") === true ||
    parsed.flags.get("verbose") === true ||
    process.env.FORGE_VERBOSE === "1";
  setEmitter(loud ? (line) => process.stderr.write(`${line}\n`) : () => {});
  // Positionals are relative to the subcommand. Leaving the subcommand in
  // place made `forge borrow "<query>"` search for the literal word "borrow".
  const args: Args = { _: parsed._.slice(1), flags: parsed.flags };
  switch (command) {
    case "retrieve": return cmdRetrieve(args);
    case "race": return cmdRace(args);
    case "bench": return cmdBench(args);
    case "borrow": return cmdBorrow(args);
    case "mcts": return cmdMcts(args);
    case "subgraph": return cmdSubgraph(args);
    case "audit": return cmdAudit(args);
    case "paths": return cmdPaths(args);
    case "doctor": return cmdDoctor(args);
    case "hf": return cmdHf(args);
    case "help":
    default:
      process.stdout.write(`${HELP}\n`);
      return command === "help" ? 0 : 2;
  }
}

export { main };

if (import.meta.main) {
  process.exitCode = await main(process.argv.slice(2));
}

export type { Strategy };
export type BorrowPaper = PaperItem;
export type BorrowCode = CodeItem;