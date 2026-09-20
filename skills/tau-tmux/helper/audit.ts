#!/usr/bin/env bun
// tau-tmux audit helper — REAL checks against the live tau install.
// Usage: bun run helper/audit.ts [--verbose]
// Exit: 0 = all PASS, 1 = any FAIL. Every check observes the box; none are stubbed.
import { existsSync, lstatSync, readlinkSync, readdirSync } from "fs";
import { join } from "path";
import { execFileSync } from "child_process";

const HOME = process.env.HOME || "/home/toxic";
const TAU_HOME = join(HOME, ".tau");
const SOVEREIGN = join(HOME, "sovereign");
const verbose = process.argv.includes("--verbose") || process.argv.includes("-v");

interface Result { name: string; pass: boolean; detail: string }
const results: Result[] = [];
function check(name: string, pass: boolean, detail: string) {
  results.push({ name, pass, detail });
  console.log(`[${pass ? "PASS" : "FAIL"}] ${name}${verbose || !pass ? ` — ${detail}` : ""}`);
}
function sh(cmd: string, args: string[], timeoutMs = 15000): string {
  try {
    return execFileSync(cmd, args, { timeout: timeoutMs, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
  } catch (e: any) {
    throw new Error(e?.stderr?.toString?.().trim() || e?.message || String(e));
  }
}

// 1. tau on PATH is the launcher and the chain resolves
try {
  const which = sh("sh", ["-c", "command -v tau"]);
  const head = sh("head", ["-c", "200", which]);
  const isLauncher = head.includes("Tau Launcher");
  let resolved = "unresolved";
  if (isLauncher) {
    const distBin = join(SOVEREIGN, "projects/tau/engine/packages/coding-agent/dist/omp");
    if (existsSync(distBin)) resolved = `dist/omp`;
    else resolved = "bun src fallback";
  }
  check("tau launcher resolves", isLauncher && resolved !== "unresolved", `${which} -> ${resolved}`);
} catch (e: any) { check("tau launcher resolves", false, e.message); }

// 2. Engine version
try {
  const ver = sh("tau", ["--version"], 30000);
  check("tau engine version", /18\.2\.\d+/.test(ver), ver.split("\n")[0]);
} catch (e: any) { check("tau engine version", false, e.message.slice(0, 120)); }

// 3. PI_CONFIG_DIR honored
{
  const cfg = join(TAU_HOME, "agent", "config.yml");
  check("PI_CONFIG_DIR=.tau honored", existsSync(cfg), cfg);
}

// 4. Skills symlink + discoverability
{
  const link = join(TAU_HOME, "agent", "skills");
  let ok = false, detail = "missing";
  try {
    if (lstatSync(link).isSymbolicLink()) {
      const target = readlinkSync(link);
      const abs = target.startsWith("/") ? target : join(join(TAU_HOME, "agent"), target);
      if (existsSync(abs)) {
        let n = 0;
        for (const entry of readdirSync(abs, { withFileTypes: true })) {
          if (entry.isDirectory() && existsSync(join(abs, entry.name, "SKILL.md"))) n++;
        }
        ok = n > 0;
        detail = `${link} -> ${target} (${n} skills with SKILL.md)`;
      } else detail = `target missing: ${abs}`;
    } else detail = "not a symlink";
  } catch (e: any) { detail = e.message; }
  check("skills symlink live", ok, detail);
}

// 5. Routers reachable
for (const [name, url] of [["herd :25100", "http://127.0.0.1:25100/v1/models"], ["sovereign :25104", "http://127.0.0.1:25104/v1/models"]]) {
  try {
    const out = sh("curl", ["-s", "-m", "8", "-o", "/dev/null", "-w", "%{http_code}", url]);
    check(`${name} reachable`, out === "200", `HTTP ${out}`);
  } catch (e: any) { check(`${name} reachable`, false, e.message.slice(0, 120)); }
}

// 6. No stale config files
{
  const stale = ["nvidia.json", "cascade.json"].filter(f => existsSync(join(SOVEREIGN, f)));
  check("no stale nvidia/cascade json", stale.length === 0, stale.length ? `found: ${stale.join(", ")}` : "absent (provider catalog is models.yml)");
}

const failed = results.filter(r => !r.pass);
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
process.exit(failed.length ? 1 : 0);
