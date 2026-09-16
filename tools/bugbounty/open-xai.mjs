#!/usr/bin/env node
/**
 * Headed Firefox/Chromium: open X / xAI HackerOne bounty program ($$).
 * Usage: node open-xai.mjs
 * Env: BB_CDP_URL=http://127.0.0.1:9222  BB_CLOSE=1  DISPLAY=:0
 */
import { runProgram } from "./lib/helpers.mjs";

console.log("=== Bug bounty opener: X / xAI (HackerOne) ===");
console.log("Program: https://hackerone.com/x  (rewards discretionary $$)");
console.log("Attach evidence: ~/projects/agent-path-wrapper-bug/");
await runProgram("xai");
