#!/usr/bin/env bun
/**
 * pattern-borrow.ts — thin delegate to the canonical pattern-forge borrower.
 *
 * The 10-factor GitHub-wide ranker + multi-source borrower (arxiv/hf/openalex/
 * s2/dblp/github/local) lives ONCE in flux's code-patterns product (pattern-forge)
 * (`/home/toxic/pens/flux/products/code-patterns/`). This file is the estate
 * PATH contract (AGENTS.md: pattern-borrow is a first-class verification
 * subtask) and forwards everything to the canonical CLI unchanged.
 *
 * CLI:
 *   bun run scripts/pattern-borrow.ts [args...]   → canonical
 *
 * Env:
 *   PATTERN_BORROW_BIN — override the canonical CLI path.
 */
import { spawnSync } from "node:child_process";

const CANONICAL =
  process.env.PATTERN_BORROW_BIN ??
  "/home/toxic/pens/flux/products/code-patterns/bin/pattern-borrow.ts";

const res = spawnSync("bun", [CANONICAL, ...Bun.argv.slice(2)], {
  stdio: "inherit",
  env: process.env,
});
process.exit(res.status ?? 0);