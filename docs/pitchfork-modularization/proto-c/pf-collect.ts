#!/usr/bin/env bun
/**
 * Design C: per-project fragments composed upward.
 * Each owning project keeps its daemon fragment colocated with its code:
 *   <project>/.daemon.toml   (holds that project's [daemons.*] tables)
 * projects.txt lists project dirs (one per line, relative to <dir>).
 * Ownership lives with the code; the composer discovers and merges.
 * Usage: pf-collect.ts <dir>   (dir holds pitchfork.toml + projects.txt + project dirs)
 */
import { parseFragment, compose, writeIfChanged } from "../harness/compose.ts";
import { join } from "node:path";

const dir = process.argv[2] ?? ".";
const parentPath = join(dir, "pitchfork.toml");

const parent = parseFragment(parentPath, await Bun.file(parentPath).text());
const projects = (await Bun.file(join(dir, "projects.txt")).text())
  .split("\n").map((s) => s.trim()).filter((s) => s && !s.startsWith("#"));

const frags = [];
for (const proj of projects) {
  const p = join(dir, proj, ".daemon.toml");
  const f = Bun.file(p);
  if (!(await f.exists())) {
    console.error(`WARN ${proj}: no .daemon.toml, skipped`);
    continue;
  }
  frags.push(parseFragment(p, await f.text()));
}
const t0 = performance.now();
const res = compose(parent, frags);
const dt = performance.now() - t0;

if (res.duplicates.length > 0) {
  for (const d of res.duplicates)
    console.error(`DUPLICATE daemon [${d.daemon}] in ${d.files[0]} and ${d.files[1]}`);
  process.exit(2);
}
const outPath = join(dir, "pitchfork.composed.toml");
const changed = await writeIfChanged(outPath, res.text);
console.log(JSON.stringify({
  design: "C", daemons: res.daemonNames.length, projects: frags.length,
  compose_ms: +dt.toFixed(3), bytes: res.text.length, changed, out: outPath,
}));
