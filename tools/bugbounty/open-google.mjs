#!/usr/bin/env node
/**
 * Headed: Google Bug Hunters VRP (primary $$ program).
 * Usage: node open-google.mjs
 */
import { runProgram } from "./lib/helpers.mjs";

console.log("=== Bug bounty opener: Google Bug Hunters / VRP ===");
console.log("https://bughunters.google.com/  report: /report");
console.log("Attach evidence: ~/projects/agent-path-wrapper-bug/");
await runProgram("google");
