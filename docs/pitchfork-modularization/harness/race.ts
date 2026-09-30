#!/usr/bin/env bun
/**
 * race.ts — hyper-race the three modularization designs + monolith baseline.
 * Usage: race.ts <orig.toml> <lane-root>
 * Assumes fixtures already built by split-fixtures.ts.
 *
 * Metrics:
 *  M1 compose latency: 20 runs/design, concurrent (Promise.all), median + p95.
 *  M2 single-daemon change: edit one daemon's fragment -> re-compose; measure
 *      wall time, composed-output diff scope (changed lines), and verify all
 *      OTHER daemons render byte-identical (restart blast-radius proxy).
 *  M3 merge-conflict safety: git sim, two writers.
 *      case1: writers edit different, non-adjacent daemons.
 *      case2: writers edit adjacent daemons (neighbor lines).
 *      -> conflict? how many files/lines to resolve?
 *  M4 rollback: bad single-daemon change committed alongside 5 good ones;
 *      measure revert blast radius (files/hunks reverted) + commands needed.
 * Validity gate (every run): composed output TOML-parses AND daemon set ==
 * original daemon set. A design that can't reproduce the monolith is DQ'd.
 */
import { parseFragment, normStanza } from "./compose.ts";
import { join } from "node:path";

const [origPath, root] = process.argv.slice(2);
if (!origPath || !root) { console.error("usage: race.ts <orig.toml> <lane-root>"); process.exit(1); }

const results: any = { metrics: {} };
const now = () => performance.now();

// ---------- validity ----------
let tomlParse: (s: string) => any;
try {
  // @ts-ignore Bun.TOML exists on recent Bun
  tomlParse = Bun.TOML.parse.bind(Bun.TOML);
  tomlParse("a=1");
} catch {
  console.error("WARN: Bun.TOML.parse unavailable, falling back to section-count check");
  tomlParse = (s: string) => { if (!/^\s*\[/m.test(s)) throw new Error("no sections"); return {}; };
}

const origText = await Bun.file(origPath).text();
const origFrag = parseFragment(origPath, origText);
const origNames = [...origFrag.daemons.keys()].sort();

async function validateDesign(tag: string, composedPath: string): Promise<{ ok: boolean; detail: string }> {
  const text = await Bun.file(composedPath).text();
  try { tomlParse(text); } catch (e: any) { return { ok: false, detail: `TOML parse fail: ${e.message}` }; }
  const f = parseFragment(composedPath, text);
  const names = [...f.daemons.keys()].sort();
  const same = names.length === origNames.length && names.every((n, i) => n === origNames[i]);
  if (!same) return { ok: false, detail: `daemon set mismatch: got ${names.length}, want ${origNames.length}` };
  // stanza-level fidelity: every daemon's stanza must match the original's
  // (trailing-blank-insensitive: separators are layout, not config)
  for (const n of origNames) {
    const a = normStanza(origFrag.daemons.get(n)!).join("\n");
    const b = normStanza(f.daemons.get(n) ?? []).join("\n");
    if (a !== b) return { ok: false, detail: `stanza drift for [${n}]` };
  }
  return { ok: true, detail: `${names.length} daemons, stanzas identical` };
}

// ---------- M1: compose latency, raced concurrently ----------
const DESIGNS = [
  { tag: "A", cli: join(root, "proto-a/pf-merge.ts"), dir: join(root, "proto-a") },
  { tag: "B", cli: join(root, "proto-b/pf-build.ts"), dir: join(root, "proto-b") },
  { tag: "C", cli: join(root, "proto-c/pf-collect.ts"), dir: join(root, "proto-c") },
];

async function runCli(d: (typeof DESIGNS)[number]): Promise<number> {
  const t0 = now();
  const p = Bun.spawn(["bun", d.cli, d.dir], { stdout: "pipe", stderr: "pipe" });
  const [out, err, code] = await Promise.all([new Response(p.stdout).text(), new Response(p.stderr).text(), p.exited]);
  const dt = now() - t0;
  if (code !== 0) throw new Error(`design ${d.tag} compose failed: ${err.slice(0, 200)}`);
  return dt;
}

const M1: Record<string, number[]> = { A: [], B: [], C: [] };
const RUNS = 20;
for (let r = 0; r < RUNS; r++) {
  // all three in flight at once — the race IS the retry policy
  const [a, b, c] = await Promise.all(DESIGNS.map(runCli));
  M1.A.push(a); M1.B.push(b); M1.C.push(c);
}
const pct = (xs: number[], p: number) => { const s = [...xs].sort((x, y) => x - y); return +s[Math.min(s.length - 1, Math.floor(p * s.length))].toFixed(2); };
const med = (xs: number[]) => pct(xs, 0.5);
results.metrics.M1_compose_ms = Object.fromEntries(
  Object.entries(M1).map(([k, v]) => [k, { median: med(v), p95: pct(v, 0.95), runs: v.length }])
);

// validity gate on the composed outputs
results.validity = {};
for (const d of DESIGNS) {
  results.validity[d.tag] = await validateDesign(d.tag, join(d.dir, "pitchfork.composed.toml"));
}

// ---------- M2: single-daemon change propagation ----------
// pick a daemon in the middle of the sorted list that actually has a port line
const withPort = origNames.filter((n) =>
  /^\s*port\s*=\s*\d+/m.test(origFrag.daemons.get(n)!.join("\n")));
const target = withPort[Math.floor(withPort.length / 2)];
const targetFile: Record<string, string> = {
  A: join(root, "proto-a/pitchfork.d", (await findFragmentFile(join(root, "proto-a/pitchfork.d"), target))!),
  B: join(root, "proto-b/daemons.d", `${target.replace(/[^a-zA-Z0-9_.-]/g, "_")}.toml`),
  C: "", // resolved below
};
async function findFragmentFile(dir: string, daemon: string): Promise<string | null> {
  const { readdir } = await import("node:fs/promises");
  for (const f of (await readdir(dir)).filter((x) => x.endsWith(".toml"))) {
    const t = await Bun.file(join(dir, f)).text();
    if (t.includes(`[daemons.${daemon}]`)) return f;
  }
  return null;
}
// design C: find the project fragment holding target
{
  const { readdir } = await import("node:fs/promises");
  const cDir = join(root, "proto-c");
  outer: for (const e of await readdir(cDir)) {
    const p = join(cDir, e, ".daemon.toml");
    if (await Bun.file(p).exists()) {
      if ((await Bun.file(p).text()).includes(`[daemons.${target}]`)) { targetFile.C = p; break outer; }
    }
  }
}

results.metrics.M2_single_daemon_change = {};
for (const d of DESIGNS) {
  const fragPath = targetFile[d.tag];
  const before = await Bun.file(join(d.dir, "pitchfork.composed.toml")).text();
  const fragText = await Bun.file(fragPath).text();
  // surgical edit: bump the first `port = N` inside target's stanza
  const edited = fragText.replace(`[daemons.${target}]`, `[daemons.${target}]`)
    .replace(new RegExp(`(\\[daemons\\.${target.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\][\\s\\S]*?)(port\\s*=\\s*)(\\d+)`),
      (_m, pre, k, n) => `${pre}${k}${parseInt(n) + 1}`);
  if (edited === fragText) throw new Error(`M2: no port line found for ${target} in design ${d.tag}`);
  await Bun.write(fragPath, edited);
  const t0 = now();
  await runCli(d);
  const dt = now() - t0;
  const after = await Bun.file(join(d.dir, "pitchfork.composed.toml")).text();
  await Bun.write(fragPath, fragText); // restore
  await runCli(d); // re-compose clean

  // diff scope: lines changed in composed output
  const bl = before.split("\n"), al = after.split("\n");
  let changedLines = 0;
  const n = Math.max(bl.length, al.length);
  for (let i = 0; i < n; i++) if (bl[i] !== al[i]) changedLines++;
  // blast radius: every OTHER daemon byte-identical?
  const fb = parseFragment("b", before), fa = parseFragment("a", after);
  let othersIdentical = true;
  for (const nm of origNames) {
    if (nm === target) continue;
    if (fb.daemons.get(nm)!.join("\n") !== fa.daemons.get(nm)!.join("\n")) { othersIdentical = false; break; }
  }
  results.metrics.M2_single_daemon_change[d.tag] = {
    target, fragment_touched: fragPath.replace(root + "/", ""),
    recompose_ms: +dt.toFixed(2), composed_diff_lines: changedLines,
    other_daemons_byte_identical: othersIdentical,
  };
}

// ---------- M3: merge-conflict safety (git simulation) ----------
async function sh(cwd: string, ...args: string[]) {
  const p = Bun.spawn(["git", ...args], { cwd, stdout: "pipe", stderr: "pipe" });
  const [out, err, code] = await Promise.all([new Response(p.stdout).text(), new Response(p.stderr).text(), p.exited]);
  return { out: out.trim(), err: err.trim(), code };
}
function editDaemonPort(file: string, daemon: string, bump: number): string {
  const t = Bun.file(file);
  return t.text().then((text) => {
    const re = new RegExp(`(\\[daemons\\.${daemon.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\][\\s\\S]*?)(port\\s*=\\s*)(\\d+)`);
    const edited = text.replace(re, (_m, pre, k, n) => `${pre}${k}${parseInt(n) + bump}`);
    if (edited === text) throw new Error(`no port for ${daemon} in ${file}`);
    return Bun.write(file, edited);
  }) as unknown as string;
}

async function mergeSim(tag: string, dir: string, daemonX: string, daemonY: string, adjacent: boolean) {
  const work = join(root, `m3-${tag.toLowerCase()}-${adjacent ? "adj" : "far"}`);
  await Bun.$`rm -rf ${work} && cp -r ${dir} ${work}`.quiet();
  // strip build outputs from the sim repo
  await Bun.$`rm -f ${work}/pitchfork.composed.toml`.quiet();
  const env = { ...process.env, GIT_AUTHOR_NAME: "t", GIT_AUTHOR_EMAIL: "t@t", GIT_COMMITTER_NAME: "t", GIT_COMMITTER_EMAIL: "t@t" };
  const g = ( ...a: string[]) => Bun.spawn(["git", ...a], { cwd: work, stdout: "pipe", stderr: "pipe", env }).exited;
  await g("init", "-q", "-b", "base"); await g("add", "-A"); await g("commit", "-qm", "base");
  const fileFor = async (daemon: string): Promise<string> => {
    const { readdir } = await import("node:fs/promises");
    const found: string[] = [];
    async function walk(d: string) {
      for (const e of await readdir(d, { withFileTypes: true })) {
        const p = join(d, e.name);
        if (e.name === ".git") continue;
        if (e.isDirectory()) await walk(p);
        else if (e.name.endsWith(".toml") && (await Bun.file(p).text()).includes(`[daemons.${daemon}]`)) found.push(p);
      }
    }
    await walk(work);
    if (found.length !== 1) throw new Error(`M3 ${tag}: daemon ${daemon} in ${found.length} files`);
    return found[0];
  };
  // writer 1 edits daemonX on branch w1
  await g("checkout", "-qb", "w1");
  await editDaemonPort(await fileFor(daemonX), daemonX, 1);
  await g("add", "-A"); await g("commit", "-qm", "w1");
  // writer 2 edits daemonY on branch w2 from base
  await g("checkout", "-q", "base"); await g("checkout", "-qb", "w2");
  await editDaemonPort(await fileFor(daemonY), daemonY, 2);
  await g("add", "-A"); await g("commit", "-qm", "w2");
  // merge w2 into w1
  await g("checkout", "-q", "w1");
  const p = Bun.spawn(["git", "merge", "--no-edit", "w2"], { cwd: work, stdout: "pipe", stderr: "pipe", env });
  const [out, err, code] = await Promise.all([new Response(p.stdout).text(), new Response(p.stderr).text(), p.exited]);
  const conflicted = code !== 0;
  let conflictFiles = 0, conflictLines = 0;
  if (conflicted) {
    const st = await sh(work, "diff", "--name-only");
    conflictFiles = st.out.split("\n").filter(Boolean).length;
    const d = await sh(work, "diff");
    conflictLines = (d.out.match(/^<{7}/gm) || []).length;
    await g("merge", "--abort");
  }
  await Bun.$`rm -rf ${work}`.quiet();
  return { conflicted, conflictFiles, conflictHunks: conflictLines };
}

const dX = withPort[10], dYfar = withPort[50], dYadj = withPort[11];
results.metrics.M3_merge_conflicts = {};
// monolith baseline
{
  const mono = join(root, "m3-mono-src");
  await Bun.$`rm -rf ${mono} && mkdir -p ${mono} && cp ${origPath} ${mono}/pitchfork.toml`.quiet();
  results.metrics.M3_merge_conflicts["MONO"] = {
    far: await mergeSim("MONO", mono, dX, dYfar, false),
    adjacent: await mergeSim("MONO", mono, dX, dYadj, true),
  };
  await Bun.$`rm -rf ${mono}`.quiet();
}
for (const d of DESIGNS) {
  results.metrics.M3_merge_conflicts[d.tag] = {
    far: await mergeSim(d.tag, d.dir, dX, dYfar, false),
    adjacent: await mergeSim(d.tag, d.dir, dX, dYadj, true),
  };
}

// ---------- M3b: concurrent daemon ADD ----------
// The fleet's most common change: two writers each ADD a new daemon.
// Monolith: both append at EOF -> same-region collision. Fragments: the
// new daemon lands in its owning file -> disjoint unless co-owned.
const ADD_A = `[daemons.zz-add-one]\nport = 25901\nrun = "exec /bin/true"\n`;
const ADD_B = `[daemons.zz-add-two]\nport = 25902\nrun = "exec /bin/true"\n`;
// design-A group fn (must match split-fixtures.ts)
const groupOfAdd = (n: string) => {
  let h = 0; for (const c of n) h = (h * 31 + c.charCodeAt(0)) >>> 0; return h % 8;
};
async function addSim(tag: string, dir: string) {
  const work = join(root, `m3b-${tag.toLowerCase()}`);
  await Bun.$`rm -rf ${work} && cp -r ${dir} ${work} && rm -f ${work}/pitchfork.composed.toml`.quiet();
  const env = { ...process.env, GIT_AUTHOR_NAME: "t", GIT_AUTHOR_EMAIL: "t@t", GIT_COMMITTER_NAME: "t", GIT_COMMITTER_EMAIL: "t@t" };
  const g = (...a: string[]) => Bun.spawn(["git", ...a], { cwd: work, stdout: "pipe", stderr: "pipe", env }).exited;
  await g("init", "-q", "-b", "base"); await g("add", "-A"); await g("commit", "-qm", "base");
  // where does a brand-new daemon land in each layout?
  async function addTarget(name: string): Promise<string> {
    if (tag === "MONO") return join(work, "pitchfork.toml");
    if (tag === "B") return join(work, "daemons.d", `${name}.toml`); // new file: no append needed
    if (tag === "A") return join(work, "pitchfork.d", `1${groupOfAdd(name)}-group${groupOfAdd(name)}.toml`);
    // C: project unknown for a new daemon -> misc fragment (honest worst case)
    return join(work, "proj-misc", ".daemon.toml");
  }
  // writer 1
  await g("checkout", "-qb", "w1");
  const t1 = await addTarget("zz-add-one");
  if (tag === "B") await Bun.write(t1, ADD_A); else await Bun.write(t1, (await Bun.file(t1).text()) + "\n" + ADD_A);
  await g("add", "-A"); await g("commit", "-qm", "w1 adds zz-add-one");
  // writer 2 (from base)
  await g("checkout", "-q", "base"); await g("checkout", "-qb", "w2");
  const t2 = await addTarget("zz-add-two");
  if (tag === "B") await Bun.write(t2, ADD_B); else await Bun.write(t2, (await Bun.file(t2).text()) + "\n" + ADD_B);
  await g("add", "-A"); await g("commit", "-qm", "w2 adds zz-add-two");
  // merge
  await g("checkout", "-q", "w1");
  const code = await g("merge", "--no-edit", "w2");
  let files = 0, hunks = 0;
  if (code !== 0) {
    const st = await sh(work, "status", "--porcelain");
    files = st.out.split("\n").filter((l) => l.startsWith("UU")).length;
    const { readdir } = await import("node:fs/promises");
    async function walk(d: string): Promise<void> {
      for (const e of await readdir(d, { withFileTypes: true })) {
        if (e.name === ".git") continue;
        const p = join(d, e.name);
        if (e.isDirectory()) await walk(p);
        else if (e.name.endsWith(".toml")) {
          const t = await Bun.file(p).text();
          hunks += (t.match(/^<{7}/gm) || []).length;
        }
      }
    }
    await walk(work);
    await g("merge", "--abort");
  }
  const r = { conflicted: code !== 0, conflict_files: files, conflict_hunks: hunks };
  await Bun.$`rm -rf ${work}`.quiet();
  return r;
}
results.metrics.M3b_concurrent_add = {};
{
  const mono = join(root, "m3b-mono-src");
  await Bun.$`rm -rf ${mono} && mkdir -p ${mono} && cp ${origPath} ${mono}/pitchfork.toml`.quiet();
  results.metrics.M3b_concurrent_add["MONO"] = await addSim("MONO", mono);
  await Bun.$`rm -rf ${mono}`.quiet();
}
for (const d of DESIGNS) results.metrics.M3b_concurrent_add[d.tag] = await addSim(d.tag, d.dir);
console.log(JSON.stringify({ metric: "M3b", ...results.metrics.M3b_concurrent_add }));

// ---------- M4: rollback triage cost ----------
// Scenario: one commit mixes 6 daemon edits (5 good + 1 bad — the monolith's
// classic "while I'm here" commit). Cost measured = how much human triage to
// revert ONLY the bad daemon: count of FOREIGN [daemons.*] stanzas touched in
// the same file as the bad daemon's diff. 0 = file-level revert, no surgery.
async function rollbackSim(tag: string, dir: string) {
  const { resolve } = await import("node:path");
  const work = resolve(root, `m4-${tag.toLowerCase()}`);
  await Bun.$`rm -rf ${work} && cp -r ${dir} ${work} && rm -f ${work}/pitchfork.composed.toml`.quiet();
  const env = { ...process.env, GIT_AUTHOR_NAME: "t", GIT_AUTHOR_EMAIL: "t@t", GIT_COMMITTER_NAME: "t", GIT_COMMITTER_EMAIL: "t@t" };
  const g = (...a: string[]) => Bun.spawn(["git", ...a], { cwd: work, stdout: "pipe", stderr: "pipe", env }).exited;
  await g("init", "-q", "-b", "base"); await g("add", "-A"); await g("commit", "-qm", "base");
  // six daemons spread across the sorted list, all with port lines
  const six = [5, 15, 25, 35, 45, 50].map((i) => withPort[i]);
  const bad = six[0];
  const { readdir } = await import("node:fs/promises");
  async function fileFor(daemon: string): Promise<string> {
    const found: string[] = [];
    async function walk(d: string) {
      for (const e of await readdir(d, { withFileTypes: true })) {
        const p = join(d, e.name);
        if (e.name === ".git") continue;
        if (e.isDirectory()) await walk(p);
        else if (e.name.endsWith(".toml") && (await Bun.file(p).text()).includes(`[daemons.${daemon}]`)) found.push(p);
      }
    }
    await walk(work);
    return found[0];
  }
  for (const dm of six) await editDaemonPort(await fileFor(dm), dm, 7);
  await g("add", "-A"); await g("commit", "-qm", "six daemon tweaks (one is bad)");
  // isolate the bad daemon's file; attribute each diff hunk to its stanza by
  // tracking the last-seen [daemons.X] header (context lines carry " " prefix)
  const badFile = await fileFor(bad);
  const d = await sh(work, "diff", "HEAD~1", "HEAD", "--", badFile);
  const stanzasTouched = new Set<string>();
  let cur = "", hunkOpen = false, hunkDaemon: string | null = null;
  for (const line of d.out.split("\n")) {
    if (line.startsWith("@@")) { hunkOpen = true; hunkDaemon = null; continue; }
    const hm = /^[ +-]\[daemons\.([^\]]+)\]/.exec(line);
    if (hm) {
      cur = hm[1];
      // an added/removed stanza header is itself the hunk's subject
      if (hunkOpen && (line[0] === "+" || line[0] === "-") && hunkDaemon === null) {
        hunkDaemon = cur; stanzasTouched.add(cur);
      }
      continue;
    }
    if (hunkOpen && (line.startsWith("+") || line.startsWith("-")) && hunkDaemon === null
        && !line.startsWith("+++") && !line.startsWith("---")) {
      hunkDaemon = cur; stanzasTouched.add(cur);
    }
  }
  const foreign = [...stanzasTouched].filter((s) => s !== bad);
  const t0 = now();
  // the revert a human runs for the single bad daemon: restore just its file.
  // over_reverted = good daemons whose tweaks get clobbered by that restore.
  await g("checkout", "HEAD~1", "--", badFile);
  await g("commit", "-qm", `revert bad ${bad} tweak`);
  const dt = now() - t0;
  await Bun.$`rm -rf ${work}`.quiet();
  return {
    bad_daemon: bad,
    bad_file: badFile.replace(work + "/", ""),
    stanzas_in_bad_file_diff: stanzasTouched.size,
    foreign_stanzas_in_same_file: foreign.length,
    over_reverted_good_daemons: foreign.length, // file restore clobbers their tweaks
    revert_cmds: foreign.length === 0 ? 2 : 2 + foreign.length, // +hunk triage per foreign stanza
    revert_ms: +dt.toFixed(2),
  };
}
results.metrics.M4_rollback = {
  MONO: await rollbackSim("MONO", await (async () => {
    const m = join(root, "m4-mono-src"); await Bun.$`rm -rf ${m} && mkdir -p ${m} && cp ${origPath} ${m}/pitchfork.toml`.quiet(); return m;
  })()),
};
await Bun.$`rm -rf ${join(root, "m4-mono-src")}`.quiet();
for (const d of DESIGNS) results.metrics.M4_rollback[d.tag] = await rollbackSim(d.tag, d.dir);

await Bun.write(join(root, "race-results.json"), JSON.stringify(results, null, 2));
console.log(JSON.stringify(results.metrics, null, 2));
