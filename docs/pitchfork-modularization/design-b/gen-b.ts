// design-b/gen-b.ts — generated config from per-daemon typed manifests (design B).
// Usage: bun gen-b.ts <base.toml> <manifests-dir> <retired.toml> [--out <merged.toml>]
// Rules (borrowed: NixOS typed modules [1], Dolstra atomicity [2], CUE conflicts-as-errors [D5]):
//   - manifest schema is SMALL and explicit (Xu/FSE'15 [3]): unknown keys are ERRORS,
//     not ignored; required keys (name, run) enforced; types checked
//   - same daemon in two manifests = ERROR (conflicts are errors, never magic [9])
//   - retired.toml is the explicit retirement ledger: a manifest for a retired
//     name is an ERROR — retirement is deliberate, never silent drift
//   - output is generated whole and swapped atomically (tmp + rename in same dir);
//     the live config is NEVER patched in place (the 2026-09-14 retired-generator
//     incident: a generator that "would destroy live daemons" — atomicity first)
import { parseToml, serDaemon, atomicWrite, sortedTomls } from "../lib/toml.ts";

// Small, explicit schema: name -> allowed typeof(s). Unknown key = error.
// Documented unions observed in the live config (the schema forces these to be
// explicit instead of tribal knowledge):
//   port:       number | array   (qdrant listens on [25133, 25134])
//   retry:      boolean | number (toolcall-llm: retry = 5 max attempts)
//   ready_port: number | object  (bare port today; probe table allowed)
const SCHEMA: Record<string, string[]> = {
  name: ["string"], run: ["string"], dir: ["string"], port: ["number", "array"],
  mise: ["boolean"], retry: ["boolean", "number"], boot_start: ["boolean"],
  auto: ["array"], env: ["object"], depends: ["array"],
  ready_http: ["string"], ready_cmd: ["string"], ready_port: ["number", "object"],
  health_http: ["object"], health_port: ["object"],
};
const typeOf = (v: any) => (Array.isArray(v) ? "array" : v === null ? "null" : typeof v);

const [base, mdir, retiredFile, ...rest] = Bun.argv.slice(2);
if (!base || !mdir || !retiredFile) {
  console.error("usage: bun gen-b.ts <base.toml> <manifests-dir> <retired.toml> [--out <f>]");
  process.exit(2);
}
const outIdx = rest.indexOf("--out");
const out = outIdx >= 0 ? rest[outIdx + 1] : null;

const baseText = await Bun.file(base).text();
const retired: string[] = (parseToml(await Bun.file(retiredFile).text()) as any).retired ?? [];
const files = await sortedTomls(mdir);

const manifests = new Map<string, Record<string, any>>();
for (const f of files) {
  const fname = f.split("/").pop()!;
  let p: any;
  try {
    p = parseToml(await Bun.file(f).text());
  } catch (e: any) {
    console.error(`ERROR: ${fname}: does not parse: ${e.message}`);
    process.exit(3);
  }
  const m = p.daemon;
  if (!m || typeof m.name !== "string") {
    console.error(`ERROR: ${fname}: missing [daemon] table with name`);
    process.exit(4);
  }
  // typed validation — conflicts-as-errors, unknown-knob rejection
  for (const k of Object.keys(m)) {
    if (!(k in SCHEMA)) {
      console.error(`ERROR: ${fname}: unknown key "${k}" (schema is explicit; add it deliberately or drop it)`);
      process.exit(5);
    }
    if (typeOf(m[k]) !== SCHEMA[k] && !SCHEMA[k].includes(typeOf(m[k]))) {
      console.error(`ERROR: ${fname}: key "${k}" must be ${SCHEMA[k].join(" | ")}, got ${typeOf(m[k])}`);
      process.exit(6);
    }
  }
  for (const req of ["name", "run"]) {
    if (!(req in m)) { console.error(`ERROR: ${fname}: missing required key "${req}"`); process.exit(7); }
  }
  if (retired.includes(m.name)) {
    console.error(`ERROR: ${fname}: "${m.name}" is in retired.toml — delete the manifest deliberately, not by drift`);
    process.exit(8);
  }
  if (manifests.has(m.name)) {
    console.error(`ERROR: daemon "${m.name}" defined in two manifests — conflicts are errors, resolve explicitly`);
    process.exit(9);
  }
  const { name, ...daemon } = m;
  manifests.set(m.name, daemon);
}

const names = [...manifests.keys()].sort();
let merged = baseText;
if (!merged.endsWith("\n")) merged += "\n";
for (const n of names) merged += "\n" + serDaemon(n, manifests.get(n)!);

// validate the generated artifact parses and is complete
let parsed: any;
try {
  parsed = parseToml(merged);
} catch (e: any) {
  console.error(`ERROR: generated config does not parse: ${e.message}`);
  process.exit(10);
}
if (Object.keys(parsed.daemons ?? {}).length !== names.length) {
  console.error("ERROR: generated daemon count mismatch");
  process.exit(11);
}

if (!out) console.log(`gen-b: OK ${names.length} daemons from ${files.length} manifests (${retired.length} retired)`);
if (out) await atomicWrite(out, merged);
