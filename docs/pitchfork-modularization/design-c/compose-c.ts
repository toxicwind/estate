// design-c/compose-c.ts — per-project fragments composed root->leaf (design C).
// Usage: bun compose-c.ts <fragments-dir> [--out <merged.toml>] [--explain <daemon> <key>]
// Rules (borrowed: docker compose mergeSpecials — an EXPLICIT per-field strategy
// table, never one implicit global rule):
//   scalars (port/run/dir/mise/retry/boot_start/ready_http/ready_cmd) .. leaf wins (full replace)
//   env (map) ...................................................... deep-merge, leaf wins per key
//   auto/depends/groups.daemons (arrays) ........................... append-with-dedup
//   health_http/health_port/ready_port (inline tables) ............. deep-merge, leaf wins per key
//   env_file (top-level scalar) .................................... leaf wins
// --explain answers the CUE critique ([D5]) directly: for any daemon+key it shows
// every layer's value and which layer won, so "which layer won" is inspectable,
// not archaeology.
import { parseToml, serDaemon, serVal, atomicWrite, sortedTomls, deepEqual } from "../lib/toml.ts";

const SCALAR_REPLACE = new Set(["port", "run", "dir", "mise", "retry", "boot_start", "ready_http", "ready_cmd"]);
const MAP_MERGE = new Set(["env", "health_http", "health_port", "ready_port"]);
const ARRAY_APPEND = new Set(["auto", "depends"]);

const isObj = (v: any) => v !== null && typeof v === "object" && !Array.isArray(v);

function mergeVal(key: string, base: any, over: any): any {
  if (over === undefined) return base;
  if (base === undefined) return over;
  // map-merge only when BOTH sides are tables (ready_port can be a bare number: then leaf wins)
  if (MAP_MERGE.has(key) && isObj(base) && isObj(over)) return { ...base, ...over };
  if ((ARRAY_APPEND.has(key) || key === "daemons") && Array.isArray(base) && Array.isArray(over))
    return [...base, ...over.filter((x: any) => !base.some((b: any) => deepEqual(b, x)))];
  return over; // SCALAR_REPLACE + default: leaf wins, full replace
}

const [dir, ...rest] = Bun.argv.slice(2);
if (!dir) { console.error("usage: bun compose-c.ts <fragments-dir> [--out <f>] [--explain <daemon> <key>]"); process.exit(2); }
const outIdx = rest.indexOf("--out");
const expIdx = rest.indexOf("--explain");
const out = outIdx >= 0 ? rest[outIdx + 1] : null;

const files = await sortedTomls(dir);
const layers: { file: string; doc: any }[] = [];
for (const f of files) {
  try {
    layers.push({ file: f.split("/").pop()!, doc: parseToml(await Bun.file(f).text()) });
  } catch (e: any) {
    console.error(`ERROR: ${f.split("/").pop()}: does not parse: ${e.message}`);
    process.exit(3);
  }
}

if (expIdx >= 0) {
  const [daemon, key] = [rest[expIdx + 1], rest[expIdx + 2]];
  console.log(`explain ${daemon}.${key}:`);
  let winner: any;
  for (const l of layers) {
    const v = l.doc.daemons?.[daemon]?.[key];
    if (v !== undefined) { console.log(`  ${l.file}: ${JSON.stringify(v)}`); winner = v; }
    else console.log(`  ${l.file}: (unset)`);
  }
  console.log(`  => winner: ${JSON.stringify(winner)}`);
  process.exit(0);
}

// compose root -> leaf
const merged: any = {};
for (const l of layers) {
  const d = l.doc;
  for (const k of Object.keys(d)) {
    if (k === "daemons" || k === "groups") continue;
    merged[k] = mergeVal(k, merged[k], d[k]);
  }
  for (const sec of ["daemons", "groups"]) {
    if (!d[sec]) continue;
    merged[sec] ??= {};
    for (const name of Object.keys(d[sec])) {
      if (sec === "daemons") {
        const cur = merged.daemons[name] ?? {};
        const nxt: any = { ...cur };
        for (const k of Object.keys(d.daemons[name])) nxt[k] = mergeVal(k, cur[k], d.daemons[name][k]);
        merged.daemons[name] = nxt;
      } else {
        merged.groups[name] ??= {};
        for (const k of Object.keys(d.groups[name]))
          merged.groups[name][k] = mergeVal(k, merged.groups[name][k], d.groups[name][k]);
      }
    }
  }
}

const names = Object.keys(merged.daemons ?? {}).sort();
let text = "";
if (merged.env_file) text += `# composed from ${files.length} fragments (root -> leaf)\nenv_file = ${serVal(merged.env_file)}\n`;
for (const g of Object.keys(merged.groups ?? {}).sort())
  text += `\n[groups.${g}]\ndaemons = ${serVal(merged.groups[g].daemons)}\n`;
for (const n of names) text += "\n" + serDaemon(n, merged.daemons[n]);

if (!out) console.log(`compose-c: OK ${names.length} daemons from ${files.length} fragments`);
if (out) await atomicWrite(out, text);
