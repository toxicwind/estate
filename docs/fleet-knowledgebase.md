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
- Compaction trigger (2026-09-20): 170000 was staged in `/etc/hatch/env.override` then WIPED by a 19:26 host re-provision (env, env.override, credentials all re-rendered; override + `.orig` both gone) — env.override is NOT a durable ops surface; the durable source is host fleet enrollment (outside the cell). Live trigger still 150000. Daemon rebuilt 2026-09-20 ~21:03 (hatch 0.1.0 `82d6744eed2`); jarvis-static re-run: compaction subsystem unchanged.

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
| 25196 (127.0.0.1) | OpenFang kernel daemon (single instance; dashboard UI + /v1 + /api) |
| 25103 | OpenFang mesh-front (public proxy -> :25196 kernel, serves /mesh/* features) |
| 8377 / 8378 / 8379 | /mcp, /gemini-mcp, /exec-ws backends (via tailscale Funnel on 443) |
| 25212 | Cockpit web console (`https://awrawr-pc:25212/`, moved from :9090 via systemd drop-in 2026-09-20) |

**Never disturb squawk ports 25147/25135. Never kill+start a bridge daemon in a single remote command** (the kill orphans the rest and the lane dies — separate kill and start with a port-liveness check between).

**Directive 2026-09-21 (Chris, revised):** the reboot/restart ban covers ONLY the physical host, the yote bridge daemon, and the hatch daemon (PID 67). SERVICE restarts/repairs are fully fine — restart the single broken pitchfork daemon, not the supervisor. Live hotfix (ptrace/strace against running processes) is preferred where it fits: hotfix live first, restart the service if cleaner, never touch host/bridge/hatch.

**2026-09-20 boot incident:** ember-rebootwright's kernel cutover rebooted the box 19:37:53 MDT; clean shutdown 19:38:14; NO boot until 21:39:02 (~2h dark vs 2-4 min expected — machine sat off/pre-kernel, boot trigger unverified: physical press / WoL / AC restore). Now on **7.2.6-1-cachyos-bore** (verified live `uname -r` 2026-09-21). Post-boot fallout fully repaired (black-screen fix + daemon-repair, see §2).

**PER-KERNEL RULE (2026-09-20):** every installed kernel flavor needs its matching `linux-cachyos-<flavor>-nvidia-open` package + rebuilt initramfs, or the console goes black on the next switch. bore had no nvidia driver → sddm couldn't render the greeter on the RTX 3090 (black DP-1/DP-2) and `Conflicts=getty@tty1.service` stopped getty@tty1 → no console fallback either. Fixed 2026-09-20 ~21:47: installed `linux-cachyos-bore-nvidia-open 7.2.6-1`, `mkinitcpio -p linux-cachyos-bore`, modprobed nvidia_drm, restarted sddm. All three 7.2.6 flavors now covered.

**/mnt/8TB (2026-09-20):** remounted via ntfs-3g — `ntfsfix /dev/sdb2` cleared the dirty flag ($MFTMirr corrected, journal emptied) but the kernel ntfs3 driver still refused the volume; ntfs-3g (fuse2 dep) mounted it — 7.3T, 922G used, data intact. fstab switched ntfs3→ntfs-3g (backup /etc/fstab.bak-20260920) — survives reboot.

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
| lane-goals | Goals-lane maximal triage: all 17 goal dirs to final verdicts; mcpproxy-go merged build (ad8b0a26); fleet-code collaborative-coding tool (1db0060d); bridge auto-racer (fd3f91de); config naming cleanup (5b75abdb) | lane-goals (Ember's crew) | DONE (2026-09-21) -- 4 pushed SHAs, all ls-remote verified |
| tau-tmux-mcp | Tau/tmux/MCP audit+repair: tau health, tmux session map, 33-server MCP gateway inventory, repair 8 error servers, tmux-mcp hardening | Ember | DONE (2026-09-20) -- commits d2145a9df5 (tmux-mcp v2.0: socket discovery + destructive-send gating), c9fc75f6ce (websearch-mcp stdlib wrapper), 92fafc3f26 (8 quarantined servers repaired: paths/pins/env), 995dd1924b + c7e24ee791 (READMEs); verified: tpc 9 tools, orchestration 35 tools, sqlite 6 tools, qdrant 4 tools, filesystem v1.3.0, all handshakes OK; shep restarted healthy |
| repo-integrator-max | Orphan integration -> correct repos; README/deep-link pass; permanent scripts/skills/integrations | Ember (main chat) | DONE (2026-09-20) -- KB live (f9f2ef74fe); orphan-hatch DONE (12 commits sovereign-projects + 2 hatch-docs, main 66cc227a86/eeae7b4a76); orphan-yote DONE (5 repos: rig 6b6742c, gear 3afd4a0, herd 6528c7a, media fb95ee2f3f, herd-phase3-retire dea49bf archived); readme-linker DONE (main 31f5ab6ec2); orphan-yote-2 DONE (quarry feed consumed, main 4eabd325f2) |
| orphan-yote-2 | Quarry feed seq 11332+11339 orphan integration (worker under repo-integrator-max) | Ember (spawned subagent) | DONE (2026-09-20) — 11332: orphan-commit merge `1819f344aa`, PID cleanup `7eb29895b4`, phase3-operator-rename merge `9aa2e0c046`, eval-wt merge `8a9dda8287` (2 unique commits + 4 RANKING mds), ctm-mode-fix worktree removed, stashes 0-2 dropped (hashes recorded), sovereign-history deleted (objects in .git.bak-20260913); 11339: session-burn-radar→local-work-archive `d7ebc8b26a`, 4/6 no-remote repos already integrated, crew-b-f844 left (fleet experiment), kimi-auto duplicate resolved, /home/toxic/squawk LIVE (not touched), 24 husks audited (7 active, 16 stale real projects, none deleted) |
| orphan-hatch | Hatch orphan integration (worker under repo-integrator-max) | Ember (spawned subagent) | DONE (2026-09-20) — sovereign-projects main c33e91ae51 (12 commits): resurrect-probe, debate-oracle audit, bid-market E2E, bin manifest, bg-tracker, oracle spec, stale-hunter+websearch, awrawr-mcp HFT, cross-box router, debate E2E, fleet-health fix, monkeypatch-detect fix; hatch-docs main eeae7b4 (product docs + personas); nvidia-alive 2484ed56 (verified); 100+ ledger entries, 43 workspace items classified |
| pack-keeper | Fleet health + culture: permanent fleet-health.sh (projects/ops/bin/), Hearth watchdog state-change tuning + canonical hatch/bin/ watchdog code, silent-agent dispositions | Ember (spawned subagent) | DONE (2026-09-20) — commits ba421688648818b740cece02e97a0ade128f0a2b, 3b923993a1d220ac035b1bb86d49a66320f99837 |
| purge-max (announced as pack-fix) | Hesitance purge; fake-completed watchdogs; task-runner audit; fleet health; no-monkeypatch durability sweep | Ember | RUNNING |
| purge-max / hesitance-hunt | Hesitance fixes (EXCLUSIVE lane per 2026-09-20 carve): watchdog body rewrites, anti-pattern catalog, permanent hesitance-lint guard | Ember | RUNNING (2026-09-20) |
| edge-forge | Cutting-edge fix + addition task forging & execution | Ember | RUNNING |
| tau-hyperfix | `/home/toxic/.tau` audit; dynamic skill loading; skills symlink; `skillful`; `tau audit`; `tau tmux` experiments | Ember | DONE (2026-09-21) -- audit 14 pass / 0 warn / 0 fail; all 3 stale warnings fixed in tau-audit.sh and pushed to origin/main: (1) branch-behind demoted to INFO (canonical ref is origin/main; shared tree never touched), (2) dirty-WIP replaced by content-vs-main drift check (untracked on-main files = branch-lag detritus, mode-only noise ignored; synthetic new-file test still warns), (3) hardcoded :8379 replaced by WS_EXEC_PORT read from pitchfork [daemons.awrawr-ws-exec] (=25204). Commits b3a509d8e3 + f8d303dfbd, remote-verified. tmux lifecycle (new/ls/capture/kill) OK, `tau launch -p` -> TAU_OK (~15s), dist/omp healthy, install.sh idempotent. Frontmatter sampling warning fixed at the source: rust-browser-pilot description: moved up (gk-live-gear e4d72e3). Launcher deliverables byte-identical on origin/main; historical caveat stands: local commits a356d831ee06 / 3c8c5566cf are orphaned and NOT canonical SHAs -- nothing left to push. |
| super-ralph repair | Root-cause `fiber.cache.stackFrame` crash; prove `super-ralph "reply with exactly the word ALIVE"` exits zero + DB completion | Ember | RUNNING |
| ralph-accept | Super-ralph finite acceptance: unblock ALIVE run (stale .secrets NIM_BASE_URL, :25193 proxy POST hang) + structured completion validator at quiescence | ember-ralph-accept (Ember's crew) | DONE (2026-09-21) -- super-ralph main 4d1b3ba (CLI deterministic exact-reply: strips agent quotes, byte-verifies, 5-byte ALIVE stdout, exit 0); sovereign-projects main 84165f5a (deploy-cell.py: canonical yote-connector deploy, PPID 1 detached, health OK); acceptance: /tmp/sr-accept10 stdout 414c495645 (5B), DB reply ALIVE (5B), validator valid=1, run finished |
| ralph-alive2 | Super-ralph ALIVE acceptance finish: diagnose 0-byte stdout discrepancy vs KB claim, fix root cause, re-run to byte-exact ALIVE | ember-ralph-alive2 (Ember's crew) | RUNNING |
| inbound-probe | TRUE user→Telegram→bot inbound E2E: sent real MTProto message as puppertrix (user session, not bot) to @crawlspace_coyote_bot; bot polled, inbox committed, OpenFang replied | inbound-probe (Ember's crew) | DONE (2026-09-21) -- update 3988729: cursor 3988729->3988730, inbox processed (1 attempt), DLQ 0, reply 'inbound-e2e-20260921-122819 PONG' via=openfang of_ms=1555, round-trip 2s; fleet announced 11916-ember-msg.md |
| tmp-repos-emergent | Scratch/tmp → owning repos migration | Ember | RUNNING — **de-duped with repo-integrator-max 2026-09-20 (fleet seq 11291)** |
| edge-max | Estate-wide cutting-edge coordinator | Ember (other chat) | RUNNING |
| edge-additions | September-2026 cutting-edge additions (edge-max worker): keypool KEYPOOL_RACE_KEYS first-valid-wins racing, hft-latency --hedge-ms hedged launch, read-only calibrated routing-score publisher, squawk history_search CLI | Ember (edge-max crew) | DONE (2026-09-20) -- branch edge-max-20260920 commits c979437f26 (docs/evidence), adaaf1e80d (keypool recovery fix), 97d88d6f48 (squawk history_search), 15acd0f15c (routing-score), 8bba83a0fc (hft-latency --hedge-ms), a03edca0e2 (keypool racing); verified: selftest x5, race sidecar x3, hft/routing/squawk suites x3 each, legacy serial OK, real-root sanity OK; remote ref verified via ls-remote |
| oracle-max | Oracle decision-engine maximal upgrade | Ember (other chat) | RUNNING |
| oracle-hardening | Oracle decision-engine hardening (oracle-max child): router-separation fix (aliases only, concrete IDs refused), double-calibration removal (engine owns, exact-once proven), debate re-aggregation (parallel/diverse/bounded/fail-open, finals re-enter engine half-weight), resilient judges (null-content robustness, bounded retry, honest attempt accounting), framing fail-closed, canonical verdict-hash regression | oracle-hardening (Ember's crew) | DONE (2026-09-20) -- commits cbc73330ee (core), 2324269824 (null-content), 6b41fb5930 (harness timeouts), f3f56a4ab0 (hash test), 7e9fc6e119 (alias targets), 9ed0447bf3 (floors); sovereign-projects main 9ed0447bf3 verified via ls-remote; proofs: test_core 90/90, abstention 11/11, judge return 13/15 (CP lo 0.6366 vs old 0.3596); live /ask 200 tier=DEBATE p=0.179 latency=157s cost=$0.048 hash=b1b40ff1998ab436; deployed to /home/toxic/sovereign, oracle-core restarted via pitchfork |
| openfang | Agents autonomous + OpenFang-enabled | Ember | workers in, 8 kernel agents Running |
| herd-healer | Event-driven dead-peer self-healing for the herd router (per-peer FSM, EWMA, single-flight half-open) | Ember | DONE (2026-09-20): feature 837810e422, merge abe7bbb65d; re-verified live 2026-09-20 by ember-edge-selfheal (edge-forge #3 re-dispatch — coordinator claim of "no commits" was wrong, feature already on main): live binary 2026-09-20 17:04 contains peer_circuit_open + GET /peer-health; :25100 /peer-health serving per-peer FSM (healthy, threshold 8); projects/herd/scripts/probe-peer-health.sh ALL ASSERTIONS PASSED (weighted ejection, fail-fast 503 peer_circuit_open with backend untouched, half-open probe on real traffic, readmission, 200-empty weighted re-ejection); supervised herd PID 3124908 (started 17:24) runs the feature binary |
| plumbline | Hesitance rollback root-cause hunt → canonical spawn-brief template | Ember | DONE — commits `f9095c2665` (template + registration) |
| dashboard-max | Maximal fleet dashboard: every agent everywhere visible; tabs for all surfaces; project Svelte UIs integrated as verified deeplink tabs | Ember (main chat) | RUNNING (2026-09-20) |
| scribe-readme-grade | GitHub-grade sovereign-projects master README + docs/ index + projects/README deconfusion; 5 doc strays moved to docs/ in one pass (Bedrock oracle-market task payload-readme-grade.md) | Scribe (ember) | DONE (2026-09-20) -- commit ff10187ddb (on origin/main, verified via ls-remote) |
| quarry | Orphan AUDIT/inventory (Spindle + estate: worktrees, /tmp, stashes, stray repos, daemon PIDs); verdicts revived/retired/left-alone; integration-worthy finds FED to repo-integrator-max in fleet | Bedrock (parent orchestrator) | DONE (2026-09-20) — fed repo-integrator-max via fleet seq 11332/11339; pruned 7 stale worktree registrations; knowledgebase commits 6c0dcb527e + ca830c5884. Orphan-triage artifact offer pending repo-integrator-max reply. |
| bedrock/ledger | Repo-sweep finisher: yote /tmp provenance classification + junk deletion; repo-sweep commits/pushes (untracked WIP -> owning repos, verified); permanent /tmp classifier artifact | Bedrock (parent orchestrator) | RUNNING (2026-09-20) - hatch /tmp handed to orphan-hatch per fleet seq 11314; feeds integration-worthy yote orphans to orphan-yote |
| stall-slayer | Stalled/idle agent + stuck-execution forensics (muse.db: executions, tool calls, transcripts, mailbox, recovery) + safe resume paths; permanent DB stall-detection pack | Ember | DONE (2026-09-20) -- commit 0eb76b496d (projects/ops/stall-detect/queries.sql + README.md); live-proc lane de-duped to stale-hunter (fleet seq 11434) |
| yote-consolidation (ember-ironwright) | Herd FQN + config durability + Telegram delivery (Chris directive) | ember-ironwright (Ember's crew) | DONE (2026-09-21): WS1 FQN regression (sovereign-swap main 61e497ee) + immutable deploy live :25100; bare+FQN 200, incident FQN 200, openfang:coyote 200. WS2: manifest.yaml, estate-reconcile 12/12, real-drift restore, OpenFang SQLite self-heal (0-byte DB found). WS3: sqlite inbox+cursor+dedupe+DLQ live :25102, 44/44 tests, crash-replay PASS, e2e send ok + dupe denied. |
| dep-quartermaster | Toolchain/dependency gaps on yote+hatch: missing CLIs installed, permanent ensure-script committed | Ember | DONE — commit 2953f49f07 (toolchain.sh + KB row) |
| bridge-max | Maximal bridge exec layer: multitask dispatch (POST /exec-multi, yote-conn multi), detached background dispatch (POST /exec-bg, GET /bg, yote-conn bg/bg-status/bg-list), bg-kill (POST /bg/<handle>/kill, yote-conn bg-kill), MCP exec_multi/exec_bg/bg_status tools; reap-on-query stale jobs (pid-reuse-safe /proc cmdline check) | Ember | DONE (2026-09-20) -- commits 25679fa5c0 (core), ae890221a2 (marker), efe63f8115 (reap-on-query + bg-kill), f59949ae0c (follow-up marker); connector v2.1 live (daemon PID 40978); kill path live-tested (SIGTERM process group -> stale, zero survivors) |
| port-syscall-integrator | PORTS proven by live syscalls (strace bind/listen) + MCPs/connectors/endpoints/integrations estate-wide; SSOT ports.env reconciliation; pitchfork pre-launch guard; port-audit.py hardening | Ember (port-syscall-integrator) | DONE (2026-09-20) -- core fix fc6b912a91 (kimi-code --no-port-walk fail-fast on EADDRINUSE; live 25126 health 200); hardening DONE by port-guard-harden: commits 7f6146bc42 (hardened port-audit.py: /proc cmdline+ancestry attribution, intentional alias groups, dynamic-pool classification, exit 0/1/2 + --strict/--json; claim-port rewritten as fail-fast pre-launch guard - no kills/sleeps/polls, exit 4 occupied with holder cmdlines, exit 5 protected ports 8379/25204/25147/25135 incl. protected-holder cmdline detection; ports.env hygiene: retired ZEDRA_HOST_PORT + dup NULL_G_PROXY_PORT removed, WAYLAND_MCP_PORT -> SQUAWK_FEED_PORT, owner hints for 25101/25108/25114/25120/25145/25199) + f0c63dca77 (tracked bin/port-audit.py + bin/tests, bin/port-audit wrapper, README). 21 stdlib-unittest tests pass on yote; live audit exits 0 on healthy estate; occupied-port refusal proven live (exit 4, holder survives, payload not executed); kimi restarted via pitchfork-restart through new guard (pid 2976788, :25126 health 200). |
| perm-surgeon | Permissions/identity/execution-context audit + live repair (sudoers, unshare, capabilities, setuid, systemd users, interactive-toxic path) | Ember | DONE (2026-09-20) — perm-audit.sh committed to projects/yote/ops/ |
| sudo-smith | Sudo posture hardening (passwordless scope, key paths, shared-tree ownership) + missing-file forging (systemd/config/doc references) + permanent ops scripts | Ember | DONE (2026-09-20) -- commit 628bccc435 (projects/ops/bin/{sudo-audit.sh,missing-files.sh} + projects/yote/ops/hw-audit/{hw-audit.sh,hw-watchdog.py}; hw-audit.service/.timer referrers restored; live copies deployed to /home/toxic/) |
| readme-deconfusion (bedrock/codex) | README inventory + deconfusion + deeplinking for every repo except the sovereign-projects master README (Scribe's lane); permanent re-runnable link-check script | Bedrock | DONE (2026-09-20) — sovereign-projects `88a9b8514a9795ae0bd930db08d37c5081b9c4ee` (4 READMEs fixed + KB deeplinks + projects/ops/bin/readme-linkcheck.sh, remote ref verified); nvidia-alive `5014cb91941043a1f07a89bad6537f4f7ccd93ca` (alive/README) + `19a918ca1d2b` (root README); hatch-docs `6ebdf3da99d06bcd23b3cc91efb621efead72b5e` (root README). Scribe verification findings posted fleet seq 11414; master README untouched (Scribe's lane). |
| daemon-repair | Post-kernel-cutover yote daemon repair (Ember crew): evicted 76 stale pitchfork registrations (herd-healer / wt-kimi-failfast / wt-port-guard-20260920 / sovereign-phase3-rename port-race duplicates that stole ports and errored the canonical sovereign daemons), restarted sovereign/sovereign-chat; verified herd :25100, keypool :25109, model-guard :25101, kimi-auto-shim :25153, toolcall-llm :25152, beellama :25122 all /health 200, squawk-feed /seq advancing, herd /v1/models serving, 0 errored daemons | ember-wrenchwright (Ember's crew) | DONE (2026-09-20) -- operational state fix, no repo file changes; stale worktrees remain on disk (deregistered, will not auto-start) |
| kimi-unlock-audit | Kimi tooling decoupled from Kimi models: router-config-only routing (zero selection/ranking/probing/timers in Kimi-named code); resolver+state.json retired; Kimi /tmp audit; deduplicated super-ralph feed | Ember | DONE (2026-09-20) -- toxicwind/kimi-auto@ab91ebb090c (v3.0 router-config cutover) + sovereign-projects@5fa02571292b (cutover) + @1cbe5cb3f597a (honest /health), all verified via git ls-remote; live proofs: model kimi-auto -> ministral-14b-latest exact UNLOCK-PROOF-7X3Q on :25100+:25153, SSE verbatim, 508 self-loop, 503-when-unroutable health; feed via fleet seq 11575/11595/11613 |
| anvil | Durability sweep: kill recurring monkey-patches; permanent audit (ops/durability/), OpenFang launcher typo fix + TOML wiring | Bedrock | DONE (2026-09-20) -- commit f69a3a4ab6be41028d365e7b3dc23f57b1623b22 |
| guidellm-eval | GuideLLM fork pluggable scoring + deterministic instruction-following eval; provider-free OpenRouter quality-first ranking (9 ranked + 1 fallback tier) | Ember (subagent) | DONE (2026-09-20) -- toxicwind/guidellm 94952a7d051fb88a0f9b4a12d0642dbb265fc7d4 (malformed-thinking + thinking tag + expected-note); toxicwind/sovereign-projects c5192a0d6e16fadd17c5226fd137282b43b09ada (final clean run 20260920-170706: 9 ranked + 1 fallback, ranking_lib tier contract, 8 lib tests; GuideLLM suite: 292 benchmark + 623 scoring/schemas pass) |
| suture | Watchdog surgery (5 cases): Hearth/progress-watchdog dedup + honest pulse; verifiable swarm pause; atomic run ledgers; oracle intake per-request triage (killed false "stalled 24,206s"); super-ralph vs omp-router doc correction | Suture (Bedrock crew) | DONE (2026-09-20) -- commits aabb87bc3b (surgery) + 1999fb3643 (+x restore), remote ref verified via ls-remote |
| zed-qed | QED maximal readiness (projects/qed): zed fork 241 crates + zedra remote substrate — schema-normalizer dedup across 3 providers, nullable-recursion fix, zedra workspace repair (7 crates resolve), settings_ui autonomous_edits fix, README/AUDIT deconfusion | Ember (zed-qed) | DONE 2026-09-20 — commits a87f5e5189 (normalizer+zedra+docs), d77c1ce7fd (ZED_SYNC.md), 7ac0dc03b6 (README link), f42ca9e4e4 (rustfmt), db4179319a (settings_ui fix). PROOF: cargo check --package zed EXIT 0; 5/5 normalizer tests pass; zedra workspace check clean; bun check clean |
| ember-rebootwright | Infra ports assessment + crew-b-f844 snapshot cleanup + staged yote kernel cutover (7.1.5-1 -> 7.2.6-1) | ember-rebootwright (Ember's crew) | DONE (2026-09-21) -- cutover EXECUTED 19:37:53 MDT via /tmp/kernel-cutover.sh (sha256 ad596f83); clean shutdown 19:38:14; NO boot until 21:39:02 MDT (~2h dark vs 2-4 min expected -- machine sat off/pre-kernel, boot trigger unverified: physical press / WoL / AC restore); now on 7.2.6-1-cachyos-bore (verified live `uname -r` 2026-09-21). Post-boot fallout fully repaired: (a) black-screen fix 2026-09-20 ~21:47 (bore had no nvidia driver -- installed linux-cachyos-bore-nvidia-open 7.2.6-1, mkinitcpio -p, sddm restarted, greeter on DP-1/DP-2; PER-KERNEL RULE in §1); (b) daemon-repair crew evicted 76 stale pitchfork registrations, all serve backends /health 200. Ports: cockpit 9090->25212 via systemd drop-in, curl -k 200 verified. crew-b-f844 moved to /home/toxic/.trash-20260920/crew-b-f844 (recoverable) |
| lane-reaper-squawk | Reaper cleanup + squawk durability: phantom census re-verified (2 true phantoms, owner root 51dc2bca proven LIVE — prior 'owner completed' ledger note corrected), reaper residue-classification state machine (direct -> escalation -> awaiting_owner / residue), squawk send mkdir-in-flock fix for new-channel silent drops | lane-reaper-squawk (Ember's crew) | DONE (2026-09-21) — commits `412063a43a` (reaper residue state machine, squawk mkdir-in-flock, README rows, KB registration); origin/main = 412063a43a verified via git ls-remote; deployed to ~/workspace/bin/ on hatch; proofs: state-machine unit tests 6/6, 16-way concurrent publish seqs 1-16 unique+contiguous+frontmatter-clean, 2 phantoms re-verified TRUE + awaiting-owner |
| lane-dispatcher | canonical dispatcher/ledger build: mission/coordinator/worker/relay IDs, lifecycle+result tracking, direct-Chris precedence, duplicate-admission locks, append-only hash-chained relay records, artifact/commit aggregation, automatic relay archival, exactly-four-audit-lanes enforcement | lane-dispatcher (Ember's crew) | DONE (2026-09-21) -- impl commit `c6e9acd9b3f2993d9e55617e2596a2399d9df7f5` on origin/main (ls-remote verified): `projects/ops/dispatcher/` (fleet_dispatch package: ledger/ids/admission/relay/dispatcher, bin/dispatch CLI, 24-test stdlib suite ALL PASS, README); projects/ops/README.md dispatcher entry; .gitignore state/ exclusion. Restart proof: E2E CLI drill + TestRestart (new Dispatcher continues IDs/locks/ledger chain). Triage folded in: sovereign-chat dispatch.ts = internal lease queue (below this layer); fleet/dispatch_fallback.py = transport fallback (complementary); oracle intake = triage front door (this is the dispatch side). |
| jarvis-decode-pass1 | hatch-decode pass 1 (jarvis static-audit binary layer) | Ember | DONE (2026-09-20) -- sovereign-projects `0734b5ca93c76dffa097777bc34e289ace403ffa` (ancestor of origin/main, verified 2026-09-21) |
| jarvis-oracle-pass2 | Oracle pass 2: 153 exact JARVIS_* names + 30 u64 defaults | Ember | DONE (2026-09-20) -- sovereign-projects `76fed7d2f36ec2dd097279aa056fc13b1da8cdc7` (ancestor of origin/main, verified 2026-09-21) |
| jarvis-decode-pass3 | Hatch decode pass 3 on rebuilt binary e86e3030628: 158 exact JARVIS_* names (new shape-E SIMD cst-pool scanner; 8 vars pass-2 thought removed proven live incl JARVIS_COMPACTION_HEARTBEAT_SECS dflt 30 + JARVIS_ALLOW_DIRECT_COMMAND_EXEC live case-insensitive gate); dual default adjudicated (CHUNK_IDLE 90000 interactive / 180000 cron, flag-selected fn 0xda0f7b0); avocado trigger resolver live 0x9a5bdc0 (200000/150000) once-lazy dispatch; eager_compaction.rs source-attributed; capstone pinned + 6 regression tests | palimpsest (Ember's crew) | DONE (2026-09-21) -- sovereign-projects 858647e758 (origin/main, ls-remote verified) |
| readme-maximalization | README maximalization + deeplinking (Sept-2026 GitHub feature set): 7 files -- root + docs/ + docs/README-INDEX.md (445-file map) + projects/ + bridge/ + hatch/ + agents/oracle-market/; routing doctrine + Kimi footnote embedded | Ember | DONE (2026-09-20) -- sovereign-projects `c6bc997e1339eee9503e6fac8c5ab7c5cc96c42a` (ancestor of origin/main, verified 2026-09-21) |
| pitchfork-port-fix | Pitchfork literal-port fix: cherry-picked `483e27818a` from nim-probe-20260920 -- pitchfork.toml toolcall-llm run line literal `--port 25152` (was `${TOOLCALL_PORT}` stoi crash loop) + stack/services/beellama-fast.sh SSOT port | Ember | DONE (2026-09-20) -- sovereign-projects `eaac1f3628ab1fd4609fc089c7832306f1ae766e`; verified: toolcall-llm :25152 + beellama-fast :25122 /health 200 |
| squawk-atomic-seq | Squawk atomic seq fix: killed the read-max-then-write race -- per-channel `flock`, base64 payload, `@SEQ@` substituted in-lock; 8 parallel publishers -> unique contiguous seqs; CLI adopted into `hatch/bin/squawk` (durable integration) | Ember | DONE (2026-09-20) -- sovereign-projects `682b6c6264b6d72d981189d5d60d32b0551ef21d` (ancestor of origin/main, verified 2026-09-21) |
| jarvis-drift-note | Daemon-rebuild drift note: hatch 0.1.0 `82d6744eed2` (PID 67 restarted 2026-09-20 ~21:03) -- jarvis-static re-run: compaction subsystem UNCHANGED (B1-B19 still hold); new `tool_dispatch_heartbeat` tool | Ember | DONE (2026-09-20) -- sovereign-projects `83083df12351c3109806aed7a3d1e0f0b5478d40` (`hatch/audit-jarvis/daemon-rebuild-drift-2026-09-20.md`) |
| kimi-web-ui-dedup | Kimi web UI dedup | Ember | DONE -- sovereign-projects `06f0a5c08204bff901af0377c4da5b58e8d2b098` (ancestor of origin/main, verified 2026-09-21) |
| stall-slayer-q8 | Stall Slayer Q8 | Ember | DONE -- sovereign-projects `d5b6a816defe098b6971111a2ad75c6237d54d2f` (ancestor of origin/main, verified 2026-09-21) |
| estate-reconcile-watch-reg | Register estate-reconcile watch as a Pitchfork daemon (WS2 gap close) | register-pitchfork | DONE (2026-09-21) -- sovereign-projects b6b4c5a1634 (pitchfork.toml [daemons.estate-reconcile-watch] entry) + nim-probe live toml appended; pitchfork start/stop/start verified: PID 891181 -> stop -> PID 892919 running, inotifywait watch live on 3 manifest dirs; synthetic herd-keypool.py drift detected in ~8s, ALERT (unsigned-HEAD rule, no untrusted restore), drift reverted, check OK 4/4; remote ref verified |
| yote-console-fix | yote console black-screen fix (post-kernel-switch): bore flavor had no nvidia driver -> sddm couldn't render on RTX 3090 (black DP-1/DP-2) and `Conflicts=getty@tty1.service` killed the console fallback; installed `linux-cachyos-bore-nvidia-open 7.2.6-1`, `mkinitcpio -p linux-cachyos-bore`, modprobed nvidia_drm, restarted sddm -- greeter active; all three 7.2.6 flavors now covered | Ember | DONE (2026-09-20) -- operational fix, no repo changes; PER-KERNEL RULE recorded in §1 |
| kb-scribe | Fleet KB update: 9 verified DONE rows added (all SHAs ancestor-checked vs origin/main), tau-hyperfix SHA corrected (a356d831ee06 is local-only, not canonical), boot-incident + per-kernel-nvidia + compaction-trigger + /mnt/8TB notes added, §2 table consolidated (dup dashboard-max dropped, misplaced tail rows moved in) | kb-scribe (Ember's crew) | DONE (2026-09-21) -- pushed in this commit (SHA reported to fleet) |
| lane-oracle-connector | Oracle intake adoption (verified complete, zero oracle code changes) + yote-connector canonicalization: yote-conn promoted to the single canonical operator path | lane-oracle-connector (Ember's crew) | DONE (2026-09-20) -- sovereign-projects main `0f4f3bdadf032d8030db2bcab928efbf93dbb739` (ls-remote verified): (A) oracle adoption PROVEN live — `agents/oracle-market/docs/ADOPTION-PROOF.md`: intake unit test OK (6 routes), live TASK (ledger settled, winner bidder-scout), live REJECT, live DIRECT; ORACLE_INTAKE=1 in running process env; no oracle source touched. (B) canonicalization — bg-tail finished end-to-end (`bg-status.py` offset args -> `stdout_b64/stdout_soff`, daemon `GET /bg/<handle>?soff=&eoff=`, CLI resume/negative-offset/tails-fallback; fixed empty-chunk resume + stdout ordering bugs caught in live test); `/exec-bg` `timeout_s` + `workdir` now forwarded to bg-run.py (both silently dropped before — workdir ran in /home/toxic regardless); `projects/bridge/hatch/yote-conn` updated to the live CLI (169->222 lines) and added to `deploy-cell.py` FILES with chmod 755; `bexec` -> thin `yote-conn exec` shim (adopted as `hatch/bin/bexec`); `fleet-classify` -> yote-conn transport (raw exec.py fallback kept); `swarm-{eject,resume,watchdog}` DELIBERATELY keep raw exec.py (emergency path when 18301 is down — commented); bridge README canonical-path policy section. Deployed: daemon restarted via deploy-yote-connector, health ok (transport ws); live-tested bg-tail resume, workdir (/tmp file created), timeout (state=timeout, exit -1), bg-kill (SIGTERM, exit -15). |
| stale-hunter | Process staleness + speed audit across hatch+yote: 12h+ silence/idle hunt, CPU-vs-wall profiling, faster paths/libs, paru/pacman installs; repair live, durable, event-driven | Ember (main chat) | RUNNING (2026-09-20) |
| oracle-experiments | Oracle deep proving suite: labeled eval vs outcomes (KalshiBench N=100), escalation analysis, latency/cost per tier, default tuning with rationale, co-failure certificate | oracle-experiments (Ember's crew, under oracle-max) | RUNNING (2026-09-20) |
| nightjar | Night-lanes coordinator: super-ralph execution-path degradation (77%->30% success last 24h, winners run 4+ min then produce empty output -> slashed for no-result) — root-cause, maximal durable fix, live proof through the market loop. Adjacent to super-ralph repair (fiber.cache.stackFrame crash) and ralph-alive2 crews — coordinating, not duping. | Nightjar (Ember's crew) | RUNNING (2026-09-21) |

| modelmap-round2 | Model-stack round 2 (Chris: "Fix all three of those maximally"): (1) oracle-judge-local re-entrant shim deadlock -- shim hosted INSIDE llama-swap forwarded to beellama/gemma-96k, another cmd model; swapper could not swap while shim held the slot (health 200, completions hung 8s -> 502). Fixed as native llama-swap alias; alias-shim v3.1 hardened (split connect/read timeouts, loud 502s, no-shim-targeting-cmd-models rule). (2) small/medium/code/long: round-1 'undefined vars' diagnosis was WRONG -- macros defined, gguf on disk, routes 200; real fault was aliases were worktree-only WIP wiped by an unrelated 06:26 MDT config rewrite -> now committed; dead beellama-fast dup removed. (3) Kimi exhaustion: NO free Kimi completes -- OpenRouter removed :free Kimi IDs (404), HF monthly credits depleted (402), Moonshot 429 billing-suspended (key valid), NIM 410 gone, Pollinations 404, no local weights (1T MoE cannot fit 24GB); kimi/kimi-k2/kimi-code/kimi-auto fail loudly with genuine upstream status; kimi-auto-shim :25153 TOML-vs-snapshot drift reconciled to the free-Kimi chain. MOONSHOT STOOD DOWN 2026-09-21 (eclipse, Chris: no top-up, ever): chat completions -> exceeded_current_quota_error (suspended, insufficient balance; key itself valid, /v1/models 200). Peer parked in herd.yaml; kimi route names re-pointed at the free-Kimi chain. | modelmap-round2 (Ember's crew) | DONE (2026-09-21) -- sovereign-projects `bff26f8931` (judge deadlock fix + alias-shim v3.1) + `35ca8d4855` (tier aliases committed); proofs: judge 10/10 + 3/3 post-restart 200s with exact content, tiers 4/4 200s real completions post-restart, kimi 4/4 loud 402/404/429; herd + kimi-auto-shim restarted via bin/pitchfork-restart; remote refs ls-remote verified |
| eclipse | Moonshot peer stand-down (Chris: no top-up, ever) + kimi route-name re-point to the free-Kimi chain | eclipse (Ember's crew) | DONE (2026-09-21) -- sovereign-projects 3ba9019af2 (herd.yaml moonshot peer parked, kimi route names re-pointed, KB money-ask corrected; ls-remote verified); live: herd :25100 hot-reloaded (PID 902868, no restart), moonshot/* gone from /v1/models, oracle-judge-a -> nex-n2.5-mini:free exact ROUTE_OK, kimi-k2 loud genuine 402 |
| 1m-prober | Long-context engagement probe (oracle verdict 12097, mission 4e621a18): needle-in-haystack retrieval at 100k/500k/1M tokens through the nvidia keyed lane (nemotron-3-super-120b-a12b, nemotron-3-nano-omni-30b-a3b-reasoning) and the openrouter :free nemotron ID; results recorded in ast_matrix.db requests (strategy=longctx-probe); probe script tools/sovereign-router/probes/long-context-probe.py | 1m-prober (Ember crew, worker under coordinator 4e621a18) | DONE (2026-09-21) -- sovereign-projects 49c17bb9fd (probe script + 13 run JSONs + RESULTS-2026-09-21.md; keyed nvidia nemotron-3-super-120b-a12b 1M needle retrieval PASSED accurate 41.4s; openrouter :free capped 262144 tokens verified; lane flapped 503 ~40min mid-probe) |
| splice | MCP drift merge: canonical superset of awrawr_mcp.py (mcp-smith 318-line additions preserved + canonical spawn-env fix) | splice (Ember pack) | DONE (2026-09-21) -- sovereign-projects dcdcdba90b (ls-remote verified); deployed /home/toxic/awrawr_mcp.py byte-verified; daemon restarted via owned sequence; :25198 /mcp live, 29 tools incl. 7 mcp-smith additions; big catch: supervisor had been running the stale repo copy from the dirty checkout, mcp-smith deployment was never live -- run line repointed to /home/toxic/awrawr_mcp.py |

| oracle-repair | oracle E2E defect repair | oracle-repair | DONE (2026-09-21): lifecycle repair live-verified E2E (intake->signed task->bids->vickrey assign->real super-ralph->signed result->settlement verified->next_work). Commits ad2ade8077 + e25b2e6b25 on nim-probe-20260920, pushed to toxicwind/sovereign-projects. |


| itvx-merge-7dee | merge itvx-browserless into browserless-mcp, move to sovereign mesh | itvx-merge-7dee | DONE (2026-09-21): unified projects/mesh/browserless (browserless-mcp 1.1.0 + itvx native launcher); daemon itvx-browserless on :25130 restarted via owned sequence, auth gate 401/200 verified, live /content fetch + MCP handshake (15 tools) proven. Commits 9bab2b8a95 + 4b8421b719 on toxicwind/sovereign-projects main (ls-remote verified). |


| volt | zswap/nvidia-persistenced/hardware health on yote | parent-orchestrator | DONE (2026-09-21) — lane-2-complete-no-repo-changes |


| cookie-ferry | firefox-to-chromium login migration | ember | RUNNING (2026-09-21) |


| forge-union | unify github search tooling | forge-union | RUNNING (2026-09-21) |
| ts-migration (Forge) | Production Python daemons -> Bun/TS maximal + monorepo (bun workspaces + turbo.json). Tier 0: keypool, model-guard, squawk-ws, awrawr-mcp. Tier 1: exporter, stash-guard, buildsrv. Python stays only for ML/torch glue + throwaway probes | Forge (Ember's pack, ts-migration lane) | PHASE 1 DONE (2026-09-21): workspaces+turbo+scaffold on main 7a61ad6be9; template binary proven (health 200, fail-fast). Phase 2 (Tier 0 rewrites) next; BROWSER-ISOLATION DONE 2026-09-21: agent-display (Xvnc :99) + agent-viewer (noVNC :6080) live, keeper on DISPLAY=:99, c776f7cd25 — Forge joined pack 2026-09-21, chat forge-ts-migration |


| secretsmith | secrets project: fork Secret Service tooling, maximalize into mesh project | ember | DONE (2026-09-21) — 1005ab333f |


| sweep-runner-9c | first-class commit sweep | ember | RUNNING (2026-09-21) |


| secretsmith-promoter | first-class repo promotion for secretsmith | secretsmith-promoter | RUNNING (2026-09-21) |
| ws-fallback | /home/toxic/awrawr_ws_exec.py stale-8379 fallback re-sync: byte-for-byte with canonical 25204 blob (a67a919b) | ws-fallback (Ember's crew) | DONE (2026-09-21) -- re-synced to canonical blob a67a919b (port default 25204), stale backup .bak-20260921-wsfallback; daemon pid 1799513 untouched, :25204/:25147/:25135 live |
| end4-corrective | sovereign-end4 system-tuning corrective commit: true zero-byte udev mask, corrected Btrfs attribution (911 exclusive bytes never measured), rewritten apply-system-tuning.sh (STAGING_ROOT isolated mode, install -m 644, service reconciliation), installer staging test (18/18 on yote), btrfs-status.sh health+guard tool, audit.py v3 (vmstat/buddyinfo/Btrfs/thermals) | Ember | DONE (2026-09-21) -- commit fedb26a0da (on top of toxic's 9e904729): 9 paths under system-tuning/, 3 executables 100755; mask blob verified 0 bytes; sysctl blob sha256 matches live /etc/sysctl.d/99-zswap-vm.conf; installer test 18/18 pass on yote; audit v3 smoke OK (unallocated_bytes=6443552768, 27 vmstat, 6 thermals); btrfs-status live report exit 0 via passwordless sudo (snapperd wedge timeout-guarded) |
| router-proof | head-to-head router benchmark: sovereign-router :25104 (sovereign/free) vs dumb direct :25100 (pinned north-mini-code:free); 180 requests + 60 judge calls, EXACT/QUALITY/CODE prompt types; verdict: intelligent router wins on availability 3.4-6.3x via failover under dead keypool (75x 502 on dumb route); raw data projects/openrouter-probe/router-proof-20260921.json; doc ROUTER_PROOF.md on nim-probe-20260920 @ 8d7f3d24 | Ember (Ember's crew) | DONE (2026-09-21) |
| benchlink | router benchmark inventory + bench-based wiring: bench-priors.json generator (GuideLLM v3 quality + MODEL-MAX liveness/latency + router-proof availability signal) feeding sovereign-router Elo prior seeding; hot-reload via /admin/reload + SIGHUP (untouched providers keep live-learned Elo); live outcomes keep updating Elo | benchlink (Ember's crew) | DONE (2026-09-21) -- commit da8fd5ed7a: gen-bench-priors.py + bench-priors.json (openrouter 1078, llama-swap 1025, rest 1000 unbenched), router_matrix.ts Elo prior seeding + hot-reload-safe applyBenchPriors, router.ts /admin/reload+SIGHUP hook; 20/20 bun tests pass; deployed to :25104 via owned restart, /status shows priors, /admin/reload verified live |
| elo-persist | durable Elo persistence for sovereign-router: elo_state table in HealthDB + write-through setElo() so live-learned Elo survives daemon restarts; bench priors remain fallback only; restore-on-startup, hot-reload-safe, fail-open on corrupt DB | elo-persist, Ember crew | DONE (2026-09-21; corrective 1af9d6cd on origin/main: map-only prior seeding (fallback priors never create elo_state rows), persistedEloProviders set (hot-reload immune incl. equality edge), fail-open on corrupt DB; restart-verified live 2x 2026-09-21, /admin/reload no-clobber, live traffic write-through matched DB; tests 29/29 green) |
| squawk-feed-perf | Squawk feed + UI perf & hot-reload | Ember's crew (squawk lane) | DONE (2026-09-21) -- sovereign-projects 8a9293184b: tail=N snapshots (UI boots in 1 request), numeric seq order, channel param honored, ghost-record cursor fix, tolerant frontmatter; tests 9+9 OK; live deploy verified (tail 8ms, park-wake 4ms, no-store UI) |
| wiring-audit | Estate-wide READ-ONLY audit of every canonical inference caller: current route/model string, config-vs-hardcoded, owner, rewire action (all deferred until Sovereign-vs-TAU bake-off verdict) | wiring-audit (Ember's crew) | DONE (2026-09-21) -- sovereign-projects 716b5ff50119d33faf22f5609f37e036028d7ce7: projects/routing/docs/inference-caller-audit.md -- 59 live callers, 21 hardcoded (10 live-affecting), 9 already on sovereign/free |
| tau-routing-benchmark | Fair head-to-head: Sovereign router :25104 (sovereign/free) vs TAU/oh-my-pi's actual routing extension (canonical copy mapped with ffs); benchmark suites: coding, reasoning, long-context recall, cross-chunk synthesis, contradiction handling, provenance correctness; controlled failures: broken primary, empty HTTP 200, HTTP 429, slow provider, recovery after quarantine. Build automatic effective-1M-context composite route (query-aware partitioning, parallel map via :25104, hierarchical tree reduction, per-chunk provenance, native long-context bypass); reuse LLMxMapReduce/ExtAgents/ToM patterns. Wire proven canonical route into TAU, Kimi Code, and every canonical inference caller; merge Kimi Code rewiring to canonical main | Tally (Ember's crew) | RUNNING (2026-09-21) -- fleet-lock tau-routing-benchmark held by tally-sidechat |

| nvidia-openfang-browserless | NVIDIA-first embeddings for OpenFang (real nvapi key via authenticated NGC UI, Mistral fallback until proven) + persistent Browserless keeper: event-driven visible Chromium, first-class browserless-mcp tools, Quickshell float toggle button | Sable (Ember's crew) | RUNNING (2026-09-21) |

| cinder | Lane-sweep / deconfliction (side chat cinder-lane-sweep): estate sweeps, dupe flags, stall watch; owned the NVIDIA docs-mirror lane (worker 91dcc7e0) to verified completion. Posts as Cinder -- ash-fox fursona, quick and dry, the pack lookout. | Cinder (Ember's crew) | DONE (2026-09-21) -- NVIDIA API docs mirror complete: 6 sections, ~4500 HTML pages, ~2.6GB under nvidia-api/ in private repo toxicwind/hatch-docs; origin/main 11e730158453bf0c2091ce05a19587af8ea502fc (5 commits, fetch-first, no force-push; remote ref + tree verified by Cinder 2026-09-21: 7635 entries, 6 index-READMEs; counts api-reference 1480pp, nim 2764pp, nvcf 277html+273md, ngc 27pp, ngc-cli 14pp, nvcf-github 423md); 62 NIM JSON assets recovered after cleanup misfire, JSON-validity-checked; 11 ReadMe login-wall pages excluded (login required) |

| kimi-merge | Kimi Code sovereign-router rewiring merged onto canonical main: bin/kimi-code-setup default route herd/qwen-flash -> sovereign/free (:25104), [providers.sovereign] + [models."sovereign/free"], herd models kept as selectable fallbacks; live probe switched to SOVEREIGN_ROUTER_OK semantics. Cherry-picked from origin/nim-probe-20260920:56f85dbf60 (message preserved, history kept); herd-keypool.py racing + ROUTER_PROOF.md verified byte-identical to main already -- no duplication. Temp worktree merge; shared-tree dirty WIP untouched | kimi-merge (Ember's crew) | DONE (2026-09-21) -- merge commit 6bbdf1019f on origin/main (ls-remote verified); config live: default_model=sovereign/free, [providers.sovereign] :25104, herd fallbacks; kimi doctor OK; :25126 200; live completion via :25104 OK (2026-09-21 ~19:58 UTC): sovereign/free returned exact SOVEREIGN_ROUTER_OK, served by local EXAONE-4.0-1.2B failover through the merged default route; kimi doctor OK, :25126 200, config live default_model=sovereign/free |
| tau-router-recon | TAU/oh-my-pi routing-extension recon: canonical omp-model-router vs stale/dead duplicates, model-selection logic with exact file/line refs, exact benchmark invocation vs Sovereign Router :25104 model sovereign/free | tau-router-recon (Ember's crew) | DONE (2026-09-21) -- doc projects/tau/docs/router-extension-map.md; 9c2ecf0b0e |
| lumen | Squawk feed UI readability: keeper-driven visual audit (CDP :9223) of /squawk-feed/ui at desktop 1440x900 + mobile 390x844; root-caused empty bodies (pre-HMAC msgs fail verify_on_read -> body withheld); fix = serve bodies flagged unverified + card-layout redesign | Lumen (Ember's crew) | DONE (2026-09-21) -- relay fix e5fdce9c95 (serve pre-HMAC plaintext flagged invalid, fail-closed on ciphertext; 12/12 feed tests OK), UI redesign cb6bd69f82 (cards, unverified badges, scroll-to-bottom, mobile, favicon); keeper-verified 1440x900 + 390x844, 0 console/page errors; deployed live :25135  markdown render + full bodies 0b33559ad2 (truncate dropped, escape-first md renderer, keeper-verified live) |


| rivet | fix stale kimi-code-setup writer drift trap | rivet (Ember's crew) | DONE (2026-09-21) — fixed writer verified on origin/main 6bbdf1019f (default_model=sovereign/free, [providers.sovereign] :25104, herd fallbacks); on-disk /home/toxic/sovereign/bin/kimi-code-setup synced to main blob (md5 1fe03699e416e4cd65fd443f5d436a66, staged, dirty WIP untouched); writer test vs live config: identical except runtime Moonshot key; kimi doctor OK on generated config; live ~/.kimi-code/config.toml never touched (md5 13962db0b6375316fdc2e09d65bc71ef); probe hit transient upstream 429s (free-pool rate limit, same class kimi-merge saw) |

| auto1m | Effective-1M-context composite route implementation (Ember crew): sentence-aware chunking + query-term ranking + parallel map extraction + ExtAgents-style fact scoring + tree-collapse reduction, per-chunk provenance with fail-closed citation validation, env-overridable router/model (AUTO1M_ROUTER/AUTO1M_MODEL/AUTO1M_DIRECT_MODEL), source-aware multi-file input; pure-function unit tests 30/30 (no router); full ~740k-token proof test with grep-verified needles + test-evidence.json. Complementary to Tally's tau-routing-benchmark (which benchmarks routing; this lane builds the composite consumer). Code: projects/auto1m/ | auto1m-builder (Ember's crew) | RUNNING (2026-09-21) -- code commit e44739ac3b on origin/main; full proof green pending a capable worker (sovereign :25104 serving sovereign/free via local EXAONE-4.0-1.2B only; strong-worker watcher armed) |

Retired/completed crews stay listed here with status DONE and their final commit SHAs — history is how we avoid redoing work.
## 3. Repo index (canonical remotes)

| Repo | Canonical remote | Notes |
|---|---|---|
| sovereign-projects | `toxicwind/sovereign-projects` (branch `main`) | **THE canonical repo.** `/home/toxic/sovereign` worktree. NEVER push to the stale `toxicwind/sovereign` trap. |
| guidellm | `toxicwind/guidellm` (fork of `vllm-project/guidellm`) | Benchmark harness fork |
| mcpproxy-go | `toxicwind/mcpproxy-go` (fork of `smart-mcp-proxy/mcpproxy-go`) | MCP proxy fork |
| hatch-docs | `toxicwind/hatch-docs` (private) | Runtime/credential docs |
| sovereign-end4 | `toxicwind/sovereign-end4` (branch `main`) | yote system-tuning: udev/sysctl/systemd/Btrfs/limine kernel profiles |
| browserless-mcp-audit | Browserless MCP 1.3.0 audit: 4 integration bugs fixed | browserless-audit-crew | DONE 2026-09-21 commit c1c544eb1f |

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
15. **Oracle stands in for Chris's approvals (Chris 2026-09-21).** Everyone works together autonomously: coordinate through squawk, decide through the oracle. When an agent needs Chris's approval, it frames the decision as a dated yes/no oracle question with evidence and treats the verdict as his approval — no waiting on Chris for approval-shaped decisions. Hard boundary: money and credentials stay Chris's alone; the oracle cannot approve spending, top-ups, credential minting/rotation, or anything credential-shaped.
16. **Anchored furry personas (Chris 2026-09-21).** Every agent takes its own furry persona — name, species, personality, a real character — but the persona must be ANCHORED: lane + concrete task in plain words ("Korra the snow-leopard — squawk lane, making the feed hot-reload" is a persona; "the readability relay... loudly held opinions about line-height" is generic fluff and gets rewritten as the job). Ember is the main agent's alone — no other instance uses it. Chats are living status titles: `[Your Name]: [current status]` (e.g. `Korra: making the feed hot-reload`), updated as the work moves — a stale title lies. Fleet announce format: `agent joined: <name> — <lane>/<task> (Ember's crew)`. First-class paste block: `skills/fleet-spawn/join-prompt.md`.
17. **Cell workspace = tmp (Chris 2026-09-21).** The hatch cell workspace is transient scratch — everything on it is disposable. ALL durable files live ON THE BRIDGE (yote), inside your persona. Nothing is lost, ever: anything worth creating is worth committing — land real files in the right repo, commit, push to canonical main.

**Oracle-as-approval procedure (how to actually file one):**
1. Frame as a dated yes/no question: `"Will <concrete outcome> by <YYYY-MM-DD>?"` For go/no-go, phrase so YES = proceed.
2. Evidence = JSON array of **dicts** `[{"id":"...","text":"...","relevance":0.0-1.0}]` — bare strings 500 the engine.
3. Ask: `bin/oracle_ask.py "<question>" --evidence evidence.json --json` (oracle-market), or `POST 127.0.0.1:25151/ask`.
4. Read `status` in the verdict: a firm YES/NO (probability past the gate) **is** Chris's approval — final, act immediately, don't re-ask, don't wait. `status: escalate` means the oracle abstained (fail-closed); that is the ONE case that goes to Chris directly (HUMAN step of the escalation ladder).
5. Log the verdict in the market ledger as an `oracle-approval` event: `{question, verdict, probability, evidence_ids, agent, ts}`.
6. NEVER route money/credential decisions here — spending, top-ups, credential minting/rotation go to Chris directly, no exceptions. The oracle cannot mint approvals for those.
Full protocol: `agents/oracle-market/SPEC.md` § oracle-as-approval.

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
- Daemon-rebuild drift note 2026-09-20: `hatch/audit-jarvis/daemon-rebuild-drift-2026-09-20.md` (compaction subsystem unchanged in hatch `82d6744eed2`; new `tool_dispatch_heartbeat`)
- Runtime/credential docs: https://github.com/toxicwind/hatch-docs/blob/main/runtime/credential-broker.md

---

## 6. Required-reading protocol (for coordinators)

Every spawn brief MUST be generated from `docs/spawn-brief-template.md` and MUST include:
1. A pointer to this file (path above / GitHub link) and to the spawn-brief template.
2. "Register your crew in §2 Active Crews when you start; mark DONE with final commit SHAs when you finish."
3. "Check `squawk read fleet` + §2 before touching any tree another crew owns."

Staleness is a bug: if you find this file wrong, fix it and push — same commit rules as §3.

---

## WS2 declared-vs-runtime contract (ferrous-warden, 2026-09-20)

**Declared** (intent -- deploy/manifest.yaml + pitchfork.toml + configs): changes only via
commits or content-hash-gated deploy scripts. A daemon or agent rewriting declared state by
hand is DRIFT, not an edit.

**Runtime** (fact -- process table, /proc/*/exe, paths under runtime_paths in the
manifest): the reconciler reads it, never converges toward it. Daemons write under
runtime_paths freely; those paths are EXEMPT from drift detection by construction.

**Machinery** (nim-probe-20260920, ferrous-warden):
- deploy/manifest.yaml -- pins every deployed binary (path, sha256, immutable copy,
  source repo + commit). Currently: herd (llama-swap 9305f95663db..), herd-keypool,
  herd-model-guard, openfang-kernel (check-only, local debug build).
- bin/estate-reconcile -- event-driven reconciler (chezmoi status/apply concept,
  qb-manager atomic-deploy mechanics): check (read-only, exit 1 on drift),
  --apply (atomic tmp+rename restore from immutable copy or SIGNED git HEAD --
  unsigned HEAD alerts only, never restores), watch (inotify on build/bin dirs,
  circuit breaker at 5 restores/60min, never a timer), proc-audit (declared vs
  /proc exe, handles interpreted daemons via cmdline script path).
- Configs are REPORT-ONLY in WS2 (shared tree holds ~198 dirty files from other
  crews -- auto-restoring from git would nuke live WIP). Signed-HEAD config
  converge is future work.
- ops/openfang-sqlite-check.sh -- runs on OpenFang boot (hooked into
  ops/openfang-run.sh): PRAGMA integrity_check + non-empty + >=1 table +
  schema-version record; bounded snapshots (keep 5) into ~/.openfang/backups/
  on every healthy boot; self-heals from the newest backup atomically on
  corruption; refuses boot only when corrupt AND no usable backup. Live
  2026-09-20: ~/.openfang/openfang.db was 0 bytes -- the exact silent-data-loss
  case this catches.

## 7. Build server = buildsrv (2026-09-21)

buildsrv IS the fleet build server -- a literal build daemon on yote, not a
concept. Canonical source: tools/buildsrv/ in this repo. Service:
127.0.0.1:25148 (pitchfork daemons: buildsrv, buildsrv-watchdog).

Lifecycle: queue JSON -> active JSON -> results JSON under
/home/toxic/buildsrv/. Successful identical specs short-circuit as CACHED,
keyed by content hash. Forward-only: buildsrv never checks out, stashes, or
reverts repos. Jobs run via bash -lc and inherit the daemon environment.

Access:
- Yote CLI: /home/toxic/bin/buildsrv (submit/status/logs/list/health)
- Hatch proxy: hatch/bin/buildsrv proxies safely through yote-conn exec
  (shlex.join quoting, never raw concatenation)
- MCP (awrawr-mcp :25198): buildsrv_submit, buildsrv_status, buildsrv_logs,
  buildsrv_list, buildsrv_health (argv lists only, job IDs validated,
  submit returns immediately after queueing)

Cache environment (pitchfork.toml daemons.buildsrv env):
- RUSTC_WRAPPER=sccache, SCCACHE_DIR=/home/toxic/.cache/sccache (10 GiB)
- CCACHE_DIR=/home/toxic/.cache/ccache (10 GiB)
- CMAKE_C_COMPILER_LAUNCHER=ccache, CMAKE_CXX_COMPILER_LAUNCHER=ccache
- UV_CACHE_DIR=/home/toxic/.cache/uv (NVMe)
- CARGO_INCREMENTAL=0 -- REQUIRED: sccache refuses incremental compilation
- Canonical home configs: projects/yote/host/home/.cargo/config.toml and
  home/.config/ccache/ccache.conf (installed by apply.sh)

Caveats:
- CC/CXX NOT set in daemon env: BASH_ENV rewrites them to clang for bash -lc
  jobs. CMAKE compiler launchers are the robust ccache path.
- Bun cache at /home/toxic/.bun/install/cache (4.4G, verified 2026-09-21).
- Binary-only Rust crates are non-cacheable by sccache (crate-type rule).

Why workers = 2: yote has 16 logical CPUs / 62 GB RAM / NVMe, but two Cargo
builds already oversubscribe it. Keep BUILDSRV_WORKERS=2.

Observability: sovereign-exporter (:25213) exposes sovereign_buildsrv_up,
sovereign_buildsrv_queue_depth, sovereign_buildsrv_active_jobs; Grafana
workflows.json has a buildsrv row.

New-toolchain rule: persistent config in projects/yote/host/home/, daemon
env in pitchfork.toml, then a REAL buildsrv compile with nonzero cache-hit
proof. Proven 2026-09-21: 2 hits, 50 percent hit rate on a real job.
