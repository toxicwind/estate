# Mise + Pitchfork as Code Convention — Estate-Wide Audit & Fix Plan

> **Date**: 2026-10-30 · **Auditor**: tau (via trio persistent bun kernel) · **Status**: findings + plan, implementation gated
> **Scope**: every mise.toml / pitchfork.toml / pitchfork.d under pens/, plus the mise conf.d/tasks layer and canary/nightly lanes.

## TL;DR
mise and pitchfork began as **execution tooling** but have become a **de-facto configuration/code convention**:
291 daemon definitions across 33 config files, 18 mise.tomls, a 5-file mise conf.d layer + 23 file-tasks, and
canary/nightly lanes carrying their own PLAN gates. This sprawl is the root of the "super confusing" estate:
the same service can be defined in the monolith, a fragment, a pen pitchfork.toml, and a mise task — four
places to edit, four drift surfaces (anomaly #6 "two truths are a bug" generalized).

## Method
Analyzed with **trio** (`pens/geode/products/trio`, the persistent bun notebook kernel) as the audit kernel —
dynamic-import support was added to trio in this session (TDD 15/15) specifically so real-repo analysis cells
could run: `await import("node:child_process")` + `node:fs` inside the persistent vm.

## Findings (measured)

### 1. Pitchfork config sprawl — 291 daemon defs, 33 config files
| pen | config files (pitchfork.toml + pitchfork.d) | daemon defs |
|---|---|---|
| estate | 4 | **221** |
| geode | 2 | 11 |
| barn | 4 | 6 |
| **ranch** | **19** | 49 |
| olympus | 2 | 4 |
| fleet | 1 | 0 |
| mesh | 1 | 0 |
| **total** | **33** | **291** |

- **ranch is the epicenter**: 19 pitchfork config files (fragments across ~19 sub-products), 49 defs.
- **estate monolith dominates**: 221 defs — the single-file supervisor truth (anomaly #6 says edit ONLY the monolith, yet fragments still exist and were edited this session to fix paper-poller — direct convention conflict).

### 2. Mise as convention — 18 mise.toml + conf.d layer + 23 tasks
- 18 mise.toml files at maxdepth 3 under pens/ (per-pen toolchain pinning).
- `estate/mise/conf.d`: 00-toolchain (7 lines, `[tools]`), 10-env (1, `[env]`), 15-remote-cache (7, `[settings]`),
  20-stack (16, `[tasks."up:all"]`), 30-dev (42, `[tasks.zed]`) — a hand-rolled config layer with task definitions
  *inside TOML files*, duplicating what scripts/run files already express.
- `estate/mise/tasks`: 23 file-tasks (doctor, down, estate-gate, ffs, health, models, status, svc-check, …)
  — bash scripts re-expressing estate operations that already exist as pitchfork daemons / ops scripts.
- `tasks.zip.txt`: a **zip archive committed as text** in the repo (binary zip blob) — a packaging antipattern
  for a convention layer that claims to be code.
- Live daemon evidence: pitchfork supervisor (systemd, cwd /home/toxic) + `mise = true` per-daemon wrapping.

### 3. Pitchfork supervisor + state shadowing
- unit: `ExecStart=.../pitchfork supervisor run --boot`, NO WorkingDirectory, TasksMax=200000.
- supervisor cwd = /home/toxic → pitchfork discovers config via namespaces in `~/.config/pitchfork/config.toml`
  (now pens/*), but the paper-poller daemon ran from **ghost path /home/toxic/paper-poller** (state.toml shadow)
  → fixed this session: canonical pens copy, state purge, fragments repointed. Same class as anomalies #48/#20.

### 4. Canary/nightly lanes carry manual gates
- `ranch/products/nightly-canary`: PLAN.md + canary-runner.sh + nightly-canary.cron — **DESIGNED, NOT ENABLED**,
  checkpoint = Raccoon reviews before cron install.
- `olympus/products/typescript-go/_extension-nightly`: upstream TS7 nightly extension vendor (not a convention lane).
- The canary lane is a *process* convention (verify-proceed) unexpressed in any machine-readable gate.

## Confusion catalogue (the "super confusing")
1. One service, four definition places: monolith + fragment + pen pitchfork.toml + mise task → drift (proven by paper-poller ghost this session).
2. `mise = true` per-daemon (anomaly #43: pre-spawn kill) vs pen mise.toml toolchains — three layers of toolchain truth.
3. tasks.zip.txt binary-in-repo + 23 file-tasks duplicating ops scripts.
4. state.toml shadowing live config (paper-poller: 2 stale blocks survived config edits until purged).
5. AGENTS.md says "edit ONLY the monolith; retire fragment generation" but 33 fragment files remain and CLI + supervisor both read them.

## Fix plan (estate-wide, phased, forward-only)

### Phase 1 — Truth collapse (this arc, done)
- [x] paper-poller: canonical = `pens/ranch/products/paper-poller`; 5-leg racer cherry-picked from wip (commit 6f19bac); wip/legacy copies archived; ghost `/home/toxic/paper-poller` purged from state.toml; fragments repointed; daemon restarts clean.
- [x] trio: dynamic-import + process TDD (15/15) so it can audit real repos (aee54f2).

### Phase 2 — Conventionalize (next)
- [ ] Pick ONE definition surface per service: **`pens/<pen>/pitchfork.d/<name>.toml`** (fragment) as the CANONICAL; monolith keeps only mesh-critical defs (thresher, squawk, mesh-hub). Migrate estate monolith's 221 defs → fragments by pen product. AGENTS.md updated to "edit the fragment", not "monolith only".
- [ ] Retire estate/mise/conf.d + tasks as a convention: move file-tasks → `pens/<pen>/bin/` scripts with mise only for toolchain pinning (mise.toml `[tools]`, never `[tasks]`).
- [ ] Delete tasks.zip.txt; git-ignore `*.zip` under mise/.
- [ ] Drop `mise = true` from fragments; use absolute binaries (anomaly #43 pattern) unless a pen toolchain genuinely varies.
- [ ] `pitchfork daemons` / `config` CLI reads = same merge the supervisor uses (today CLI volume vs supervisor path disagree — verify AFTER fragment migration).

### Phase 3 — Canary/nightly as machine gates
- [ ] nightly-canary: convert Raccoon checkpoint into a repo-visible GATE file (docs/AGENTS.md + CI-able script) — canary-runner.sh already verify-proceed; add `nightly-canary/ENABLED` marker so "not installed" is explicit state, not a comment.
- [ ] Wire nightly canary to run trio analysis cells as its verification kernel (dogfood).

### Phase 4 — Watchdogging
- [ ] Add a trio cell + estate health lane: assert every pitchfork def's run/dir target EXISTS (catches ghost-path class before it bites). Fold into estate_health_audit or a new lane.
- [ ] lint: fragment names match product dirs; no `mise = true`; no tasks.zip.

## Ownership
- **Loom** (visor/tauvisor) audits agent-tree writes; this plan's config-consistency cell is the daemon-side equivalent.
- **Stencil** (ex-forge) owns pattern/paper borrow; paper-poller canonical lives under ranch/products (poller) with racer shared.

## Papers grounding the runtime-enforcement thesis (from live race)
- "Agent Safety Should Be a Runtime Contract" (arXiv 2608.11274)
- "Beyond Guardrails: Runtime Enforcement for Secure AI Agents — Systematic Review" (JRSC 2026)
- "AgentWall: A Runtime Safety Layer for Local AI Agents" (arXiv 2605.16265)
- "StepGuard / DreamGuard / Provably Secure Agent Guardrail" (2026)
→ The estate's real fix parallels the literature: enforcement at the runtime (pitchfork/mise as config, validated),
   not more prompt-level instruction.