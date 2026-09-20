# README audit — toxicwind/tau-extensions @ e488bdf — 2026-09-14

**Verdict:** NEEDS UPDATE

Audited SHA `e488bdfd2e844ddab7a723fadeda7db02f77a827` (main HEAD, CI-green per fleet record). README is 2424 chars / 81 lines.

## Mechanical results (`bin/audit.py`)

- readme-exists: PASS (2424 chars, 81 lines)
- mentioned-paths-exist: PASS (0 paths mentioned — README links only `packages/omp-kafka`, `packages/omp-edit-committer`, `./LICENSE`, all resolve)
- relative-links-resolve: PASS
- versions-match-manifests: WARN — `17.0.0` ("Requires omp >= 17.0.0") not found in any manifest; it's a host-CLI requirement, external to the repo
- badge-workflows-exist: PASS (no badges in README)
- quickstart-entrypoints-exist: PASS (no missing commands detected)
- external-links-alive: PASS

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| "monorepo of Tau extensions" (header) | marketplace.json: name `tau-extensions`, metadata "Tau extensions by toxicwind" | VERIFIED |
| "Three extensions ship out of the box" (intro) | `packages/` has 10 dirs; README documents 2; marketplace.json lists 10 plugins | WRONG |
| omp-kafka: auto (push)/pull modes, `/kafka-*` slash commands, `kafka_consume` LLM tool | packages/omp-kafka/src/extension.ts:11,190; commands kafka-drop/pause/reload/resume/status/tail | VERIFIED |
| omp-edit-committer: auto-commit Edit/Write, ASCII diagram, commit badge for modem-dev/hunk | packages/omp-edit-committer/src/message.ts, src/renderer.ts:5-6 ("badge… under the Edit tool result"), hunk refs in message.ts | VERIFIED |
| "Requires omp >= 17.0.0" (Install) | No manifest pins it; host CLI is external; root devDep is @oh-my-pi/pi-coding-agent ^18.0.11 | UNVERIFIED |
| Option A: sparse clone + `git sparse-checkout set packages/omp-kafka` + `bun install` + `omp plugin link .` | paths exist; `omp plugin link .` echoed at packages/omp-kafka/README.md:32 | VERIFIED (paths) / UNVERIFIED (omp CLI is external) |
| Option B: `bun add -g @toxicwind/omp-kafka` / `@toxicwind/omp-edit-committer` | packages/omp-kafka/package.json, packages/omp-edit-committer/package.json `name` fields match exactly | VERIFIED |
| Option C: `omp --extension /path/to/...` | No in-tree evidence; omp CLI is external | UNVERIFIED |
| `~/.tau/agent/config.yml` extensions list | No in-tree evidence for this config format | UNVERIFIED |
| Dev: `bun run --workspaces test` / `bun run --workspaces typecheck` | Root package.json scripts: `test` = `bun test packages/*`, `typecheck` = `bun scripts/typecheck.mjs`; bun has no `--workspaces` flag | WRONG |
| "All packages typecheck and test cleanly" | .github/workflows/ci.yml runs typecheck + tests; audited SHA is the CI-green commit | VERIFIED (via CI at audited SHA; not re-run locally) |
| "`node_modules/` stays minimal — only declared dependencies, no transitive junk" | Cannot be derived from the tree; bun.lock exists | UNVERIFIED |
| "License: MIT" | Root LICENSE + all 10 packages MIT (incl. packages/engram/LICENSE, MIT © Kirill Turanskiy) | VERIFIED |

## Missing from README

Dominant recent work (commits 85bc0a6..e488bdf) with zero README coverage:

- **8 vendored forks now in `packages/`**: engram (thebtf/engram 6.48.0, locally adapted), gsd-omp (Baylar55/gsd-omp 1.0.24), omp-best-of (wolfiesch/omp-best-of 0.2.0), omp-model-router (moved into packages/, 150+ strict typecheck fixes), omp-undo-redo (Baylar55/omp-undo-redo 1.6.2), pi-agent-browser-native (fitchmultz/pi-agent-browser-native 0.6.12), pi-tasks (tintinweb/pi-tasks 0.9.0), pi-workflow (AgwaB/pi-workflow 0.13.8). README documents 2 of 10 packages.
- **Fork model**: AGENTS.md:3 "our extensions plus forks of others"; AGENTS.md:32 + NOTICE file carry fork provenance/attribution. README frames the repo as a curated 2-extension set.
- **bun 1.3.x requirement**: .github/workflows/ci.yml:17 pins `bun-version: 1.3.x`; lockfiles must be generated with bun 1.3.x to match CI (`--frozen-lockfile`). Not mentioned.
- **marketplace.json tau rebrand**: name `tau-extensions`, owner toxicwind, 10 plugins, `pluginRoot: packages` — README never mentions the marketplace manifest.
- **Discrepancy**: fleet notes mention "kimi implemented as packages/omp-kimi" — no `omp-kimi` in tree, marketplace.json, or any commit at e488bdf. Either planned/not landed or on another branch.

## Quickstart check

- [x] Commands exist (git sparse-checkout paths valid; per-package READMEs echo the omp commands)
- [ ] Ports/config keys match code — n/a (no ports), but `~/.tau/agent/config.yml` format is unverified
- [ ] A fresh user could follow it end to end — dev section commands are wrong (`--workspaces` flag doesn't exist in bun); correct: `bun run test`, `bun run typecheck`; missing bun 1.3.x prerequisite

## Action taken

- None — REPORT ONLY per task. Suggested fixes: correct "Three extensions" count, add the 8 vendored forks to the Extensions table with upstream provenance, fix dev commands to `bun run test` / `bun run typecheck`, document the bun 1.3.x lockfile requirement, mention marketplace.json/NOTICE.
