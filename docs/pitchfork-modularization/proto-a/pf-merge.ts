#!/usr/bin/env bun
/**
 * Design A: pitchfork.d/*.toml drop-ins merged at load.
 * Parent pitchfork.toml stays the entrypoint (globals + preamble); operators add
 * grouped drop-in files under pitchfork.d/. Lexicographic order; duplicates fail loud.
 * Usage: pf-merge.ts <dir>   (dir holds pitchfork.toml + pitchfork.d/)
 */
import { parseFragment, compose, writeIfChanged } from "../harness/compose.ts";
import { readdir } from "node:fs/promises";
import { join } from "node:path";

const dir = process.argv[2] ?? ".";
const parentPath = join(dir, "pitchfork.toml");
const dropDir = join(dir, "pitchfork.d");

const parent = parseFragment(parentPath, await Bun.file(parentPath).text());
const files = (await readdir(dropDir)).filter((f) => f.endsWith(".toml")).sort();
const frags = [];
for (const f of files) {
  const p = join(dropDir, f);
  frags.push(parseFragment(p, await Bun.file(p).text()));
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
  design: "A", daemons: res.daemonNames.length, fragments: files.length,
  compose_ms: +dt.toFixed(3), bytes: res.text.length, changed, out: outPath,
}));
