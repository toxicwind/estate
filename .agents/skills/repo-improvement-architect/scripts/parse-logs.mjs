#!/usr/bin/env node
// Extract likely root-cause lines from a build/test log.
// Usage:
//   node parse-logs.mjs <logfile>
//   cat build.log | node parse-logs.mjs
// Prints the FIRST cluster of error lines (root cause is usually first, not last),
// with a little surrounding context. Read-only.
import { readFileSync } from "node:fs";

const ERROR_PATTERNS = [
  /\berror\b/i,
  /\bfailed\b/i,
  /\bexception\b/i,
  /\btraceback\b/i,
  /\bcannot find\b/i,
  /\bunexpected\b/i,
  /\bTS\d{3,5}\b/, // TypeScript error codes
  /\bENOENT\b|\bEACCES\b|\bEADDRINUSE\b/,
  /AssertionError|ReferenceError|TypeError|SyntaxError/
];

function readInput() {
  const file = process.argv[2];
  if (file) return readFileSync(file, "utf8");
  return readFileSync(0, "utf8"); // stdin
}

let text;
try {
  text = readInput();
} catch (err) {
  console.error(`Could not read log input: ${err.message}`);
  process.exit(2);
}

const lines = text.split(/\r?\n/);
const hits = [];
for (let i = 0; i < lines.length; i++) {
  if (ERROR_PATTERNS.some((p) => p.test(lines[i]))) hits.push(i);
}

if (hits.length === 0) {
  console.log("No error-like lines found. Showing the last 10 lines:\n");
  console.log(lines.slice(-10).join("\n"));
  process.exit(0);
}

// Focus on the FIRST error and a small window after it.
const first = hits[0];
const start = Math.max(0, first - 2);
const end = Math.min(lines.length, first + 12);

console.log(`First error at line ${first + 1} of ${lines.length}. Context:\n`);
for (let i = start; i < end; i++) {
  const marker = hits.includes(i) ? ">>" : "  ";
  console.log(`${marker} ${String(i + 1).padStart(5)}  ${lines[i]}`);
}
console.log(`\n${hits.length} error-like line(s) total.`);
