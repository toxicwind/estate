// setup.ts — split the sandbox pitchfork.toml.orig into the three prototype layouts.
// Run once: bun setup.ts
// Layouts (all under ./work/, sandbox only — never touches live config):
//   a/  parent pitchfork.toml + pitchfork.d/NN-name.toml drop-ins (design A)
//   b/  base.toml + daemons.d/<name>.toml typed manifests + retired.toml (design B)
//   c/  fragments/NN-*.toml composed root->leaf (design C)
import { parseToml, serVal } from "./lib/toml.ts";

const ORIG = "./pitchfork.toml.orig";
const WORK = "./work";

interface Block { kind: "daemon" | "groups"; name: string; text: string; dir?: string }

function splitBlocks(src: string): { preamble: string; blocks: Block[] } {
  const lines = src.split("\n");
  let i = 0;
  const pre: string[] = [];
  while (i < lines.length && !/^\[/.test(lines[i])) { pre.push(lines[i]); i++; }
  const preamble = pre.join("\n");
  const blocks: Block[] = [];
  let pending: string[] = []; // comments/blanks leading the next section
  while (i < lines.length) {
    const m = lines[i].match(/^\[(daemons|groups)\.([^\]]+)\]/);
    if (!m) { pending.push(lines[i]); i++; continue; }
    const kind = (m[1] === "daemons" ? "daemon" : "groups") as "daemon" | "groups";
    const name = m[2];
    const body: string[] = [lines[i]];
    i++;
    while (i < lines.length && !/^\[(daemons|groups)\./.test(lines[i])) { body.push(lines[i]); i++; }
    // strip trailing blank lines from body, keep them as pending for next block
    while (body.length && body[body.length - 1].trim() === "") { pending.unshift(body.pop()!); }
    blocks.push({ kind, name, text: pending.join("\n") + (pending.length ? "\n" : "") + body.join("\n") + "\n" });
    pending = [];
  }
  return { preamble, blocks };
}

function projectOf(dir: string): string {
  if (dir === "." || dir === "/home/toxic/estate") return "10-root";
  if (dir.includes("/ranch/")) return "20-ranch";
  if (dir.includes("/tools/")) return "30-tools";
  return "40-home";
}

const src = await Bun.file(ORIG).text();
const { preamble, blocks } = splitBlocks(src);
const daemons = blocks.filter((b) => b.kind === "daemon");
const groups = blocks.filter((b) => b.kind === "groups");
console.log(`split: ${daemons.length} daemons, ${groups.length} groups`);

// resolve dir per daemon for design-C grouping
for (const d of daemons) {
  const p = parseToml(d.text) as any;
  d.dir = p.daemons[d.name].dir;
}

await Bun.$`rm -rf ${WORK}`.quiet();
const A = `${WORK}/a`, B = `${WORK}/b`, C = `${WORK}/c`;
await Bun.$`mkdir -p ${A}/pitchfork.d ${B}/daemons.d ${C}/fragments`.quiet();

// ---- design A: parent + drop-ins ----
await Bun.write(`${A}/pitchfork.toml`, preamble + "\n" + groups.map((g) => g.text).join("\n"));
daemons.forEach((d, idx) => {
  const nn = String(idx + 1).padStart(2, "0");
  return Bun.write(`${A}/pitchfork.d/${nn}-${d.name}.toml`, d.text);
});

// ---- design B: base + typed manifests + retired list ----
await Bun.write(`${B}/base.toml`, preamble + "\n" + groups.map((g) => g.text).join("\n"));
for (const d of daemons) {
  const p = parseToml(d.text) as any;
  const obj = p.daemons[d.name];
  const keys = Object.keys(obj);
  const leading = d.text.split(/^\[daemons\./m)[0]; // preserve human comments
  const manifest =
    leading +
    `[daemon]\nname = ${serVal(d.name)}\n` +
    keys.map((k) => `${k} = ${serVal(obj[k])}`).join("\n") +
    "\n";
  await Bun.write(`${B}/daemons.d/${d.name}.toml`, manifest);
}
await Bun.write(
  `${B}/retired.toml`,
  `# Explicit retirement ledger (replaces silent drift like the 5 stale entries).\n` +
    `# A manifest MUST NOT exist for a retired name — the generator errors if it does.\n` +
    `retired = [ "bidder-forge", "bidder-scout", "buildsrv", "flicker", "flicker-agent" ]\n`
);

// ---- design C: per-project fragments, root -> leaf ----
await Bun.write(`${C}/fragments/00-base.toml`, preamble + "\n" + groups.map((g) => g.text).join("\n"));
const buckets = new Map<string, Block[]>();
for (const d of daemons) {
  const b = projectOf(d.dir!);
  if (!buckets.has(b)) buckets.set(b, []);
  buckets.get(b)!.push(d);
}
for (const [bucket, ds] of [...buckets.entries()].sort()) {
  await Bun.write(`${C}/fragments/${bucket}.toml`, ds.map((d) => d.text).join("\n"));
}
await Bun.write(`${C}/fragments/99-local.toml`, `# leaf override layer — empty until an operator needs a local override\n`);

console.log("design A: parent +", daemons.length, "drop-ins");
console.log("design B: base +", daemons.length, "manifests + retired.toml");
for (const [b, ds] of [...buckets.entries()].sort()) console.log(`design C: fragments/${b}.toml: ${ds.length} daemons`);
console.log("layouts ready under ./work/");
