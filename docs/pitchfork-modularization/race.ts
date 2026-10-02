// race.ts — hyper-race the three modularization designs (Ferret, Ember's crew, 2026-09-30).
// HFT doctrine: fire the contestants CONCURRENTLY, per-attempt ceilings, first-valid-wins
// is replaced here by a measurement shootout (designs are alternatives, not retries):
// every contestant is timed at high precision and the table is the verdict.
// Phases: (1) merge/generate/compose race  (2) parallel-edit conflict simulation
//         (3) hot-reload granularity        (4) rollback                     (5) retire-5 demo
import { nsNow, nsToMs, median, withCeiling, parseToml, deepEqual, daemonDiff } from "./lib/toml.ts";

const HERE = import.meta.dir;
const WORK = `${HERE}/work`;
const RACE = `${WORK}/race`;
const CEIL = 10_000;
const RUNS = 7;
const results: any = { phases: {} };

async function sh(cmd: string[], cwd = ".") {
  const p = Bun.spawn(cmd, { cwd, stdout: "pipe", stderr: "pipe" });
  const [so, se, code] = await Promise.all([new Response(p.stdout).text(), new Response(p.stderr).text(), p.exited]);
  return { so, se, code };
}

// Edit a key in a design-B manifest ([daemon] table, single-daemon file).
async function editManifestKey(path: string, key: string, neu: string) {
  const before = await Bun.file(path).text();
  const after = before.replace(new RegExp(`^${key} = .*$`, "m"), `${key} = ${neu}`);
  if (after === before) throw new Error(`editManifestKey: ${key} not found in ${path}`);
  await Bun.write(path, after);
}

// Edit one daemon's key inside a TOML-ish text file, section-aware. Verifies the edit landed.
async function editDaemonKey(path: string, daemon: string, key: string, neu: string) {
  const lines = (await Bun.file(path).text()).split("\n");
  let cur = "", done = false;
  const out = lines.map((l) => {
    const m = l.match(/^\[(daemons|groups)\.([^\]]+)\]/);
    if (m) cur = m[1] === "daemons" ? m[2] : "";
    if (cur === daemon && !done && l.match(new RegExp(`^${key} = `))) { done = true; return `${key} = ${neu}`; }
    return l;
  });
  if (!done) throw new Error(`editDaemonKey: ${daemon}.${key} not found in ${path}`);
  await Bun.write(path, out.join("\n"));
}

const origParsed = parseToml(await Bun.file(`${WORK}/../pitchfork.toml.orig`).text());

// ---------------- phase 1: merge race ----------------
console.log("== phase 1: merge race (7 timed runs each, 10s ceiling, concurrent) ==");
// B's fail-closed retirement ledger blocks generation while the 5 stale manifests exist.
// Phase 1 races the faithful reproduction of the CURRENT 82-daemon set, so B runs against
// a scratch copy with an empty retirement ledger (phase 5 covers the retirement explicitly).
await Bun.$`rm -rf ${RACE}/b-full`.quiet();
await Bun.$`cp -r ${WORK}/b ${RACE}/b-full`.quiet();
await Bun.write(`${RACE}/b-full/retired.toml`, `retired = []\n`);
const contestants = [
  { name: "A drop-ins", cmd: ["bun", `${HERE}/design-a/merge-a.ts`, `${WORK}/a/pitchfork.toml`, `${WORK}/a/pitchfork.d`, "--out", `${RACE}/a.toml`] },
  { name: "B manifests", cmd: ["bun", `${HERE}/design-b/gen-b.ts`, `${RACE}/b-full/base.toml`, `${RACE}/b-full/daemons.d`, `${RACE}/b-full/retired.toml`, "--out", `${RACE}/b.toml`] },
  { name: "C fragments", cmd: ["bun", `${HERE}/design-c/compose-c.ts`, `${WORK}/c/fragments`, "--out", `${RACE}/c.toml`] },
];
await Bun.$`mkdir -p ${RACE}`.quiet();
const phase1 = await Promise.all(contestants.map(async (c) => {
  const lat: number[] = [];
  for (let i = 0; i < RUNS; i++) {
    const t0 = nsNow();
    const r = await withCeiling(sh(c.cmd).then((x) => { if (x.code !== 0) throw new Error(x.se); }), CEIL, c.name);
    lat.push(nsToMs(nsNow() - t0));
  }
  const out = `${RACE}/${c.name[0].toLowerCase()}.toml`;
  const parsed = parseToml(await Bun.file(out).text());
  const valid = deepEqual(parsed.daemons, origParsed.daemons) && deepEqual(parsed.groups, origParsed.groups) && parsed.env_file === origParsed.env_file;
  const bytes = (await Bun.file(out).text()).length;
  console.log(`  ${c.name}: median ${median(lat).toFixed(2)}ms valid=${valid} bytes=${bytes}`);
  return { design: c.name, median_ms: +median(lat).toFixed(2), runs_ms: lat.map((x) => +x.toFixed(2)), valid, bytes };
}));
results.phases.merge = phase1;

// ---------------- phase 2: parallel-edit conflict simulation ----------------
// This is what killed the last attempt: committed merge-conflict markers in [daemons.flock].
console.log("== phase 2: parallel-edit conflict simulation (concurrent) ==");
async function gitRepo(dir: string) {
  await Bun.$`rm -rf ${dir}`.quiet();
  await Bun.$`mkdir -p ${dir}`.quiet();
  await sh(["git", "init", "-b", "main", "-q"], dir);
  await sh(["git", "config", "user.email", "ferret@fleet"], dir);
  await sh(["git", "config", "user.name", "Ferret"], dir);
}
async function tryMerge(dir: string): Promise<{ conflict: boolean; ms: number }> {
  const t0 = nsNow();
  const r = await sh(["git", "merge", "e2", "--no-edit"], dir);
  const ms = nsToMs(nsNow() - t0);
  const conflict = r.code !== 0 || /CONFLICT/.test(r.so + r.se);
  await sh(["git", "merge", "--abort"], dir).catch(() => {});
  return { conflict, ms: +ms.toFixed(1) };
}

const simMonolithOverlap = (async () => {
  const d = `${RACE}/git-monolith-overlap`;
  await gitRepo(d);
  await Bun.$`cp ${WORK}/../pitchfork.toml.orig ${d}/pitchfork.toml`.quiet();
  await sh(["git", "add", "."], d); await sh(["git", "commit", "-qm", "base"], d);
  await sh(["git", "checkout", "-qb", "e1"], d);
  await editDaemonKey(`${d}/pitchfork.toml`, "flock", "port", "25194"); // agent 1: flock port
  await sh(["git", "commit", "-qam", "e1: flock port"], d);
  await sh(["git", "checkout", "-q", "main"], d);
  await sh(["git", "checkout", "-qb", "e2"], d);
  await editDaemonKey(`${d}/pitchfork.toml`, "flock", "run", '"exec /home/toxic/estate/projects/range/ranch/flock/bin/flock-run.sh --trace"'); // agent 2: flock run
  await sh(["git", "commit", "-qam", "e2: flock run"], d);
  await sh(["git", "checkout", "-q", "e1"], d);
  return { case: "monolith: two agents edit SAME section [daemons.flock]", ...(await tryMerge(d)) };
})();

const simMonolithAdjacent = (async () => {
  const d = `${RACE}/git-monolith-adjacent`;
  await gitRepo(d);
  await Bun.$`cp ${WORK}/../pitchfork.toml.orig ${d}/pitchfork.toml`.quiet();
  await sh(["git", "add", "."], d); await sh(["git", "commit", "-qm", "base"], d);
  await sh(["git", "checkout", "-qb", "e1"], d);
  await editDaemonKey(`${d}/pitchfork.toml`, "flicker", "run", '"exec e1-flag"'); // agent 1: flicker (line ~554)
  await sh(["git", "commit", "-qam", "e1"], d);
  await sh(["git", "checkout", "-q", "main"], d);
  await sh(["git", "checkout", "-qb", "e2"], d);
  await editDaemonKey(`${d}/pitchfork.toml`, "flicker-agent", "run", '"exec e2-flag"'); // agent 2: adjacent section
  await sh(["git", "commit", "-qam", "e2"], d);
  await sh(["git", "checkout", "-q", "e1"], d);
  return { case: "monolith: two agents edit ADJACENT sections", ...(await tryMerge(d)) };
})();

const simModularDisjoint = (async () => {
  const d = `${RACE}/git-modular-disjoint`;
  await gitRepo(d);
  await Bun.$`cp -r ${WORK}/a/pitchfork.toml ${WORK}/a/pitchfork.d ${d}/`.quiet();
  await sh(["git", "add", "."], d); await sh(["git", "commit", "-qm", "base"], d);
  const flockF = (await sh(["bash", "-c", `ls ${d}/pitchfork.d/*-flock.toml`], ".")).so.trim();
  const flickF = (await sh(["bash", "-c", `ls ${d}/pitchfork.d/*-flicker.toml | head -1`], ".")).so.trim();
  await sh(["git", "checkout", "-qb", "e1"], d);
  await editDaemonKey(flockF, "flock", "port", "25194");
  await sh(["git", "commit", "-qam", "e1"], d);
  await sh(["git", "checkout", "-q", "main"], d);
  await sh(["git", "checkout", "-qb", "e2"], d);
  await editDaemonKey(flickF, "flicker", "port", "25991");
  await sh(["git", "commit", "-qam", "e2"], d);
  await sh(["git", "checkout", "-q", "e1"], d);
  return { case: "modular (A): two agents edit DIFFERENT daemon files", ...(await tryMerge(d)) };
})();

const simModularSameFile = (async () => {
  const d = `${RACE}/git-modular-samefile`;
  await gitRepo(d);
  await Bun.$`cp -r ${WORK}/a/pitchfork.toml ${WORK}/a/pitchfork.d ${d}/`.quiet();
  await sh(["git", "add", "."], d); await sh(["git", "commit", "-qm", "base"], d);
  const flockF = (await sh(["bash", "-c", `ls ${d}/pitchfork.d/*-flock.toml`], ".")).so.trim();
  await sh(["git", "checkout", "-qb", "e1"], d);
  await editDaemonKey(flockF, "flock", "port", "25194");
  await sh(["git", "commit", "-qam", "e1"], d);
  await sh(["git", "checkout", "-q", "main"], d);
  await sh(["git", "checkout", "-qb", "e2"], d);
  await editDaemonKey(flockF, "flock", "run", '"exec /home/toxic/estate/projects/range/ranch/flock/bin/flock-run.sh --trace"');
  await sh(["git", "commit", "-qam", "e2"], d);
  await sh(["git", "checkout", "-q", "e1"], d);
  return { case: "modular (A): two agents edit the SAME daemon file", ...(await tryMerge(d)) };
})();

const phase2 = await Promise.all([simMonolithOverlap, simMonolithAdjacent, simModularDisjoint, simModularSameFile]);
for (const p of phase2) console.log(`  ${p.case}: conflict=${p.conflict} (${p.ms}ms)`);
results.phases.conflict = phase2;

// ---------------- phase 3: hot-reload granularity ----------------
// One daemon's port changes in source; re-run; diff old vs new merged => daemons to re-register.
console.log("== phase 3: hot-reload granularity (one daemon port change) ==");
// (granularity edits are design-specific; run inline below for clarity)
const gran: any = {};
{
  const s = `${RACE}/gran-a`; await Bun.$`rm -rf ${s}`.quiet();
  await Bun.$`cp -r ${WORK}/a ${s}`.quiet();
  await sh(["bun", `${HERE}/design-a/merge-a.ts`, `${s}/pitchfork.toml`, `${s}/pitchfork.d`, "--out", `${s}/before.toml`]);
  const t0 = nsNow();
  const flockF = (await sh(["bash", "-c", `ls ${s}/pitchfork.d/*-flock.toml`], ".")).so.trim();
  await editDaemonKey(flockF, "flock", "port", "25993");
  await sh(["bun", `${HERE}/design-a/merge-a.ts`, `${s}/pitchfork.toml`, `${s}/pitchfork.d`, "--out", `${s}/after.toml`]);
  const ms = nsToMs(nsNow() - t0);
  const diff = daemonDiff(parseToml(await Bun.file(`${s}/before.toml`).text()), parseToml(await Bun.file(`${s}/after.toml`).text()));
  gran.A = { changed_daemons: [...diff.changed, ...diff.added, ...diff.removed], remerge_ms: +ms.toFixed(2) };
}
{
  const s = `${RACE}/gran-b`; await Bun.$`rm -rf ${s}`.quiet();
  await Bun.$`cp -r ${RACE}/b-full ${s}`.quiet();
  await sh(["bun", `${HERE}/design-b/gen-b.ts`, `${s}/base.toml`, `${s}/daemons.d`, `${s}/retired.toml`, "--out", `${s}/before.toml`]);
  const t0 = nsNow();
  await editManifestKey(`${s}/daemons.d/flock.toml`, "port", "25993");
  await sh(["bun", `${HERE}/design-b/gen-b.ts`, `${s}/base.toml`, `${s}/daemons.d`, `${s}/retired.toml`, "--out", `${s}/after.toml`]);
  const ms = nsToMs(nsNow() - t0);
  const diff = daemonDiff(parseToml(await Bun.file(`${s}/before.toml`).text()), parseToml(await Bun.file(`${s}/after.toml`).text()));
  gran.B = { changed_daemons: [...diff.changed, ...diff.added, ...diff.removed], remerge_ms: +ms.toFixed(2) };
}
{
  const s = `${RACE}/gran-c`; await Bun.$`rm -rf ${s}`.quiet();
  await Bun.$`cp -r ${WORK}/c ${s}`.quiet();
  await sh(["bun", `${HERE}/design-c/compose-c.ts`, `${s}/fragments`, "--out", `${s}/before.toml`]);
  const t0 = nsNow();
  await Bun.write(`${s}/fragments/99-local.toml`, `[daemons.flock]\nport = 25993\n`);
  await sh(["bun", `${HERE}/design-c/compose-c.ts`, `${s}/fragments`, "--out", `${s}/after.toml`]);
  const ms = nsToMs(nsNow() - t0);
  const diff = daemonDiff(parseToml(await Bun.file(`${s}/before.toml`).text()), parseToml(await Bun.file(`${s}/after.toml`).text()));
  gran.C = { changed_daemons: [...diff.changed, ...diff.added, ...diff.removed], remerge_ms: +ms.toFixed(2) };
}
for (const k of ["A", "B", "C"]) console.log(`  design ${k}: re-register ${JSON.stringify(gran[k].changed_daemons)} (${gran[k].remerge_ms}ms)`);
results.phases.granularity = gran;

// ---------------- phase 4: rollback ----------------
// git checkout the single changed source file + re-run => merged must equal pre-change bytes.
console.log("== phase 4: rollback (single-file revert + re-merge) ==");
const roll: any = {};
async function rollback(design: "A" | "B" | "C") {
  const s = `${RACE}/roll-${design}`;
  await Bun.$`rm -rf ${s}`.quiet();
  const layout = design === "A" ? "a" : design === "B" ? "b" : "c";
  const srcDir = design === "B" ? `${RACE}/b-full` : `${WORK}/${layout}`; // B: empty retirement ledger (phase-5 covers retirement)
  await Bun.$`cp -r ${srcDir} ${s}`.quiet();
  await sh(["git", "init", "-b", "main", "-q"], s);
  await sh(["git", "config", "user.email", "ferret@fleet"], s);
  await sh(["git", "config", "user.name", "Ferret"], s);
  await sh(["git", "add", "."], s); await sh(["git", "commit", "-qm", "base"], s);
  const runArgs = design === "A"
    ? [`${HERE}/design-a/merge-a.ts`, `${s}/pitchfork.toml`, `${s}/pitchfork.d`]
    : design === "B"
      ? [`${HERE}/design-b/gen-b.ts`, `${s}/base.toml`, `${s}/daemons.d`, `${s}/retired.toml`]
      : [`${HERE}/design-c/compose-c.ts`, `${s}/fragments`];
  const t0 = nsNow();
  await withCeiling(sh(["bun", ...runArgs, "--out", `${s}/merged.toml`]).then((r) => { if (r.code !== 0) throw new Error(r.se); }), CEIL, `roll-${design}`);
  const goodBytes = await Bun.file(`${s}/merged.toml`).text();
  // apply a bad change, then roll it back with a single-file checkout
  let changedRel: string;
  if (design === "C") {
    await Bun.write(`${s}/fragments/99-local.toml`, `[daemons.flock]\nport = 1\n`);
    changedRel = "fragments/99-local.toml";
  } else if (design === "A") {
    const f = (await sh(["bash", "-c", `ls ${s}/pitchfork.d/*-flock.toml`], ".")).so.trim();
    await editDaemonKey(f, "flock", "port", "1");
    changedRel = "pitchfork.d/" + f.split("/").pop()!;
  } else {
    await editManifestKey(`${s}/daemons.d/flock.toml`, "port", "1");
    changedRel = "daemons.d/flock.toml";
  }
  await sh(["git", "checkout", "--", changedRel], s);
  await withCeiling(sh(["bun", ...runArgs, "--out", `${s}/merged2.toml`]).then((r) => { if (r.code !== 0) throw new Error(r.se); }), CEIL, `roll-${design}-2`);
  const ms = nsToMs(nsNow() - t0);
  const restored = (await Bun.file(`${s}/merged2.toml`).text()) === goodBytes;
  return { ms: +ms.toFixed(2), restored, steps: [`git checkout -- ${changedRel}`, "re-run merger"] };
}
const [rA, rB, rC] = await Promise.all([rollback("A"), rollback("B"), rollback("C")]);
roll.A = rA; roll.B = rB; roll.C = rC;
for (const k of ["A", "B", "C"]) console.log(`  design ${k}: rollback ${roll[k].ms}ms restored=${roll[k].restored}`);
results.phases.rollback = roll;

// ---------------- phase 5: retire the 5 stale ----------------
console.log("== phase 5: the 5 stale entries (bidder-forge, bidder-scout, buildsrv, flicker, flicker-agent) ==");
const stale = ["bidder-forge", "bidder-scout", "buildsrv", "flicker", "flicker-agent"];
const retire: any = {};
{
  // B fail-closed demo: manifests still exist while retired.toml lists them => ERROR
  const r = await sh(["bun", `${HERE}/design-b/gen-b.ts`, `${WORK}/b/base.toml`, `${WORK}/b/daemons.d`, `${WORK}/b/retired.toml`]);
  retire.B_failclosed = { exit: r.code, stderr: r.se.trim().split("\n")[0] };
  const s = `${RACE}/retire-b`; await Bun.$`rm -rf ${s}`.quiet();
  await Bun.$`cp -r ${WORK}/b ${s}`.quiet();
  for (const n of stale) await Bun.$`rm ${s}/daemons.d/${n}.toml`.quiet();
  const r2 = await sh(["bun", `${HERE}/design-b/gen-b.ts`, `${s}/base.toml`, `${s}/daemons.d`, `${s}/retired.toml`, "--out", `${s}/out.toml`]);
  const n = Object.keys(parseToml(await Bun.file(`${s}/out.toml`).text()).daemons).length;
  retire.B = { after_delete: `${n} daemons`, exit: r2.code };
}
{
  const s = `${RACE}/retire-a`; await Bun.$`rm -rf ${s}`.quiet();
  await Bun.$`cp -r ${WORK}/a ${s}`.quiet();
  for (const n of stale) await Bun.$`rm ${s}/pitchfork.d/*-${n}.toml`.quiet();
  const r = await sh(["bun", `${HERE}/design-a/merge-a.ts`, `${s}/pitchfork.toml`, `${s}/pitchfork.d`, "--out", `${s}/out.toml`]);
  const n = Object.keys(parseToml(await Bun.file(`${s}/out.toml`).text()).daemons).length;
  retire.A = { after_delete: `${n} daemons`, exit: r.code, how: "delete 5 drop-in files" };
}
{
  // C: the 5 live INSIDE shared multi-daemon project fragments — no per-daemon file to delete
  retire.C = {
    note: "stale daemons live inside shared fragments (no per-daemon file)",
    locations: {
      "fragments/20-ranch.toml": ["bidder-forge", "bidder-scout", "flicker", "flicker-agent"],
      "fragments/30-tools.toml": ["buildsrv"],
    },
    how: "hand-edit 2 shared fragments to remove 5 sections (multi-writer hazard)",
  };
}
console.log(`  B fail-closed: exit=${retire.B_failclosed.exit} "${retire.B_failclosed.stderr}"`);
console.log(`  A: ${retire.A.how} => ${retire.A.after_delete}`);
console.log(`  B: delete 5 manifests => ${retire.B.after_delete}`);
console.log(`  C: ${retire.C.how}`);
results.phases.retire5 = retire;

// code size per design
const loc: any = {};
for (const [k, f] of [["A", `${HERE}/design-a/merge-a.ts`], ["B", `${HERE}/design-b/gen-b.ts`], ["C", `${HERE}/design-c/compose-c.ts`]])
  loc[k] = +(await Bun.$`wc -l < ${f}`.text()).trim();
results.loc = loc;
results.shared_lib_loc = +(await Bun.$`wc -l < lib/toml.ts`.text()).trim();

await Bun.write(`${RACE}/results.json`, JSON.stringify(results, null, 2));
console.log("\nresults => work/race/results.json");
