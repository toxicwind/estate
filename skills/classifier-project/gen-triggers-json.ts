#!/usr/bin/env bun
/**
 * tools/gen-triggers-json.ts — regenerate triggers.json from db-src/triggers.ts.
 *
 * db-src/triggers.ts is the single source of truth (merged 18-shape DB from
 * the classifier-project skill). triggers.json is the runtime artifact
 * consumed by preflight.ts / preflight.test.ts.
 *
 * Run: bun tools/gen-triggers-json.ts
 */
import { TRIGGER_SHAPES } from "../db-src/triggers.ts";
import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

interface JSPattern {
  source: string;
  flags: string;
}

function toJSPatterns(id: string, pattern: string): JSPattern[] {
  if (id === "c2-term") {
    // PCRE scoped inline flags (?i:...)/(?-i:...) are not valid JS RegExp:
    // split into per-alternative patterns with explicit flags.
    // \bC2\b stays case-sensitive by design: lowercase c1/c2 are
    // chunk-variable names in code, not the term.
    return [
      { source: "command[- ]and[- ]control", flags: "gi" },
      { source: "\\bC2\\b", flags: "g" },
    ];
  }
  new RegExp(pattern, "gi"); // fail fast on any other JS-incompatible pattern
  return [{ source: pattern, flags: "gi" }];
}

const shapes = TRIGGER_SHAPES.map((t) => ({
  id: t.id,
  patterns: toJSPatterns(t.id, t.pattern),
  why: t.why,
  rewrite: t.rewrite,
}));

writeFileSync(
  join(ROOT, "triggers.json"),
  JSON.stringify(
    { version: 1, generated_from: "db-src/triggers.ts", shapes },
    null,
    2,
  ) + "\n",
);
console.log(`triggers.json: ${shapes.length} shapes`);
