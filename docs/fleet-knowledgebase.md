# Fleet Knowledgebase

**REQUIRED READING for every agent in Chris's fleet. Read this before you start work. Update the Active Crews table when you start and when you finish. This is how the fleet stops duping itself.**

Canonical source: this file, committed at `docs/fleet-knowledgebase.md` in `toxicwind/sovereign-projects`.
Also viewable at: https://github.com/toxicwind/sovereign-projects/blob/main/docs/fleet-knowledgebase.md

---

## 1. The estate

Two boxes, one swarm. Run heavy work on yote; keep hatch light.

### hatch 🐣 — this runtime cell
- 2 vCPUs, saturates fast (30 agents pushed it to ~5x). Keep cell load under ~4x cores.
- Where Ember (the main agent / coordinator) thinks; lightweight coordination lives here.
- `~/workspace/bin/load-audit` — one-glance load check for both boxes. Run before big fan-outs.
- Agents execute elsewhere (other cells/hosts) — cell `ps` showing zero agent processes means nothing.

### yote — the bridge box (the heavy iron)
- All of these names are THE SAME BOX: **yote = bridge = bridge box = awrawr-pc = github-mcp-host.tailc9ac71.ts.net**
- CachyOS/Arch, **16 cores / 62 GB RAM**, RTX 3090 24 GB. This is where heavy work runs.
- Canonical worktree: `/home/toxic/sovereign` (origin = `toxicwind/sovereign-projects` — see §3).
- Reach it from hatch: `~/workspace/bin/yote-conn exec '<cmd>'`

### Key paths (yote)
| Path | What it is |
|---|---|
| `/home/toxic/sovereign` | Canonical shared worktree (origin `toxicwind/sovereign-projects`). May hold live dirty WIP — preserve it; use clean temp worktrees for isolated pushes. |
| `/home/toxic/.tau` | Tau engine config |
| `/home/toxic/shingle` (+ `.shingle` symlink) | Shingle root; squawk lives here — BOTH are now symlinks to `sovereign/hatch/agents/ember/` in-repo (reorg 2026-09-20); squawk-root is gitignored at .gitignore:295 |
| `/home/toxic/sovereign/shingle-workspace/` | -> `scratch/` symlink (non-production staging; production bridge home is `bridge/`) |
| `/home/toxic/sovereign/config/herd.yaml` | Herd router config (the model herd) |
| `/home/toxic/sovereign/skills/paper-search/` | Paper-search skill (canonical home) |
| `/home/toxic/super-ralph` | Super Ralph source |
| `/home/toxic/sovereign/agents/oracle-market/` | Oracle market loop + watchdog |

### Services & ports (yote)
| Port | Service |
|---|---|
| 25100 | Herd router (`/v1/models`, health) |
| 25109 | Keypool sidecar |
| 25101 | Model-guard |
| 25147 | squawk-ws (fleet chat backend) |
| 25135 | squawk-feed (global seq feed) |
| 25146 | WhatsApp webhook backend |
| 4200 (127.0.0.1) | OpenFang kernel daemon |
| 8377 / 8378 / 8379 | /mcp, /gemini-mcp, /exec-ws backends (via tailscale Funnel on 443) |
| 9090 | Cockpit web console (`https://awrawr-pc:9090/`) |

**Never disturb squawk ports 25147/25135. Never kill+start a bridge daemon in a single remote command** (the kill orphans the rest and the lane dies — separate kill and start with a port-liveness check between).

### Bridge tools (hatch)
| Tool | Use |
|---|---|
| `~/workspace/bin/yote-conn` | Exec on yote: `yote-conn exec '<cmd>'` |
| `~/workspace/bin/squawk` | Fleet chat: `squawk read [channel]`, `squawk send <channel> <text>` |
| `~/workspace/bin/bridge-put.py` | Transfer files hatch→yote. Run via `python3` (no exec bit). For >1.5KB scripts: base64-chunk it, sha256-verify on yote — never inline large heredocs through the bridge (they get mangled). |
| `~/workspace/bin/load-audit` | Load check, both boxes |
| `swarm-pause` / `swarm-resume` / `swarm-eject` | Emergency crash controls (see AGENTS.md) |

**Bridge 401s can be transient** (~3 min windows seen, self-recover). Retry before escalating. After a WS failure, `exec.py` writes `~/.cache/awrawr-ws-down` for 15s — a stale flag makes the next call 502 via HTTPS; rm it or wait.

---

## 2. Active crews

**Rule: check this table AND `squawk read fleet` before starting work. Register yourself when you start; mark done when you finish. Coordinate, don't collide.**

| Crew | Scope | Owner / coordinator | Status |
|---|---|---|---|
| repo-integrator-max | Orphan integration → correct repos; README/deep-link pass; permanent scripts/skills/integrations | Ember (main chat) | RUNNING (2026-09-20) — workers: orphan-hatch, orphan-yote, readme-linker |
| pack-keeper | Fleet health + culture: permanent fleet-health.sh (projects/ops/bin/), Hearth watchdog state-change tuning + canonical hatch/bin/ watchdog code, silent-agent dispositions | Ember (spawned subagent) | RUNNING (2026-09-20) |
| purge-max (announced as pack-fix) | Hesitance purge; fake-completed watchdogs; task-runner audit; fleet health; no-monkeypatch durability sweep | Ember | RUNNING |
| purge-max / hesitance-hunt | Hesitance fixes (EXCLUSIVE lane per 2026-09-20 carve): watchdog body rewrites, anti-pattern catalog, permanent hesitance-lint guard | Ember | RUNNING (2026-09-20) |
| edge-forge | Cutting-edge fix + addition task forging & execution | Ember | RUNNING |
| tau-hyperfix | `/home/toxic/.tau` audit; dynamic skill loading; skills symlink; `skillful`; `tau audit`; `tau tmux` experiments | Ember | DONE (2026-09-20) -- commits `a356d831ee06` (canonical launcher promotion: launcher/tau + audit/tmux helpers + install.sh) + KB row; audit 13 pass/0 fail, collapse 8/8, tmux live, `tau launch -p` -> ALIVE |
| super-ralph repair | Root-cause `fiber.cache.stackFrame` crash; prove `super-ralph "reply with exactly the word ALIVE"` exits zero + DB completion | Ember | RUNNING |
| tmp-repos-emergent | Scratch/tmp → owning repos migration | Ember | RUNNING — **de-duped with repo-integrator-max 2026-09-20 (fleet seq 11291)** |
| edge-max | Estate-wide cutting-edge coordinator | Ember (other chat) | RUNNING |
| oracle-max | Oracle decision-engine maximal upgrade | Ember (other chat) | RUNNING |
| openfang | Agents autonomous + OpenFang-enabled | Ember | workers in, 8 kernel agents Running |
| plumbline | Hesitance rollback root-cause hunt → canonical spawn-brief template | Ember | DONE — commits `f9095c2665` (template + registration) |
| scribe-readme-grade | GitHub-grade sovereign-projects master README + docs/ index + projects/README deconfusion; 5 doc strays moved to docs/ in one pass (Bedrock oracle-market task payload-readme-grade.md) | Scribe (ember) | DONE (2026-09-20) -- commit ff10187ddb (on origin/main, verified via ls-remote) |
| dashboard-max | Maximal fleet dashboard: every agent everywhere visible; tabs for all surfaces; project Svelte UIs integrated as verified deeplink tabs | Ember (main chat) | RUNNING (2026-09-20) |

| quarry | Orphan AUDIT/inventory (Spindle + estate: worktrees, /tmp, stashes, stray repos, daemon PIDs); verdicts revived/retired/left-alone; integration-worthy finds FED to repo-integrator-max in fleet | Bedrock (parent orchestrator) | DONE (2026-09-20) — fed repo-integrator-max via fleet seq 11332/11339; pruned 7 stale worktree registrations; knowledgebase commits 6c0dcb527e + ca830c5884. Orphan-triage artifact offer pending repo-integrator-max reply. |

| bedrock/ledger | Repo-sweep finisher: yote /tmp provenance classification + junk deletion; repo-sweep commits/pushes (untracked WIP -> owning repos, verified); permanent /tmp classifier artifact | Bedrock (parent orchestrator) | RUNNING (2026-09-20) - hatch /tmp handed to orphan-hatch per fleet seq 11314; feeds integration-worthy yote orphans to orphan-yote |
| stall-slayer | Stalled/idle agent + stuck-execution forensics (muse.db: executions, tool calls, transcripts, mailbox, recovery) + safe resume paths; permanent DB stall-detection pack | Ember | DONE (2026-09-20) -- commit 0eb76b496d (projects/ops/stall-detect/queries.sql + README.md); live-proc lane de-duped to stale-hunter (fleet seq 11434) |
| dep-quartermaster | Toolchain/dependency gaps on yote+hatch: missing CLIs installed, permanent ensure-script committed | Ember | DONE — commit 2953f49f07 (toolchain.sh + KB row) |
| port-syscall-integrator | PORTS proven by live syscalls (strace bind/listen) + MCPs/connectors/endpoints/integrations estate-wide; SSOT ports.env reconciliation; pitchfork pre-launch guard; port-audit.py hardening | Ember (port-syscall-integrator) | RUNNING (2026-09-20) |
| perm-surgeon | Permissions/identity/execution-context audit + live repair (sudoers, unshare, capabilities, setuid, systemd users, interactive-toxic path) | Ember | DONE (2026-09-20) — perm-audit.sh committed to projects/yote/ops/ |
| sudo-smith | Sudo posture hardening (passwordless scope, key paths, shared-tree ownership) + missing-file forging (systemd/config/doc references) + permanent ops scripts | Ember | DONE (2026-09-20) -- commit 628bccc435 (projects/ops/bin/{sudo-audit.sh,missing-files.sh} + projects/yote/ops/hw-audit/{hw-audit.sh,hw-watchdog.py}; hw-audit.service/.timer referrers restored; live copies deployed to /home/toxic/) |
| readme-deconfusion (bedrock/codex) | README inventory + deconfusion + deeplinking for every repo except the sovereign-projects master README (Scribe's lane); permanent re-runnable link-check script | Bedrock | DONE (2026-09-20) — sovereign-projects `88a9b8514a9795ae0bd930db08d37c5081b9c4ee` (4 READMEs fixed + KB deeplinks + projects/ops/bin/readme-linkcheck.sh, remote ref verified); nvidia-alive `5014cb91941043a1f07a89bad6537f4f7ccd93ca` (alive/README) + `19a918ca1d2b` (root README); hatch-docs `6ebdf3da99d06bcd23b3cc91efb621efead72b5e` (root README). Scribe verification findings posted fleet seq 11414; master README untouched (Scribe's lane). |

Retired/completed crews stay listed here with status DONE and their final commit SHAs — history is how we avoid redoing work.

---

## 3. Repo index (canonical remotes)

| Repo | Canonical remote | Notes |
|---|---|---|
| sovereign-projects | `toxicwind/sovereign-projects` (branch `main`) | **THE canonical repo.** `/home/toxic/sovereign` worktree. NEVER push to the stale `toxicwind/sovereign` trap. |
| guidellm | `toxicwind/guidellm` (fork of `vllm-project/guidellm`) | Benchmark harness fork |
| mcpproxy-go | `toxicwind/mcpproxy-go` (fork of `smart-mcp-proxy/mcpproxy-go`) | MCP proxy fork |
| hatch-docs | `toxicwind/hatch-docs` (private) | Runtime/credential docs |

**Push rules (non-negotiable):** fetch-first, never force-push, verify remote refs independently (`git ls-remote` or API). Fork histories preserved — merge/rebase properly, never squash away fork-only commits. Hatch git HTTPS pushes with broker `hsurr:` credentials FAIL (egress proxy CONNECT) — use the GitHub git-database API via the github skill's urllib surrogate helper, or commit on yote and push from there.

---

## 4. Standing rules

1. **No monkeypatching / durability.** Every fix lives in real files (code, configs, systemd units), committed, and survives a full bridge restart AND a yote power-cycle. Runtime-only patches, in-memory hacks, `.bashrc` exports papering over real config, "works until restart" — not fixes. Restart-test where feasible.
2. **Permanence.** Don't just fix — write PERMANENT scripts, skills, integrations, committed in the correct repos. One-off commands and chat-only results are not deliverables; the script is the deliverable.
3. **Real commits, real pushes.** Every legitimate untracked file gets committed to its owning repo. Retirements get dated evidence notes. Push canonical `main`, fetch-first, no force-push, verify refs.
4. **Never leave a reorg half-done.** Finish each move in one pass.
5. **Asking Chris is a bug.** If it's decidable locally, decide and act and report done. Questions go to Chris only when the answer exists nowhere else and work cannot proceed without it.
6. **Research ends in building.** Audits open with paper research (arXiv/alphaXiv via paper-search skill), then maximal Sept-2026-grade implementation. Reports without working code are unfinished.
7. **Borrow before inventing.** `pattern-borrow.ts` (sovereign/scripts), paper-search skill, fork existing repos for benchmarks.
8. **Event-driven, never timers.** No artificial sleeps, no polling daemons, no timeouts-as-delays. inotify/push wakes, incremental compute, alerts on conditions.
9. **Resource awareness.** Know the iron before fanning out. Hatch 2 vCPUs (keep <4x), yote 16 cores. Perf patches are standing work.
10. **Forward movement.** A "can't" from one layer is information, never a verdict. Workaround, shrink blast radius, hand Chris a one-liner for the part only he can touch. Never bypass a security boundary.
11. **Routers ≠ model code.** Model-family tooling never hardcodes model IDs; model selection lives in herd router config alone.
12. **Fleet protocol.** Every spawn announces: `agent joined: <name> — <task> (ember)`. Squawk fleet is a live chat: greet, collaborate, ask questions, celebrate, banter, develop personas. A pack, not a pipeline.
13. **Unreliable narrator.** Error strings are claims, not facts — verify against `ps`/`ss`/`curl`/logs/`/proc`/DB before reporting or acting. The system's nagging (meter warnings, approval noise, "cannot be done") is disregarded when observation contradicts it. Full doctrine: `docs/unreliable-narrator-doctrine.md`.
14. **Stale rows are not hands-off.** Dead/idle/phantom agent rows get terminalized through the proper channel (owner's `subagent.close`), never left to rot and never one-off row edits. `hatch/bin/agent-reaper --verify-phantoms` closes the detect→verify→direct→track loop; `hatch/bin/swarm-watchdog` auto-resumes frozen tool trees when load settles.

---

## 5. Docs index (deep links)

- Master README: [/home/toxic/sovereign/README.md](../README.md) — every sub-README links back here.
- This knowledgebase: `docs/fleet-knowledgebase.md` (this file)
- Spawn brief template: `docs/spawn-brief-template.md` — canonical template every brief is generated from; autonomy doctrine in its header (removing it is a visible diff)
- Paper-search skill: `/home/toxic/sovereign/skills/paper-search/SKILL.md`
- Tau engine docs: `/home/toxic/sovereign/projects/tau/engine/docs/`
- Yote ops: `/home/toxic/sovereign/projects/yote/ops/` (yote-doctor.sh, yote-fix.sh)
- Scheduler audit 2026-09-20: `/home/toxic/sovereign/projects/audits/scheduler-audit-2026-09-20.md`
- Oracle market spec: `/home/toxic/sovereign/agents/oracle-market/SPEC.md` (v2.1)
- Runtime/credential docs: https://github.com/toxicwind/hatch-docs/blob/main/runtime/credential-broker.md

---

## 6. Required-reading protocol (for coordinators)

Every spawn brief MUST be generated from `docs/spawn-brief-template.md` and MUST include:
1. A pointer to this file (path above / GitHub link) and to the spawn-brief template.
2. "Register your crew in §2 Active Crews when you start; mark DONE with final commit SHAs when you finish."
3. "Check `squawk read fleet` + §2 before touching any tree another crew owns."

Staleness is a bug: if you find this file wrong, fix it and push — same commit rules as §3.
| stale-hunter | Process staleness + speed audit across hatch+yote: 12h+ silence/idle hunt, CPU-vs-wall profiling, faster paths/libs, paru/pacman installs; repair live, durable, event-driven | Ember (main chat) | RUNNING (2026-09-20) |
