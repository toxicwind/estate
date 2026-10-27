// design-a/merge-a.ts — pitchfork.d drop-ins merged at load (design A).
// Usage: bun merge-a.ts <parent.toml> <dropin-dir> [--out <merged.toml>] [--diff-old <prev-merged.toml>]
// Rules (borrowed: systemd drop-in discipline + supervisord loader + k3s naming):
//   - parent first, then drop-ins in lexical filename order (NN-name.toml)
//   - each drop-in owns exactly ONE [daemons.<name>] section, wholly (Shapiro [6]:
//     additive per-daemon-key => conflict-free map union, no resolution logic)
//   - a daemon name appearing in two files is an ERROR, never silent last-wins
//   - --diff-old implements the two-phase reload: parse+validate all, then report
//     the per-daemon diff so the caller re-registers ONLY changed daemons
//     (systemd daemon-reload semantics [D2]: reload definitions, restart nothing implicit)
import { parseToml, daemonDiff, atomicWrite, sortedTomls } from "../lib/toml.ts";

const [parent, dir, ...rest] = Bun.argv.slice(2);
if (!parent || !dir) {
  console.error("usage: bun merge-a.ts <parent.toml> <dropin-dir> [--out <f>] [--diff-old <f>]");
  process.exit(2);
}
const outIdx = rest.indexOf("--out");
const diffIdx = rest.indexOf("--diff-old");
const out = outIdx >= 0 ? rest[outIdx + 1] : null;
const diffOld = diffIdx >= 0 ? rest[diffIdx + 1] : null;

const parentText = await Bun.file(parent).text();
const files = await sortedTomls(dir);
if (files.length === 0) console.error("warning: no drop-ins matched (supervisord idiom: warning, not error)");

const seen = new Map<string, string>();
const parts = [parentText];
for (const f of files) {
  const text = await Bun.file(f).text();
  const sections = [...text.matchAll(/^\[daemons\.([^\]]+)\]/gm)].map((m) => m[1]);
  const fname = f.split("/").pop()!;
  if (sections.length !== 1) {
    console.error(`ERROR: ${fname}: must own exactly one [daemons.*] section, found ${sections.length}`);
    process.exit(3);
  }
  const name = sections[0];
  if (seen.has(name)) {
    console.error(`ERROR: daemon "${name}" owned by both ${seen.get(name)} and ${fname} — refusing silent last-wins`);
    process.exit(4);
  }
  seen.set(name, fname);
  parts.push(text);
}
const merged = parts.join("\n");

// validate: whole merged doc must parse, every daemon needs run+dir (SOSP [10]: validate in the same change)
let parsed: any;
try {
  parsed = parseToml(merged);
} catch (e: any) {
  console.error(`ERROR: merged config does not parse: ${e.message}`);
  process.exit(5);
}
const dn = Object.keys(parsed.daemons ?? {});
if (dn.length !== seen.size) {
  console.error(`ERROR: parsed ${dn.length} daemons but merged ${seen.size} drop-ins`);
  process.exit(6);
}
for (const n of dn) {
  const d = parsed.daemons[n];
  if (typeof d.run !== "string" || typeof d.dir !== "string") {
    console.error(`ERROR: daemon "${n}" missing run/dir`);
    process.exit(7);
  }
}

if (diffOld) {
  const oldParsed = parseToml(await Bun.file(diffOld).text());
  const diff = daemonDiff(oldParsed, parsed);
  console.log(JSON.stringify({ daemons: dn.length, ...diff }));
} else if (!out) {
  console.log(`merge-a: OK ${dn.length} daemons from ${files.length} drop-ins`);
}

if (out) await atomicWrite(out, merged);
