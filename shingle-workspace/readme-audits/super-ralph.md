# README audit — toxicwind/super-ralph @ 568753e6 — 2026-09-14

**Verdict:** NEEDS UPDATE

Audited the GitHub state (tarball of `main` @ `568753e6`, 2026-02-27). Note: the
fork's **+3 local NIM-proxy commits live only on awrawr-pc** (`/home/toxic/super-ralph`)
and are NOT on GitHub — this audit covers the pushed tree only. This is a fork;
GitHub lists parent as `roninjin10/super-ralph` (package.json still points at
`evmts/super-ralph` — stale, not a README issue). **Read-only audit; nothing
edited, committed, or pushed.**

Mechanical (`audit.py`): 6/7 PASS. Sole FAIL is a false positive:
`.super-ralph/generated/workflow.tsx` is generated at runtime
(`src/cli/index.ts:637`) and `.super-ralph/` is gitignored — expected absent.

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Tagline: ticket-driven Ralph workflow, multi-agent review loops | `src/components/{TicketScheduler,AgenticMergeQueue}.tsx`; `mergeQueue/coordinator.ts`; `package.json:4` description matches | VERIFIED |
| Install: `bun add super-ralph smithers-orchestrator` | `package.json`: name `super-ralph`, `smithers-orchestrator` is a peerDep | VERIFIED |
| CLI wraps workflow from prompt string or file | `src/cli/index.ts` (758 lines, full CLI) | VERIFIED |
| Preflight checks for `jj`, prints install instructions | `src/cli/index.ts:258-262` | VERIFIED |
| Auto-detects `claude` and `codex` CLIs on startup | `src/cli/index.ts:147-154,695` | VERIFIED |
| Planning pass interprets prompt into `SuperRalph` props | `InterpretConfig` wired into generated workflow, `src/cli/index.ts:367` | VERIFIED |
| Generates runnable workflow at `.super-ralph/generated/workflow.tsx` | `src/cli/index.ts:620-638` | VERIFIED |
| Runs Smithers with built-in OpenTUI monitor | `src/components/Monitor.tsx:55` imports `@opentui/core` | VERIFIED |
| "Emits throttled status reports every 5 minutes" | No report-interval mechanism anywhere in `src/` | WRONG |
| `--report-interval-minutes` CLI flag | Only `--max-concurrency` and `--dry-run` exist (`src/cli/index.ts:39-41`); no `reportInterval` in `src/` | WRONG |
| "Detects error patterns and suggests likely fixes" | Nothing in `src/` | WRONG |
| "Prepares issue drafts and prints `gh issue create` commands" | `gh` only detected (`src/cli/index.ts:147-154`), never used; no `issue create` in `src/` | WRONG |
| Exports `SuperRalph`, `ralphOutputSchemas` | `src/index.ts:35,77,102,128` | VERIFIED |
| Usage agents (`ClaudeCodeAgent`, `CodexAgent`, `GeminiAgent`, `KimiAgent` from `smithers-orchestrator`) | External package; `KimiAgent`/`GeminiAgent` never referenced in `src/` (generated workflow uses only Claude/Codex, `src/cli/index.ts:310-341`) | UNVERIFIED |
| `UpdateProgress → PROGRESS.md` | `src/components/SuperRalph.tsx:99` (`progressFile = "PROGRESS.md"`) | VERIFIED |
| Speculative merge queue: `ticket/<id>` bookmarks, rebase stack, parallel post-land CI, fast-forward main | `src/mergeQueue/coordinator.ts:106,244,261,276,485,607` | VERIFIED |
| Dedicated merge-queue agent, `mergeQueueOrdering="report-complete-fifo"` | Strategy exists and is the default (`coordinator.ts:9,333`); prop at `SuperRalph.tsx:48` | VERIFIED |
| `maxSpeculativeDepth`, `postLandChecks` (falls back to `testCmds`) | `SuperRalph.tsx:47-49,106,122` | VERIFIED |
| jj-native workflow (`jj describe`/`jj new`, bookmark + `jj git push --bookmark`, `jj rebase`) | `src/prompts/Test.mdx:18-20`, `ReviewFix.mdx:42-44`, `UpdateProgress.mdx:27-30` | VERIFIED |
| "Supports subscriptions." | No `subscription` match anywhere in `src/` | UNVERIFIED |
| License MIT | `LICENSE` present; `package.json` license MIT | VERIFIED |

## Missing from README

- **Flat job-system refactor (Feb 24–27, commits `eef04ed3`, `4614adc7`, `a79b1da0`, `76584240`, `b5040451`, `5917c55d`):** scheduling moved from ticket assignments to a unified AI-driven job system (`Job.tsx`, `bun:sqlite` tracking, separate scheduler/execution/merge-queue loops, scheduler controlling ALL side tasks). The Pattern section still describes the pre-refactor ticket-phase model; tickets remain the work unit but jobs are now the scheduling unit.
- **New `Monitor` component** (`568753e6`, latest commit) — README mentions the OpenTUI monitor only in passing under CLI.
- **`docs/ARCHITECTURE.md`, `docs/CLI_CLARIFICATIONS.md`** exist but are not linked from the README.
- No mention that this is a fork, and `package.json` repository/bugs/homepage still point to `evmts/super-ralph` while GitHub's recorded parent is `roninjin10/super-ralph` (stale metadata, not README text).

## Quickstart check

- [x] Commands exist (`bun add …`, `super-ralph` bin → `src/cli/index.ts`)
- [x] Config keys match code (`maxConcurrency`, `postLandChecks`, `mergeQueueOrdering`, `maxSpeculativeDepth` all real props)
- [ ] A fresh user could follow it end to end — **no**: `--report-interval-minutes` is not a real flag, and the promised 5-minute reports, error-pattern suggestions, and `gh issue create` drafts do not exist in the code.

## Action taken

- None — read-only audit per task rules (fork; never push to its origin). Recommended fixes: delete the four WRONG CLI claims (or implement them), add a paragraph on the job-based scheduler refactor, link `docs/`, and fix `package.json` repo URLs.
