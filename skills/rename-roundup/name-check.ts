#!/usr/bin/env bun
// name-check.ts — Estate name availability checker using ffs
// Usage: bun run name-check.ts <candidate>

import { $ } from "bun";

const CANDIDATE = process.argv[2];
if (!CANDIDATE) {
  console.error("Usage: bun run name-check.ts <candidate>");
  process.exit(1);
}

const ESTATE = "/home/toxic/estate";

async function checkSource(name: string, cmd: string): Promise<string[]> {
  try {
    const proc = await $`bash -c ${cmd}`.quiet();
    const out = proc.stdout.toString().trim();
    return out ? out.split("\n").map(l => l.trim()).filter(Boolean) : [];
  } catch {
    return [];
  }
}

async function main() {
  console.log(`=== Checking '${CANDIDATE}' ===\n`);

  const checks = [
    ["Pitchfork daemons", `grep -oE '\\[daemons\\.[^]]+\\]' ${ESTATE}/pitchfork.toml | sed 's/\\[daemons\\.\(.*\)\\]/\\1/'`],
    ["Ranch folders", `ls ${ESTATE}/ranch/`],
    ["Port vars", `grep -i '${CANDIDATE}_PORT' ${ESTATE}/config/ports.env`],
    ["Mise tasks", `grep -i '^\\[tasks\\.' ${ESTATE}/mise.toml | sed 's/\\[tasks\\.\(.*\)\\]/\\1/'`],
    ["Service scripts", `ls ${ESTATE}/stack/services/ 2>/dev/null`],
    ["Config files", `ls ${ESTATE}/config/ 2>/dev/null`],
    ["Binaries", `ls /home/toxic/.local/bin/ 2>/dev/null`],
    ["Vendored repos", `ls ${ESTATE}/ranch/vendored/ 2>/dev/null`],
  ];

  const allConflicts = new Set<string>();

  for (const [label, cmd] of checks) {
    const matches = await checkSource(CANDIDATE, cmd);
    const filtered = matches.filter(m => m.toLowerCase().includes(CANDIDATE.toLowerCase()));
    if (filtered.length > 0) {
      console.log(`${label}:`);
      for (const m of filtered) {
        console.log(`  - ${m}`);
        allConflicts.add(`${label}: ${m}`);
      }
    } else {
      console.log(`${label}: (free)`);
    }
  }

  console.log("\n=== Summary ===");
  if (allConflicts.size === 0) {
    console.log(`✅ '${CANDIDATE}' appears FREE across all checked sources`);
    process.exit(0);
  } else {
    console.log(`❌ CONFLICTS found:`);
    for (const c of allConflicts) console.log(`   - ${c}`);
    process.exit(1);
  }
}

main();
