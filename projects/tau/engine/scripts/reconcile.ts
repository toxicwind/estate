#!/usr/bin/env bun
// Permanent reconciler. Runs the full loop:
//   recover manifest → merge workspace → cargo metadata verify → build → embed → probe
// Auto-detects and reports the build cache on every run.
import { $, TOML } from "bun";
import { dirname, resolve } from "node:path";

const HERE   = dirname(new URL(import.meta.url).pathname);
const ENGINE = resolve(HERE, "..");
const E_TOML = resolve(ENGINE, "Cargo.toml");
const V_TOML = resolve(ENGINE, "..", "vendor", "oh-my-pi", "Cargo.toml");

const log  = (...a: unknown[]) => console.log("[reconcile]", ...a);
const warn = (...a: unknown[]) => console.warn("[reconcile]", ...a);
const die  = (...a: unknown[]) => { console.error("[reconcile]", ...a); process.exit(1); };

async function cacheInfo() {
  const r = await $`cargo metadata --no-deps --format-version 1`.cwd(ENGINE).quiet();
  const m = JSON.parse(r.stdout.toString());
  const sccache = (await $`which sccache`.nothrow().quiet()).exitCode === 0;
  return { targetDir: m.target_directory, sccache };
}

async function verify() {
  const r = await $`cargo metadata --no-deps --format-version 1`.cwd(ENGINE).nothrow().quiet();
  if (r.exitCode !== 0) die("cargo metadata failed:\n" + r.stderr.toString().split("\n").slice(0, 20).join("\n"));
  log("cargo metadata OK");
}

async function build() {
  log("building pi-natives");
  const r = await $`bun run --cwd packages/natives build`.cwd(ENGINE).nothrow();
  if (r.exitCode !== 0) die("build failed");
  log("build OK");
}

async function embed() {
  const p = resolve(ENGINE, "packages/natives/scripts/embed-native.ts");
  if (!(await Bun.file(p).exists())) { log("no embed script"); return; }
  log("embedding");
  const r = await $`bun ${p}`.cwd(ENGINE).nothrow();
  if (r.exitCode !== 0) die("embed failed");
}

async function probe(): Promise<boolean> {
  const code = `
    const { loadNative } = require("./packages/natives/native/loader-state.js");
    const b = loadNative();
    const s = Object.keys(b).find(k => k.startsWith("__piNativesV"));
    const need = ["NativeOAuthCallback","EditSession","EditStore","VcsRepo","VcsGitRepo","VcsJjWorkspace"];
    const missing = need.filter(k => !(k in b));
    console.log("SENTINEL=" + s);
    console.log("MISSING=" + JSON.stringify(missing));
  `;
  const r = await $`bun -e ${code}`.cwd(ENGINE).nothrow();
  const out = r.stdout.toString() + r.stderr.toString();
  const sentinel = out.match(/SENTINEL=(\S+)/)?.[1] ?? "(none)";
  const missing  = out.match(/MISSING=(\[[^\]]*\])/)?.[1] ?? "(unknown)";
  log(`sentinel: ${sentinel}`);
  log(`missing : ${missing}`);
  return missing === "[]" && sentinel !== "(none)";
}

// COUPLED_CRATES_EXPANSION
// Before building, ensure any crate in a coupled pair is present in the
// workspace members list with its partner. If not, sync from vendor.
{
  const fs = require("node:fs") as typeof import("node:fs");
  const path = require("node:path") as typeof import("node:path");
  const here = new URL(".", import.meta.url).pathname;
  const coupledPath = path.join(here, "coupled-crates.json");
  if (fs.existsSync(coupledPath)) {
    const { pairs } = JSON.parse(fs.readFileSync(coupledPath, "utf8")) as { pairs: string[][] };
    const vendorRoot = path.resolve(here, "..", "..", "vendor", "oh-my-pi", "crates");
    const engineRoot = path.resolve(here, "..", "crates");
    for (const group of pairs) {
      const present = group.filter((c) => fs.existsSync(path.join(engineRoot, c)));
      if (present.length !== group.length) {
        for (const c of group) {
          const src = path.join(vendorRoot, c);
          const dst = path.join(engineRoot, c);
          if (fs.existsSync(src)) {
            const r = Bun.spawnSync(["rsync", "-a", "--delete",
              "--exclude", "target/", "--exclude", "node_modules/", "--exclude", ".git/",
              src + "/", dst + "/"]);
            console.log(`[reconcile] coupled sync ${c}: exit ${r.exitCode}`);
          }
        }
      }
    }
  }
}

const cmd = (process.argv[2] ?? "all").toLowerCase();
const ci = await cacheInfo();
log(`engine   : ${ENGINE}`);
log(`target   : ${ci.targetDir}`);
log(`sccache  : ${ci.sccache ? "on" : "off"}`);
log(`cmd      : ${cmd}`);

try {
  if (cmd === "merge" || cmd === "all") {
    const r = await $`bun ${HERE}/merge-workspace.ts`.nothrow();
    if (r.exitCode !== 0) die("merge failed");
    await verify();
  }
  if (cmd === "verify") await verify();
  if (cmd === "build" || cmd === "all") await build();
  if (cmd === "embed" || cmd === "all") await embed();
  if (cmd === "probe" || cmd === "all") {
    if (!(await probe())) process.exit(1);
  }
} catch (e) {
  die((e as Error).message);
}
