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

// 1. tau on PATH is the pinned launcher and the chain executes
try {
  const which = sh("sh", ["-c", "command -v tau"]);
  const expected = join(HOME, ".local/bin/tau");
  const ver = sh("tau", ["--version"], 30000).split("\n")[0];
  const ok = which === expected && /omp\/\d+\.\d+\.\d+/.test(ver);
  check("tau launcher resolves", ok, `${which} -> ${ver}`);
} catch (e: any) { check("tau launcher resolves", false, e.message.slice(0, 160)); }

// 2. Engine version >= 18.2.6 (semver compare; 18.3.x passes)
try {
  const ver = sh("tau", ["--version"], 30000).split("\n")[0];
  const m = ver.match(/(\d+)\.(\d+)\.(\d+)/);
  const parts = m ? [+m[1], +m[2], +m[3]] : [0, 0, 0];
  const min = [18, 2, 6];
  const ok = parts[0] > min[0] ||
    (parts[0] === min[0] && (parts[1] > min[1] || (parts[1] === min[1] && parts[2] >= min[2])));
  check("tau engine version >= 18.2.6", ok, ver);
} catch (e: any) { check("tau engine version >= 18.2.6", false, e.message.slice(0, 120)); }

// 3. PI_CONFIG_DIR honored
{
  const cfg = join(TAU_HOME, "config.yml");
  check("PI_CONFIG_DIR=.tau honored", existsSync(cfg), cfg);
}

// 4. Skills symlink + discoverability
{
  const link = join(TAU_HOME, "skills");
  let ok = false, detail = "missing";
  try {
    if (lstatSync(link).isSymbolicLink()) {
      const target = readlinkSync(link);
      const abs = target.startsWith("/") ? target : join(TAU_HOME, target);
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
