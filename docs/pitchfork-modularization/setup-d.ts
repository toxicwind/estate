// setup-d.ts — round-2 layouts: PER-PROJECT OWNERSHIP (Chris's reframe, 2026-09-30).
// The parent composes; each project owns its daemon definition(s).
//   d1/  <key>/pitchfork/daemons.toml     — one manifest file per project
//   d2/  <key>/pitchfork.d/<daemon>.toml  — per-project drop-in dirs (A x D synthesis)
//   d3/  <key>/mise.toml                  — [daemons.*] blocks in the project's own mise.toml
//   Each variant also gets parent.toml (preamble + groups: composition-level, parent-owned)
//   and projects.toml (the parent's project registry: key -> manifest path).
// Sandbox only — never touches live config. Does NOT wipe ./work (round-1 artifacts stay).
import { parseToml, serVal } from "./lib/toml.ts";

const ORIG = "./pitchfork.toml.orig";
const SOV = "/home/toxic/estate";

interface Block { kind: "daemon" | "groups"; name: string; text: string; dir?: string }

function splitBlocks(src: string): { preamble: string; blocks: Block[] } {
  const lines = src.split("\n");
  let i = 0;
  const pre: string[] = [];
  while (i < lines.length && !/^\[/.test(lines[i])) { pre.push(lines[i]); i++; }
  const preamble = pre.join("\n");
  const blocks: Block[] = [];
  let pending: string[] = [];
  while (i < lines.length) {
    const m = lines[i].match(/^\[(daemons|groups)\.([^\]]+)\]/);
    if (!m) { pending.push(lines[i]); i++; continue; }
    const kind = (m[1] === "daemons" ? "daemon" : "groups") as "daemon" | "groups";
    const name = m[2];
    const body: string[] = [lines[i]];
    i++;
    while (i < lines.length && !/^\[(daemons|groups)\./.test(lines[i])) { body.push(lines[i]); i++; }
    while (body.length && body[body.length - 1].trim() === "") { pending.unshift(body.pop()!); }
    blocks.push({ kind, name, text: pending.join("\n") + (pending.length ? "\n" : "") + body.join("\n") + "\n" });
    pending = [];
  }
  return { preamble, blocks };
}

// Ground-truth ownership signal: the daemon's working dir, from the real config.
// Relative dirs resolve against /home/toxic/estate.
function projectKey(dir: string, daemon: string): string {
  let d = dir;
  if (!d) return "sovereign";
  if (!d.startsWith("/")) d = SOV + "/" + d;
  if (d === SOV) return "sovereign";
  const ranch = SOV + "/projects/range/ranch/";
  if (d.startsWith(ranch)) {
    const rest = d.slice(ranch.length).split("/").filter(Boolean);
    if (rest[0] === "barn" && rest[1]) return `ranch/barn/${rest[1]}`; // barn/gatehouse stays distinct
    return `ranch/${rest[0]}`;
  }
  if (d === SOV + "/projects/range") return "range";
  if (d.startsWith(SOV + "/projects/range/")) return `range/${d.slice((SOV + "/projects/range/").length).split("/").filter(Boolean)[0]}`;
  if (d.startsWith(SOV + "/projects/")) return `projects/${d.slice((SOV + "/projects/").length).split("/").filter(Boolean)[0]}`;
  if (d.startsWith(SOV + "/tools/")) return `tools/${d.slice((SOV + "/tools/").length).split("/").filter(Boolean)[0]}`;
  if (d.startsWith(SOV + "/")) return "sovereign"; // config/, engines/, ops/, agents/, *-search: parent's own estate
  if (d === "/home/toxic") {
    // runs from $HOME: attribute by daemon name (tau, awrawr-*, codebase-memory)
    if (daemon === "tau") return "standalone/tau";
    if (daemon.startsWith("awrawr-")) return "standalone/awrawr";
    return `standalone/${daemon}`;
  }
  if (d.startsWith("/home/toxic/")) {
    const rest = d.slice("/home/toxic/".length).split("/").filter(Boolean);
    if (rest[0] === ".fleet-bus") return "standalone/squawk-relay";
    if (rest[0] === "projects") return `standalone/${rest[1]}`; // /home/toxic/projects/rig-work
    return `standalone/${rest[0]}`;
  }
  return "standalone/unknown";
}

const src = await Bun.file(ORIG).text();
const { preamble, blocks } = splitBlocks(src);
const daemons = blocks.filter((b) => b.kind === "daemon");
const groups = blocks.filter((b) => b.kind === "groups");
for (const d of daemons) d.dir = (parseToml(d.text) as any).daemons[d.name].dir ?? "";
console.log(`split: ${daemons.length} daemons, ${groups.length} groups`);

const byProject = new Map<string, Block[]>();
for (const d of daemons) {
  const k = projectKey(d.dir!, d.name);
  if (!byProject.has(k)) byProject.set(k, []);
  byProject.get(k)!.push(d);
}
const order = [...byProject.keys()].sort((a, b) => {
  const rank = (k: string) => k === "sovereign" ? 0 : k.startsWith("ranch/") ? 1 : k.startsWith("range") ? 2 : k.startsWith("tools/") ? 3 : k.startsWith("projects/") ? 4 : 5;
  return rank(a) - rank(b) || (a < b ? -1 : 1);
});
for (const k of order) console.log(`  ${k}: ${byProject.get(k)!.length} daemons`);

const D1 = "./work/d1", D2 = "./work/d2", D3 = "./work/d3";
await Bun.$`rm -rf ${D1} ${D2} ${D3}`.quiet();

const parentToml = preamble + "\n" + groups.map((g) => g.text).join("\n");
const reg1: string[] = [], reg2: string[] = [], reg3: string[] = [];
reg1.push("# The parent's project registry. The parent COMPOSES; it does not own daemon stanzas.");
reg1.push("# Removing a project = delete its directory + one line here. Adding one = the reverse.");
reg2.push(...reg1); reg3.push(...reg1);

for (const k of order) {
  const ds = byProject.get(k)!.sort((a, b) => (a.name < b.name ? -1 : 1));
  const p1 = `${D1}/${k}/pitchfork`, p2 = `${D2}/${k}/pitchfork.d`, p3 = `${D3}/${k}`;
  await Bun.$`mkdir -p ${p1} ${p2} ${p3}`.quiet();

  // D1: one manifest per project, original text (comments preserved — the project owns this file)
  await Bun.write(`${p1}/daemons.toml`,
    `# ${k} — project-owned daemon manifest. This file is the source of truth for ${k}'s daemons.\n` +
    `# Owned by the ${k} project; the parent at /home/toxic/estate only composes it.\n\n` +
    ds.map((d) => d.text).join("\n"));

  // D2: per-project drop-in dir, one daemon per file
  for (const d of ds) await Bun.write(`${p2}/${d.name}.toml`, d.text);

  // D3: the project's own mise.toml carries [daemons.*] blocks (the mise question)
  const daemonBlocks = ds.map((d) => {
    const obj = (parseToml(d.text) as any).daemons[d.name];
    const keys = Object.keys(obj);
    return `[daemons.${d.name}]\n` + keys.map((kk) => `${kk} = ${serVal(obj[kk])}`).join("\n");
  }).join("\n\n");
  await Bun.write(`${p3}/mise.toml`,
    `# ${k} — project-owned mise config.\n` +
    `# Daemon definitions live WITH the project (the mise question: one mise.toml per project).\n` +
    `[tools]\n# project tool pins go here\n\n` + daemonBlocks + "\n");

  const entry = (manifest: string, kind?: string) =>
    `[[project]]\nkey = "${k}"\nmanifest = "${manifest}"` + (kind ? `\nkind = "${kind}"` : "") + "\n";
  reg1.push(entry(`${k}/pitchfork/daemons.toml`));
  reg2.push(entry(`${k}/pitchfork.d`, "dir"));
  reg3.push(entry(`${k}/mise.toml`));
}

await Bun.write(`${D1}/parent.toml`, parentToml);
await Bun.write(`${D2}/parent.toml`, parentToml);
await Bun.write(`${D3}/parent.toml`, parentToml);
await Bun.write(`${D1}/projects.toml`, reg1.join("\n"));
await Bun.write(`${D2}/projects.toml`, reg2.join("\n"));
await Bun.write(`${D3}/projects.toml`, reg3.join("\n"));
console.log(`round-2 layouts ready: ${order.length} projects across d1/d2/d3`);
