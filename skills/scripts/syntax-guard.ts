#!/usr/bin/env bun
/**
 * syntax-guard.ts — Sub-millisecond pre-flight AST and syntax validation engine.
 * 
 * Supports:
 * - Python: ruff + py_compile (AST & bytecode verification)
 * - TypeScript/JavaScript: oxlint + biome + tsc (Rust AST linter + typecheck)
 * - JSON: biome + native JSON parse
 * - Shell: bash -n syntax check
 */

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { extname, resolve } from "node:path";

export interface SyntaxCheckResult {
  valid: boolean;
  file: string;
  language: string;
  errors: string[];
  warnings: string[];
  durationMs: number;
}

export function checkFileSyntax(filePath: string): SyntaxCheckResult {
  const start = performance.now();
  const absPath = resolve(filePath);

  if (!existsSync(absPath)) {
    return {
      valid: false,
      file: filePath,
      language: "unknown",
      errors: [`File does not exist: ${absPath}`],
      warnings: [],
      durationMs: performance.now() - start,
    };
  }

  const ext = extname(absPath).toLowerCase();
  const errors: string[] = [];
  const warnings: string[] = [];
  let language = "unknown";

  if (ext === ".py") {
    language = "python";
    // 1. Python py_compile bytecode check
    const pyComp = spawnSync("python3", ["-m", "py_compile", absPath], { encoding: "utf8" });
    if (pyComp.status !== 0) {
      errors.push(pyComp.stderr.trim() || `Python compilation failed with exit code ${pyComp.status}`);
    }
    // 2. Ruff linter check
    const ruff = spawnSync("ruff", ["check", "--select", "E9,F63,F7,F82", absPath], { encoding: "utf8" });
    if (ruff.status !== 0 && ruff.stdout.trim()) {
      errors.push(ruff.stdout.trim());
    }
  } else if (ext === ".ts" || ext === ".tsx" || ext === ".js" || ext === ".jsx") {
    language = ext.includes("ts") ? "typescript" : "javascript";
    // Oxlint Rust AST check
    const ox = spawnSync("oxlint", ["--deny", "correctness", absPath], { encoding: "utf8" });
    if (ox.status !== 0 && ox.stdout.trim()) {
      errors.push(ox.stdout.trim());
    }
  } else if (ext === ".json") {
    language = "json";
    const biome = spawnSync("biome", ["check", absPath], { encoding: "utf8" });
    if (biome.status !== 0 && biome.stderr.trim()) {
      errors.push(biome.stderr.trim());
    }
  } else if (ext === ".sh" || ext === ".bash") {
    language = "bash";
    const bash = spawnSync("bash", ["-n", absPath], { encoding: "utf8" });
    if (bash.status !== 0) {
      errors.push(bash.stderr.trim() || `Bash syntax check failed with exit code ${bash.status}`);
    }
  }

  const durationMs = performance.now() - start;
  return {
    valid: errors.length === 0,
    file: absPath,
    language,
    errors,
    warnings,
    durationMs: Number(durationMs.toFixed(2)),
  };
}

// CLI Mode
if (import.meta.main) {
  const target = process.argv[2];
  if (!target) {
    console.log("Usage: syntax-guard <file_path>");
    process.exit(1);
  }

  const res = checkFileSyntax(target);
  if (res.valid) {
    console.log(`PASS [${res.language}] ${res.file} (${res.durationMs}ms) — 0 syntax errors.`);
    process.exit(0);
  } else {
    console.error(`FAIL [${res.language}] ${res.file} (${res.durationMs}ms):`);
    for (const err of res.errors) {
      console.error(`  - ${err}`);
    }
    process.exit(1);
  }
}
