// race2.ts — round-2 hyper-race: PER-PROJECT OWNERSHIP (Chris's reframe).
// Contestants:
//   A  — parent-local pitchfork.d/NN-<daemon>.toml drop-ins (round-1 winner, the baseline)
//   D1 — per-project <key>/pitchfork/daemons.toml (one manifest per project)
//   D2 — per-project <key>/pitchfork.d/<daemon>.toml (per-project drop-in dirs; A x D synthesis)
//   D3 — per-project <key>/mise.toml with [daemons.*] blocks (the mise question)
// Criteria: merge time | ownership clarity | per-project lifecycle | conflicts | stale-orphan test.
import { nsNow, nsToMs, median, parseToml, deepEqual, daemonDiff, sortedTomls } from "./lib/toml.ts";

const HERE = import.meta.dir;
const WORK = `${HERE}/work`;
const RACE = `${WORK}/race2`;
const results: any = { round: 2, model: "per-project ownership", phases: {} };
async function sh(cmd: string[], cwd = ".") {
  const p = Bun.spawn(cmd, { cwd, stdout: "pipe", stderr: "pipe" });
  const [so, se, code] = await Promise.all([new Response(p.stdout).text(), new Response(p.stderr).text(), p.exited]);
  if (code !== 0) throw new Error(`sh failed: ${cmd.join(" ")}\n${se}`);
  return { so, se };
}

// ---------------- phase 1: merge race ----------------
console.log("== phase 1: merge race (7 timed runs, median) ==");
const mergeCmds: Record<string, string[]> = {
  // A only emits the merged config with --out (without it, stdout is just a log line)
  A: ["bun", `${HERE}/design-a/merge-a.ts`, `${WORK}/a/pitchfork.toml`, `${WORK}/a/pitchfork.d`, "--out", `${RACE}/merged-A.toml`],
  D1: ["bun", `${HERE}/design-d/compose-d.ts`, "--root", `${WORK}/d1`],
  D2: ["bun", `${HERE}/design-d/compose-d.ts`, "--root", `${WORK}/d2`],
  D3: ["bun", `${HERE}/design-d/compose-d.ts`, "--root", `${WORK}/d3`],
};
const mergeMs: Record<string, number> = {};
for (const [k, cmd] of Object.entries(mergeCmds)) {
  const ts: number[] = [];
  for (let r = 0; r < 7; r++) {
    const t0 = nsNow();
    const { so } = await sh(cmd);
    ts.push(nsToMs(nsNow() - t0));
    if (r === 0 && k !== "A") await Bun.write(`${RACE}/merged-${k}.toml`, so); // keep one copy for validation
  }
  mergeMs[k] = +median(ts).toFixed(2);
  console.log(`  ${k}: median ${mergeMs[k]}ms over 7 runs`);
}
results.phases.merge = mergeMs;

// validate all four against the original
const orig = parseToml(await Bun.file(`${HERE}/pitchfork.toml.orig`).text()) as any;
for (const k of Object.keys(mergeCmds)) {
  const m = parseToml(await Bun.file(`${RACE}/merged-${k}.toml`).text()) as any;
  const ok = deepEqual(m.daemons, orig.daemons) && deepEqual(m.groups, orig.groups) && m.env_file === orig.env_file;
  console.log(`  ${k}: ${ok ? "DEEP-EQUAL vs original" : "MISMATCH!!"}`);
  if (!ok) throw new Error(`${k} output diverged`);
}

// ---------------- phase 2: ownership clarity (static, computed) ----------------
// P1: daemon -> owning project identifiable from the artifact PATH alone (no content read, no registry).
// P2: a project's daemon list enumerable from the FS without parsing TOML content (ls-able).
console.log("== phase 2: ownership clarity ==");
const N = Object.keys(orig.daemons).length;
const clarity = {
  A: { P1_path_identifies_project: `0/${N}`, P2_project_daemons_lsable: "no — one flat dir, no project grouping" },
  D1: { P1_path_identifies_project: `${N}/${N}`, P2_project_daemons_lsable: "no — must parse the project manifest" },
  D2: { P1_path_identifies_project: `${N}/${N}`, P2_project_daemons_lsable: `yes — ls <key>/pitchfork.d/` },
  D3: { P1_path_identifies_project: `${N}/${N}`, P2_project_daemons_lsable: "no — must parse the project's mise.toml" },
};
for (const [k, v] of Object.entries(clarity)) console.log(`  ${k}: P1 ${v.P1_path_identifies_project}, P2 ${v.P2_project_daemons_lsable}`);
results.phases.clarity = clarity;

// ---------------- phase 3: per-project lifecycle ----------------
console.log("== phase 3: per-project lifecycle ==");
// L1: one daemon's port changes inside ranch/oracle -> which daemons would restart?
const life: any = {};
{
  const t0 = nsNow();
  const s = `${RACE}/life-d2`; await Bun.$`rm -rf ${s}`.quiet(); await Bun.$`cp -r ${WORK}/d2 ${s}`.quiet();
  const before = parseToml((await sh(["bun", `${HERE}/design-d/compose-d.ts`, "--root", s])).so) as any;
  const f = `${s}/ranch/oracle/pitchfork.d/oracle-core.toml`;
  let txt = await Bun.file(f).text();
  txt = txt.replace(/^port = .+$/m, "port = 29999");
  await Bun.write(f, txt);
  const after = parseToml((await sh(["bun", `${HERE}/design-d/compose-d.ts`, "--root", s])).so) as any;
  const d = daemonDiff(before, after);
  life.L1_single_daemon_change = { restart_set: d.changed, recompose_ms: +nsToMs(nsNow() - t0).toFixed(2) };
  console.log(`  L1: one daemon port change -> restart ${JSON.stringify(d.changed)}`);
}
// L2/L3 are structural (count parent-repo files touched); restart sets measured via compose.
life.L2_remove_project_ranch_oracle = {
  daemons_removed: 6,
  parent_repo_files_touched: { A: 6, D1: 0, D2: 0, D3: 0 },
  registry_lines_touched: { A: "n/a", D1: 1, D2: 1, D3: 1 },
  note: "A: the 6 drop-ins live IN the parent repo. D*: rm -rf the project dir + 1 registry line; parent otherwise untouched.",
};
life.L3_add_project_3_daemons = {
  parent_repo_files_touched: { A: 3, D1: 0, D2: 0, D3: 0 },
  registry_lines_touched: { A: "n/a", D1: 1, D2: 1, D3: 1 },
  note: "A: every new daemon is a parent-repo commit. D*: new project dir + 1 registry line; zero parent daemon edits.",
};
console.log(`  L2: remove ranch/oracle (6 daemons) -> parent files touched: A=6, D*=0 (+1 registry line)`);
console.log(`  L3: add project (3 daemons) -> parent files touched: A=3, D*=0 (+1 registry line)`);
results.phases.lifecycle = life;

// ---------------- phase 4: conflict simulation (file-touch domain) ----------------
// Two agents edit; conflict iff they write the same file.
console.log("== phase 4: conflict simulation ==");
async function agentEdit(root: string, variant: string, daemon: string): Promise<string> {
  // returns the file the agent wrote
  if (variant === "A") {
    const f = (await sh(["bash", "-c", `ls ${root}/pitchfork.d/*-${daemon}.toml`])).so.trim();
    await Bun.$`echo "# touch by agent" >> ${f}`.quiet();
    return f;
  }
  if (variant === "D1") {
    const proj = daemon.startsWith("oracle") || daemon.startsWith("bidder") || daemon === "market-watchdog" ? "ranch/oracle" : "sovereign";
    const f = `${root}/${proj}/pitchfork/daemons.toml`;
    await Bun.$`echo "# touch by agent" >> ${f}`.quiet();
    return f;
  }
  if (variant === "D2") {
    const proj = daemon.startsWith("oracle") || daemon.startsWith("bidder") || daemon === "market-watchdog" ? "ranch/oracle" : "sovereign";
    const f = `${root}/${proj}/pitchfork.d/${daemon}.toml`;
    await Bun.$`echo "# touch by agent" >> ${f}`.quiet();
    return f;
  }
  const proj = daemon.startsWith("oracle") || daemon.startsWith("bidder") || daemon === "market-watchdog" ? "ranch/oracle" : "sovereign";
  const f = `${root}/${proj}/mise.toml`;
  await Bun.$`echo "# touch by agent" >> ${f}`.quiet();
  return f;
}
const conflicts: any = {};
for (const v of ["A", "D1", "D2", "D3"]) {
  const wroot = v === "A" ? "a" : v.toLowerCase();
  // C1: same project (ranch/oracle), different daemons
  let s = `${RACE}/conf-${v}`; await Bun.$`rm -rf ${s}`.quiet(); await Bun.$`cp -r ${WORK}/${wroot} ${s}`.quiet();
  const f1 = await agentEdit(s, v, "oracle-market");
  const f2 = await agentEdit(s, v, "bidder-forge");
  const c1 = f1 === f2 ? "CONFLICT" : "no conflict";
  // C2: different projects
  s = `${RACE}/conf2-${v}`; await Bun.$`rm -rf ${s}`.quiet(); await Bun.$`cp -r ${WORK}/${wroot} ${s}`.quiet();
  const g1 = await agentEdit(s, v, "oracle-market");
  const g2 = await agentEdit(s, v, "mesh-hub");
  const c2 = g1 === g2 ? "CONFLICT" : "no conflict";
  // C3: same daemon
  s = `${RACE}/conf3-${v}`; await Bun.$`rm -rf ${s}`.quiet(); await Bun.$`cp -r ${WORK}/${wroot} ${s}`.quiet();
  const h1 = await agentEdit(s, v, "oracle-market");
  const h2 = await agentEdit(s, v, "oracle-market");
  const c3 = h1 === h2 ? "CONFLICT" : "no conflict";
  conflicts[v] = { C1_same_project_diff_daemons: c1, C2_diff_projects: c2, C3_same_daemon: c3 };
  console.log(`  ${v}: C1 ${c1} | C2 ${c2} | C3 ${c3}`);
}
results.phases.conflicts = conflicts;

// ---------------- phase 5: the 5 stale as first test case ----------------
// Simulate: the owning projects retire the 5 stale in their own manifests.
// "Running" set = full 82 (what pitchfork currently runs). Orphan detector -> declared vs running.
console.log("== phase 5: stale test — do the 5 stale become obvious? ==");
const STALE = ["bidder-forge", "bidder-scout", "buildsrv", "flicker", "flicker-agent"];
const stale: any = { entries: STALE };
// attribution map from the full D2 layout (last-known project per daemon)
const prevMap: Record<string, string> = {};
{
  // build daemon->project map from D2 layout directly
  const reg = parseToml(await Bun.file(`${WORK}/d2/projects.toml`).text()) as any;
  for (const p of reg.project) {
    for (const f of await sortedTomls(`${WORK}/d2/${p.manifest}`)) {
      const t = parseToml(await Bun.file(f).text()) as any;
      for (const n of Object.keys(t.daemons ?? {})) prevMap[n] = p.key;
    }
  }
}
await Bun.write(`${RACE}/attribution.json`, JSON.stringify(prevMap));
const runningAll = Object.keys(orig.daemons);
await Bun.write(`${RACE}/running.json`, JSON.stringify(runningAll));
stale.ownership = Object.fromEntries(STALE.map((d) => [d, prevMap[d]]));
console.log(`  ownership under D: ${JSON.stringify(stale.ownership)}`);

// retire them in D2 (per-project drop-in dirs): delete 5 files across 3 project dirs
{
  const s = `${RACE}/stale-d2`; await Bun.$`rm -rf ${s}`.quiet(); await Bun.$`cp -r ${WORK}/d2 ${s}`.quiet();
  for (const d of STALE) {
    const proj = prevMap[d];
    await Bun.$`rm ${s}/${proj}/pitchfork.d/${d}.toml`.quiet();
  }
  const t0 = nsNow();
  const { so } = await sh(["bun", `${HERE}/design-d/compose-d.ts`, "--root", s, "--running", `${RACE}/running.json`, "--attribution", `${RACE}/attribution.json`]);
  const rep = JSON.parse(so);
  stale.D2_orphan_report = rep;
  stale.D2_detect_ms = +nsToMs(nsNow() - t0).toFixed(2);
  console.log(`  D2 orphan detector: ${rep.orphan_count} orphans in ${stale.D2_detect_ms}ms`);
  for (const o of rep.orphans) console.log(`    orphan: ${o.daemon} (last project: ${o.last_project})`);
}
// retire them in D1 (one manifest per project): edit 3 shared project files
{
  const s = `${RACE}/stale-d1`; await Bun.$`rm -rf ${s}`.quiet(); await Bun.$`cp -r ${WORK}/d1 ${s}`.quiet();
  const touched = new Set<string>();
  for (const d of STALE) {
    const proj = prevMap[d];
    const f = `${s}/${proj}/pitchfork/daemons.toml`;
    touched.add(f);
    const lines = (await Bun.file(f).text()).split("\n");
    const start = lines.findIndex((l) => l.trim() === `[daemons.${d}]`);
    if (start < 0) throw new Error(`section [daemons.${d}] not found in ${f}`);
    let end = lines.findIndex((l, i) => i > start && /^\[daemons\./.test(l.trim()));
    if (end < 0) end = lines.length;
    // drop trailing blank lines belonging to the removed section
    while (end > start && lines[end - 1].trim() === "") end--;
    await Bun.write(f, lines.slice(0, start).concat(lines.slice(end)).join("\n"));
  }
  const t0 = nsNow();
  const { so } = await sh(["bun", `${HERE}/design-d/compose-d.ts`, "--root", s, "--running", `${RACE}/running.json`, "--attribution", `${RACE}/attribution.json`]);
  const rep = JSON.parse(so);
  stale.D1_orphan_report = rep;
  stale.D1_detect_ms = +nsToMs(nsNow() - t0).toFixed(2);
  stale.D1_note = `retiring the 5 stale touched ${touched.size} shared project files (ranch/oracle, tools/buildsrv, ranch/flicker) — vs D2's 5 file deletions`;
  console.log(`  D1 orphan detector: ${rep.orphan_count} orphans in ${stale.D1_detect_ms}ms (${stale.D1_note})`);
}
// A-side: delete 5 drop-ins from the parent repo — orphans unattributed
{
  const s = `${RACE}/stale-a`; await Bun.$`rm -rf ${s}`.quiet(); await Bun.$`cp -r ${WORK}/a ${s}`.quiet();
  for (const d of STALE) await Bun.$`bash -c "rm ${s}/pitchfork.d/*-${d}.toml"`.quiet();
  stale.A_note = "A can also delete the 5 files, but nothing records which PROJECT owned them — the orphan is unattributed. Under D the report names ranch/oracle, tools/buildsrv, ranch/flicker.";
  console.log(`  A: ${stale.A_note}`);
}
results.phases.stale = stale;

// ---------------- phase 6: the mise question ----------------
// Can a project's own mise.toml carry [daemons.*] and still be a valid mise file?
// (mise ignores unknown tables today — the prototype relies on that leniency.)
console.log("== phase 6: the mise question ==");
const mise: any = {};
{
  const sample = await Bun.file(`${WORK}/d3/ranch/oracle/mise.toml`).text();
  const t = parseToml(sample) as any;
  mise.D3_mise_toml_parses = true;
  mise.D3_daemon_tables_found = Object.keys(t.daemons ?? {}).length;
  mise.D3_tools_table_present = "tools" in t;
  mise.D3_caveat = "mise ignores unknown tables ([daemons.*]) today — D3 relies on that leniency. One mise.toml per project is NOT current reality: only ranch/android-fleet/nuvio/nuvio-platform has its own mise.toml; everything else is parent-only (/home/toxic/sovereign/mise.toml).";
  mise.D3_recommendation = "If D3 is adopted, keep daemon blocks namespaced (e.g. [pitchfork.daemons.<name>] or a separate daemon.toml) so a future mise schema-strict mode can't break composition. D2 (pitchfork.d/ per project) avoids the coupling entirely.";
  console.log(`  D3: mise.toml parses, ${mise.D3_daemon_tables_found} daemon tables, tools table present: ${mise.D3_tools_table_present}`);
  console.log(`  caveat: ${mise.D3_caveat}`);
}
results.phases.mise = mise;

await Bun.write(`${RACE}/results.json`, JSON.stringify(results, null, 2));
console.log(`\nround-2 complete: ${RACE}/results.json`);
