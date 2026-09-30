#!/usr/bin/env bun
/**
 * Safe RG Audit Scaffold (`safe-rg-audit.ts`)
 *
 * Prevents catastrophic self-referential log loops and runaway disk bloat
 * by enforcing:
 * 1. Hard exclusions for session transcripts (*.log, *.jsonl, .git, cache, node_modules)
 * 2. Strict execution timeout (default 5s)
 * 3. Max result limit cap (default 100 lines)
 * 4. Max file size cutoff (--max-filesize 2M)
 */

import { spawnSync } from "node:child_process";

export interface SafeSearchOptions {
  pattern: string;
  paths?: string[];
  maxLines?: number;
  timeoutMs?: number;
}

export function safeSearch(options: SafeSearchOptions): {
  stdout: string;
  stderr: string;
  exitCode: number;
} {
  const {
    pattern,
    paths = [
      "/home/toxic/.tau",
      "/home/toxic/.config",
      "/home/toxic/sovereign",
    ],
    maxLines = 100,
    timeoutMs = 5000,
  } = options;

  const defaultExcludes = [
    "!**/*.log",
    "!**/*.jsonl",
    "!**/*.tombstone",
    "!**/sessions/**",
    "!**/logs/**",
    "!**/.git/**",
    "!**/node_modules/**",
    "!**/target/**",
    "!**/dist/**",
    "!**/cache/**",
  ];

  const args: string[] = [
    "--max-filesize",
    "2M",
    "--max-columns",
    "500",
    "--color",
    "never",
    "-n",
  ];

  for (const glob of defaultExcludes) {
    args.push("-g", glob);
  }

  args.push("-e", pattern, "--", ...paths);

  const proc = spawnSync("rg", args, {
    encoding: "utf-8",
    timeout: timeoutMs,
    maxBuffer: 10 * 1024 * 1024,
  });

  const lines = (proc.stdout || "").split("\n");
  const boundedStdout = lines.slice(0, maxLines).join("\n");

  return {
    stdout: boundedStdout,
    stderr: proc.stderr || "",
    exitCode: proc.status ?? 1,
  };
}

// CLI Mode
if (import.meta.main) {
  const pattern = process.argv[2] || "api\\.nvidia\\.com";
  const customPaths = process.argv.slice(3);

  console.log(`[safe-rg-audit] Scanning for pattern: "${pattern}"...`);
  const result = safeSearch({
    pattern,
    paths: customPaths.length > 0 ? customPaths : undefined,
  });

  if (result.stdout.trim().length > 0) {
    console.log(result.stdout);
    console.log(`\n✅ Scan completed safely.`);
  } else {
    console.log(`(no matches found outside excluded session logs)`);
  }

  if (result.stderr.trim().length > 0) {
    console.error(`[stderr]:\n${result.stderr}`);
  }
}
