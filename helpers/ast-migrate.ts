#!/usr/bin/env bun
/**
 * Sovereign Universal AST Migration Helper (September 2026)
 * Leverages ast-grep for structural, language-agnostic code transformation.
 * Translates and modernizes legacy syntax across Python, TypeScript, and Rust.
 */

import { $ } from "bun";

interface MigrationRule {
  id: string;
  language: "python" | "typescript" | "rust";
  pattern: string;
  rewrite: string;
  description: string;
}

const COMMON_RULES: MigrationRule[] = [
  // Python -> TS / Modernization Rules
  {
    id: "py-print-to-console",
    language: "python",
    pattern: "print($ARG)",
    rewrite: "console.log($ARG)",
    description: "Converts print statements to console.log",
  },
  {
    id: "py-dict-get-to-optional",
    language: "python",
    pattern: "$OBJ.get($KEY, $DEFAULT)",
    rewrite: "$OBJ?.[$KEY] ?? $DEFAULT",
    description: "Converts Python dict.get to optional chaining with nullish coalescing",
  },
  // TS Modernization (September 2026 standard)
  {
    id: "ts-prefer-nullish-coalescing",
    language: "typescript",
    pattern: "$A || $B",
    rewrite: "$A ?? $B",
    description: "Migrates logical OR fallbacks to nullish coalescing",
  },
  {
    id: "ts-fs-promises-to-bun-file",
    language: "typescript",
    pattern: "await fs.promises.readFile($PATH, $ENC)",
    rewrite: "await Bun.file($PATH).text()",
    description: "Modernizes Node fs.promises to native Bun.file API",
  },
];

async function main() {
  const targetDir = process.argv[2] || ".";
  const action = process.argv[3] || "scan";

  console.log(`[ast-migrate] Target Directory: ${targetDir}`);
  console.log(`[ast-migrate] Mode: ${action} (${COMMON_RULES.length} built-in structural rules)\n`);

  for (const rule of COMMON_RULES) {
    try {
      console.log(`--- Checking rule: ${rule.id} [${rule.language}] ---`);
      console.log(`    ${rule.description}`);
      if (action === "rewrite") {
        await $`ast-grep scan -p ${rule.pattern} --rewrite ${rule.rewrite} -l ${rule.language} ${targetDir}`.nothrow();
      } else {
        await $`ast-grep scan -p ${rule.pattern} -l ${rule.language} ${targetDir}`.nothrow();
      }
    } catch {
      // ast-grep exits non-zero if matches are found or none found depending on flags
    }
  }

  console.log("\n[ast-migrate] Scan complete. Run with 'rewrite' argument to apply transformations.");
}

await main();
