#!/usr/bin/env bun
// Permanent workspace merger. Lives in engine/scripts/.
// Unions [workspace].members and [workspace].dependencies (including features).
import { $, TOML } from "bun";
import { dirname, resolve } from "node:path";

const HERE   = dirname(new URL(import.meta.url).pathname);
const ENGINE = resolve(HERE, "..");
const E_TOML = resolve(ENGINE, "Cargo.toml");
const V_TOML = resolve(ENGINE, "..", "vendor", "oh-my-pi", "Cargo.toml");

const log = (...a: unknown[]) => console.log("[merge]", ...a);

async function parse(path: string, label: string): Promise<any> {
  const t = await Bun.file(path).text();
  try { return TOML.parse(t); }
  catch (e) { throw new Error(`${label} TOML invalid: ${(e as Error).message}`); }
}

const e = await parse(E_TOML, "engine");
const v = await parse(V_TOML, "vendor");
if (!e.workspace) throw new Error("engine has no [workspace]");
if (!v.workspace) throw new Error("vendor has no [workspace]");

// members
const em = new Set<string>((e.workspace.members ?? []) as string[]);
const addedM: string[] = [];
for (const m of ((v.workspace.members ?? []) as string[]))
  if (!em.has(m)) { em.add(m); addedM.push(m); }
e.workspace.members = [...em].sort();

// dependencies + features union
const ed = (e.workspace.dependencies ?? {}) as Record<string, any>;
const vd = (v.workspace.dependencies ?? {}) as Record<string, any>;
const addedD: string[] = [];

for (const [k, vv] of Object.entries(vd)) {
  if (!(k in ed)) { ed[k] = vv; addedD.push(k); continue; }
  const ev = ed[k];
  if (ev && typeof ev === "object" && vv && typeof vv === "object") {
    const ef = new Set<string>(ev.features ?? []);
    const before = ef.size;
    for (const f of (vv.features ?? []) as string[]) ef.add(f);
    if (ef.size !== before) {
      ev.features = [...ef].sort();
      addedD.push(`${k} (features +${ef.size - before})`);
    }
    // prefer permissive default-features
    if (vv["default-features"] === true) ev["default-features"] = true;
  }
}
e.workspace.dependencies = ed;

if (addedM.length === 0 && addedD.length === 0) {
  log("already in sync — no write");
  process.exit(0);
}

await Bun.write(E_TOML, TOML.stringify(e) + "\n");
log(`members +${addedM.length}: ${addedM.join(", ") || "-"}`);
log(`deps    +${addedD.length}: ${addedD.join(", ") || "-"}`);
