#!/usr/bin/env bun
/**
 * split-fixtures.ts — build proto fixtures from a monolithic pitchfork.toml.
 * Usage: split-fixtures.ts <orig.toml> <lane-root>
 * Produces:
 *   proto-a/: pitchfork.toml (preamble) + pitchfork.d/{10..17}-group<N>.toml (8 groups)
 *   proto-b/: pitchfork.toml (preamble) + daemons.d/<sanitized-name>.toml (1 per daemon)
 *   proto-c/: pitchfork.toml (preamble) + projects.txt + proj-<p>/.daemon.toml
 *             (projects derived from daemon name prefix before '/')
 */
import { parseFragment } from "./compose.ts";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";

const [origPath, root] = process.argv.slice(2);
if (!origPath || !root) { console.error("usage: split-fixtures.ts <orig.toml> <lane-root>"); process.exit(1); }

const text = await Bun.file(origPath).text();
const frag = parseFragment(origPath, text);
const names = [...frag.daemons.keys()].sort();
console.log(`daemons: ${names.length}, preamble lines: ${frag.preamble.length}`);

const parentText = frag.preamble.join("\n").replace(/\n+$/, "") + "\n";
const sanitized = (n: string) => n.replace(/[^a-zA-Z0-9_.-]/g, "_");

// ---- Design A: 8 grouped drop-ins ----
const aDir = join(root, "proto-a");
await mkdir(join(aDir, "pitchfork.d"), { recursive: true });
await Bun.write(join(aDir, "pitchfork.toml"), parentText);
const GROUPS = 8;
for (let g = 0; g < GROUPS; g++) {
  const chunk = names.filter((_, i) => i % GROUPS === g);
  const lines: string[] = [`# design A drop-in: group ${g} (${chunk.length} daemons)`];
  for (const n of chunk) { lines.push(""); lines.push(...frag.daemons.get(n)!); }
  await Bun.write(join(aDir, "pitchfork.d", `1${g}-group${g}.toml`), lines.join("\n").replace(/\n+$/, "") + "\n");
}

// ---- Design B: one file per daemon ----
const bDir = join(root, "proto-b");
await mkdir(join(bDir, "daemons.d"), { recursive: true });
await Bun.write(join(bDir, "pitchfork.toml"), parentText);
for (const n of names) {
  const lines = [`# design B manifest: [daemons.${n}]`, "", ...frag.daemons.get(n)!];
  await Bun.write(join(bDir, "daemons.d", `${sanitized(n)}.toml`), lines.join("\n").replace(/\n+$/, "") + "\n");
}

// ---- Design C: per-project fragments (project derived from dir/run ownership) ----
const cDir = join(root, "proto-c");
await mkdir(cDir, { recursive: true });
await Bun.write(join(cDir, "pitchfork.toml"), parentText);

function projectOf(lines: string[]): string {
  const text = lines.join("\n");
  const dirM = /^\s*dir\s*=\s*"([^"]+)"/m.exec(text);
  const runM = /^\s*run\s*=\s*"([^"]+)"/m.exec(text);
  const candidates: string[] = [];
  if (dirM) candidates.push(dirM[1]);
  if (runM) {
    // scan every token: prefer one rooted at the sovereign tree
    for (const tok of runM[1].replace(/^exec\s+/, "").split(/\s+/)) {
      if (tok.includes("/home/toxic/estate/")) candidates.push(tok);
    }
    if (candidates.length === 0) {
      const tok0 = runM[1].replace(/^exec\s+/, "").split(/\s+/)[0] ?? "";
      if (tok0.includes("/")) candidates.push(tok0);
    }
  }
  for (const c of candidates) {
    let p = c.replace(/^\/home\/toxic\/sovereign\//, "").replace(/^\.\//, "");
    if (!p || p === ".") continue;
    const parts = p.split("/").filter(Boolean);
    // drop a trailing file component (has a dot) so proj ~= owning dir
    if (parts.length > 2 && parts[parts.length - 1].includes(".")) parts.pop();
    const proj = parts.slice(0, 2).join("/");
    if (proj) return proj;
  }
  return "misc";
}

const byProj = new Map<string, string[]>();
for (const n of names) {
  const proj = projectOf(frag.daemons.get(n)!);
  if (!byProj.has(proj)) byProj.set(proj, []);
  byProj.get(proj)!.push(n);
}
const projs = [...byProj.keys()].sort();
const projLines: string[] = ["# project dirs owning daemon fragments (design C)"];
for (const p of projs) {
  const slug = "proj-" + p.replace(/\//g, "-");
  const pd = join(cDir, slug);
  await mkdir(pd, { recursive: true });
  const lines: string[] = [`# design C fragment: project ${p} (${byProj.get(p)!.length} daemons)`];
  for (const n of byProj.get(p)!) { lines.push(""); lines.push(...frag.daemons.get(n)!); }
  await Bun.write(join(pd, ".daemon.toml"), lines.join("\n").replace(/\n+$/, "") + "\n");
  projLines.push(slug);
}
await Bun.write(join(cDir, "projects.txt"), projLines.join("\n") + "\n");
console.log(`A: 8 drop-ins | B: ${names.length} manifests | C: ${projs.length} projects`);
