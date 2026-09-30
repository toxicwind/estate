#!/usr/bin/env bun
/**
 * Design B: per-daemon manifests compiled into pitchfork.toml.
 * daemons.d/<name>.toml — exactly one [daemons.<name>] table per file.
 * One daemon per file = parallel writers never touch the same file.
 * Usage: pf-build.ts <dir>   (dir holds pitchfork.toml preamble + daemons.d/)
 */
import { parseFragment, compose, writeIfChanged } from "../harness/compose.ts";
import { readdir } from "node:fs/promises";
import { join } from "node:path";

const dir = process.argv[2] ?? ".";
const parentPath = join(dir, "pitchfork.toml");
const dDir = join(dir, "daemons.d");

const parent = parseFragment(parentPath, await Bun.file(parentPath).text());
const files = (await readdir(dDir)).filter((f) => f.endsWith(".toml")).sort();
const frags = [];
for (const f of files) {
  const p = join(dDir, f);
  const frag = parseFragment(p, await Bun.file(p).text());
  if (frag.daemons.size !== 1)
    console.error(`WARN ${p}: holds ${frag.daemons.size} daemon tables (expected 1)`);
  frags.push(frag);
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
  design: "B", daemons: res.daemonNames.length, fragments: files.length,
  compose_ms: +dt.toFixed(3), bytes: res.text.length, changed, out: outPath,
}));
