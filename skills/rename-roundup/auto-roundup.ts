#!/usr/bin/env bun
/**
 * auto-roundup — Automatic, collision-aware repo & fork renamer.
 *
 * Inspects all existing file and folder names across the repository,
 * detects conflicts automatically, suggests/resolves collision-free
 * thematic names, and invokes rename-roundup safely.
 */

import { existsSync, readdirSync, statSync } from "node:fs";
import { resolve, join } from "node:path";
import { parseArgs } from "node:util";

const RANCH_THEME_CANDIDATES = [
  "remuda",     // herd of working saddle horses on a ranch
  "wrangler",   // hand who manages and trains horses
  "paddock",    // small enclosure/pen for working animals
  "pasture",    // grazing field
  "outpost",    // edge station
  "range",      // open expanse
  "corral_fleet",
  "stockade",
  "cavy",       // alternative term for saddle horse remuda
];

export function getExistingNames(repoRoot: string): Set<string> {
  const names = new Set<string>();
  try {
    const entries = readdirSync(repoRoot);
    for (const e of entries) {
      names.add(e.toLowerCase());
    }
  } catch (err) {
    console.error(`Failed to scan root: ${err}`);
  }
  return names;
}

export function pickSafeThematicName(repoRoot: string, candidates = RANCH_THEME_CANDIDATES): string {
  const existing = getExistingNames(repoRoot);
  for (const cand of candidates) {
    if (!existing.has(cand.toLowerCase())) {
      return cand;
    }
  }
  // Fallback with monotonic suffix if all are taken
  let counter = 1;
  while (existing.has(`remuda-${counter}`)) {
    counter++;
  }
  return `remuda-${counter}`;
}

async function main() {
  const { values } = parseArgs({
    args: process.argv.slice(2),
    options: {
      repo: { type: "string" },
      old: { type: "string" },
      new: { type: "string" },
      theme: { type: "string", default: "ranch" },
      commit: { type: "string" },
      "dry-run": { type: "boolean", default: false },
      help: { type: "boolean", short: "h" },
    },
    strict: false,
  });

  if (values.help || !values.old) {
    console.log(`
auto-roundup — Automatic collision-aware fork & project renamer

Usage:
  bun run auto-roundup.ts --repo <path> --old <target> [--new <target>] [--dry-run] [--commit "<msg>"]

Features:
  - Scans workspace namespace to avoid naming collisions automatically
  - Synthesizes ranch-themed alternative names if destination exists
  - Executes Bun-native rename-roundup atomically
`);
    return 0;
  }

  const repo = resolve((values.repo as string) ?? process.cwd());
  const oldName = values.old as string;
  let targetNew = values.new as string | undefined;

  const existing = getExistingNames(repo);
  console.log(`[auto-roundup] Scanned repo: ${repo}`);
  console.log(`[auto-roundup] Discovered ${existing.size} existing root entries.`);

  if (!targetNew || existing.has(targetNew.toLowerCase())) {
    if (targetNew) {
      console.warn(`[auto-roundup] Warning: Requested name "${targetNew}" already exists in namespace!`);
    }
    targetNew = pickSafeThematicName(repo);
    console.log(`[auto-roundup] Automatically picked collision-free theme name: "${targetNew}"`);
  }

  console.log(`[auto-roundup] Renaming: "${oldName}" => "${targetNew}"`);

  // Build command for rename.ts
  const renameScript = join(import.meta.dir, "rename.ts");
  const args = [
    "run",
    renameScript,
    "--repo", repo,
    "--old", oldName,
    "--new", targetNew,
  ];

  if (values["dry-run"]) {
    args.push("--dry-run");
  } else if (values.commit) {
    args.push("--commit", values.commit as string);
  } else {
    args.push("--commit", `rename: ${oldName} -> ${targetNew} (thematic auto-roundup)`);
  }

  console.log(`[auto-roundup] Invoking: bun ${args.join(" ")}`);
  const proc = Bun.spawn(["bun", ...args], {
    cwd: repo,
    stdout: "inherit",
    stderr: "inherit",
  });

  const exitCode = await proc.exited;
  process.exit(exitCode);
}

if (import.meta.main) {
  main().catch((err) => {
    console.error("Fatal:", err);
    process.exit(1);
  });
}
