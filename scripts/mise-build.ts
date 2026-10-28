#!/usr/bin/env bun
/**
 * Estate Build Check - Pure TypeScript replacement for mise-build.sh.
 * Executes test suites through Bun and validates script syntax without invoking bash subprocess chains.
 */
import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { readdirSync, existsSync } from "node:fs";

const ROOT = resolve(import.meta.dir, "..");

console.log("Running estate test suite via Bun...");
const portTest = spawnSync("bun", ["test", "tests/ports.test.ts"], {
  cwd: ROOT,
  stdio: "inherit",
});
if (portTest.status !== 0) {
  process.exit(portTest.status ?? 1);
}

const uiTest = spawnSync("bun", ["test", "tests/open_web_uis.test.ts"], {
  cwd: ROOT,
  stdio: "inherit",
});
if (uiTest.status !== 0) {
  process.exit(uiTest.status ?? 1);
}

console.log("Verifying scripts directory syntax...");
const scriptsDir = resolve(ROOT, "scripts");
if (existsSync(scriptsDir)) {
  const files = readdirSync(scriptsDir);
  for (const file of files) {
    if (file.endsWith(".sh")) {
      const res = spawnSync("bash", ["-n", resolve(scriptsDir, file)], {
        stdio: "inherit",
      });
      if (res.status !== 0) {
        console.error(`Syntax error in ${file}`);
        process.exit(res.status ?? 1);
      }
    }
  }
}

console.log("Estate build check passed.");
