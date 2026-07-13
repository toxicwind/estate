#!/usr/bin/env node
/**
 * Headed: GitHub Security Bug Bounty (HackerOne + bounty.github.com).
 * Criticals advertised $30,000+.
 * Usage: node open-github.mjs
 */
import { runProgram } from "./lib/helpers.mjs";

console.log("=== Bug bounty opener: GitHub Security ===");
console.log("https://hackerone.com/github  |  https://bounty.github.com/");
console.log("Attach evidence: ~/projects/agent-path-wrapper-bug/");
await runProgram("github");
