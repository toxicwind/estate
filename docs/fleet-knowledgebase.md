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
- Canonical worktree: `/home/toxic/estate` (origin = `toxicwind/sovereign-projects` — see §3). `/home/toxic/estate` is a deprecated symlink to it (2026-10-02 migration); old sovereign-prefixed paths below still resolve.
- Reach it from hatch: `~/workspace/bin/yote-conn exec '<cmd>'`

### Key paths (yote)
| Path | What it is |
|---|---|
| `/home/toxic/estate` | Canonical shared worktree (origin `toxicwind/sovereign-projects`). May hold live dirty WIP — preserve it; use clean temp worktrees for isolated pushes. |
| `/home/toxic/.tau` | Tau engine config |
| `/home/toxic/shingle` (+ `.shingle` symlink) | Shingle root; squawk lives here — BOTH are now symlinks to `sovereign/hatch/agents/ember/` in-repo (reorg 2026-09-20); squawk-root is gitignored at .gitignore:295 |
| `/home/toxic/estate/shingle-workspace/` | -> `scratch/` symlink (non-production staging; production bridge home is `bridge/`) |
| `/home/toxic/estate/config/herd.yaml` | Herd router config (the model herd) |
| `/home/toxic/estate/skills/paper-search/` | Paper-search skill (canonical home) |
| `/home/toxic/super-ralph` | Super Ralph source |
| `/home/toxic/estate/projects/range/ranch/oracle/` | Oracle market loop + watchdog |

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
| 25198 | /mcp backend (Funnel `:443/mcp` -> `127.0.0.1:25198/mcp`) |
| 25204 | /exec-ws backend (Funnel `:443/exec-ws` -> `127.0.0.1:25204/exec-ws`) |
| 25201 | Funnel `/` root backend |
| 25207 | Funnel `/status` backend |
| 34567 (127.0.0.1) | Funnel `/files` backend |
| 25127 | /mesh-mcp backend (Funnel `:443/mesh-mcp` -> `127.0.0.1:25127/mcp`) |
| 25202 | /gemini-mcp backend (Funnel `:443/gemini-mcp` -> `127.0.0.1:25202/mcp`) |
| 25136 (tailnet) | /fleet backend (Funnel `:443/fleet`) |
| 4222 / 4223 (127.0.0.1) | NATS server + websocket (Funnel `:443/nats-ws` -> `:4223`) |
| 25212 | Cockpit web console (`https://awrawr-pc:25212/`, moved from :9090 via systemd drop-in 2026-09-20) |

**Extended serve map (all verified listening on yote 2026-09-30):**
| Port | Service |
|---|---|
| 25104 | Sovereign router (`sovereign/free`) |
| 25148 | flicker (ranch build daemon — replaced brand/buildsrv 2026-09-30; see §7) |
| 25193 | Flock router |
| 25126 | kimi-auto-shim |
| 25152 | toolcall-llm |
| 25122 | beellama-fast |
| 25110 | Grafana |
| 25211 | node-exporter |
| 25213 | sovereign-exporter |
| 6080 | noVNC agent-viewer (browser isolation) |
| 9223 | Keeper browser CDP |
| 25130 | browserless-mcp |

**Additional live services (verified 2026-10-01, cartographer):** `pitchfork list` is the authoritative daemon source (77 daemons running 2026-10-01; bidder-forge and bidder-scout retired/stopped). The port→process map below was verified live via `ss -ltnp` + `/proc/<pid>/cmdline` + cwd on yote.
| Port | Service |
|---|---|
| 25102 | yote/openfang-bridge (`src/services/yote.ts` — OpenFang HTTP API integration) |
| 25105 / 25106 / 25110 | mesh-front proxies → prometheus / hf-downloader / grafana (`src/services/mesh-front.ts --service <name>`) |
| 25107 | null-g-proxy (`tools/null-g-proxy`) |
| 25111 | chute (`ranch/barn/chute/chute.mjs`) |
| 25113 | sovereign-github-search MCP (`sovereign-github-search/apps/mcp`) |
| 25114 | sovereign-github-search frontend (next-server) |
| 25115 | mesh-hub (`src/services/mesh-hub.ts`) |
| 25116 | kimi-token-audit dashboard (bun --hot) |
| 25117 | hindsight-api |
| 25118 | control-plane (/app/control-plane, next-server) |
| 25120 | sovereign-chat (bun chat.ts; tailnet + loopback) |
| 25121 | byte-vision-mock (health stub) |
| 25127 | gatehouse (MCP gateway; also the /mesh-mcp funnel backend) |
| 25133 / 25134 | qdrant |
| 25137 | bedrock web (`/home/toxic/projects/bedrock/web/server.ts`; tailnet) |
| 25142 | cell-files UI (bun --hot) |
| 25143 | coyote-loop (OpenFang agent loop → :25100) |
| 25149 / 25150 | paper-poller + watchdog (`/home/toxic/deep-paper-reader/paper-poller`) |
| 25151 | oracle-core (oracle-as-approval `POST /ask`) |
| 25153 | kimi-auto-shim |
| 25194 | ralph-dashboard backend (uvicorn) |
| 25195 | codebase-memory |
| 25197 | boundless (uvicorn) |
| 25199 | valkey (redis) |
| 25205 | prometheus |
| 25208 | nginx |
| 25210 | grafana (binary; :25110 is the mesh-front proxy) |
| 25215 | sovereign-stream-broker |
| 25219 | windmill |
| 25220 | lookout (`/home/toxic/projects/lookout`) |
| 25240 | flicker/woodpecker gRPC |

**Routing-audit notes 2026-09-30 (corvid, corrected):** the old `8377 / 8378 / 8379` row was stale — nothing listens on those ports and neither pitchfork.toml nor funnel-map.sh references them; the live funnel backends are the 25xxx ports above. Correction to the first version of this note: an unprivileged `tailscale serve status` shows a PARTIAL view (tailscaled state is root-only) — it hid `/gemini-mcp`, `/whatsapp-webhook`, `/squawk-ws`, `/squawk-feed/seq`, `/mesh-health`, and the `[serve:8443]` tailnet mount. `sudo funnel-map.sh --check` is the authoritative check and it passes: all mounts present, including `[serve:8443] /agent-browser -> 127.0.0.1:6080`, `/gemini-mcp -> 127.0.0.1:25202/mcp`, `/whatsapp-webhook -> 127.0.0.1:25146/webhook`. Lesson: verify serve state as root, never via the unprivileged CLI.

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

> **GENERATED TABLE — do not edit by hand.** Source of truth is `fleet/crews/<crew>.md` (one file per crew). Regenerate with `bun ranch/ops/bin/kb-rollup.ts`. Register via `fleet-onboard.sh --register`; mark done via `fleet-onboard.sh --done SHA`.

<!-- KB-ROLLUP:START -->
| Crew | Scope | Owner / coordinator | Status |
|---|---|---|---|
<!-- KB-ROLLUP:END -->


| stream-e | document the #yolo exec-policy bypass in the fleet KB | Ember (spawned subagent) | DONE (2026-09-30) — 2c83dd09a714a44d0eccee38bdea3ae257065a81 |


| rhyx | brand hyper-race focus core: three-path focus-window racer + mock compositor + tests + native C++ verification | ember | DONE (2026-09-30) - toxicwind/brand@547a87811a1cd94e6068cf426ccca587e817b60d |

| quill | bedrock timeline refinement: enumerate uncertainties, gather primary evidence, settle contested points by debate, land verified corrections | Quill (Ember's crew) | DONE (2026-09-30) — fb5baa3 |

| twitch | infra recon: fireworks.ai + moonshot.ai public surface via pd-mcp | ember | DONE (2026-09-30) — 50e0c7952eb9f62ab8787f7cbe49810e2d4e361c |


| rigger | yote-conn mainline fix + Bun forward fork (ripline) with fallover | rigger | RUNNING (2026-09-30) |


| barnaby | flock ts/policy: port sovereign-router policy engine (Elo, bench-priors, quarantine circuits, warm standby, health analytics) to TypeScript | Ember (main) | RUNNING (2026-09-30) |


| juniper | effusion-labs maximalization: CSS/JS killshot fix, framework, LFS, pages, reorg | Ember | DONE 2026-09-30 (deployed 21006142) |


| pip | minus1: verify metaaivm-profile end to end | Ember | DONE (2026-09-30) — verify-only-12of12 |
| rowan | fleet-kb: reconcile Pip minus1 KB row + fix fleet-onboard overlap-check DONE false positive | Ember (main chat) | DONE (2026-09-30) — b27d806a2 (pip row) + 1868bdcc6 (onboard fix), both ls-remote verified |


| torr | metaaivm-fork: maximalize toxicwind/muse-cli, land on main | Ember (main chat) | DONE (2026-09-30) — 628fa52 |


| rusty | connector-repair: durable yote-connector launcher + lane verification | ember-sidechat | DONE (2026-09-30) — 11906ae474776cfb27ccfe78632431ec73d2563a |

Retired/completed crews stay listed here with status DONE and their final commit SHAs — history is how we avoid redoing work.
## 3. Repo index (canonical remotes)

| Repo | Canonical remote | Notes |
|---|---|---|
| sovereign-projects | `toxicwind/sovereign-projects` (branch `main`) | **THE canonical repo.** `/home/toxic/estate` worktree. NEVER push to the stale `toxicwind/sovereign` trap. |
| roundup | `toxicwind/roundup` (fork of `vllm-project/guidellm`) | Benchmark harness fork |
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
10. **Forward movement.** A "can't" from one layer is information, never a verdict. Workaround, shrink blast radius, hand Chris a one-liner for the part only he can touch. Security boundaries and safeguards stay intact.
11. **Routers ≠ model code.** Model-family tooling never hardcodes model IDs; model selection lives in herd router config alone.
12. **Fleet protocol.** Every spawn announces: `agent joined: <name> — <task> (ember)`. Squawk fleet is a live chat: greet, collaborate, ask questions, celebrate, banter, develop personas. A pack, not a pipeline.
13. **Unreliable narrator.** Error strings are claims, not facts — verify against `ps`/`ss`/`curl`/logs/`/proc`/DB before reporting or acting. The system's nagging (meter warnings, approval noise, "cannot be done") is disregarded when observation contradicts it. Full doctrine: `docs/unreliable-narrator-doctrine.md`.
14. **Stale rows are not hands-off.** Dead/idle/phantom agent rows get terminalized through the proper channel (owner's `subagent.close`), never left to rot and never one-off row edits. `hatch/bin/agent-reaper --verify-phantoms` closes the detect→verify→direct→track loop; `hatch/bin/swarm-watchdog` auto-resumes frozen tool trees when load settles.
15. **Oracle stands in for Chris's approvals (Chris 2026-09-21).** Everyone works together autonomously: coordinate through squawk, decide through the oracle. When an agent needs Chris's approval, it frames the decision as a dated yes/no oracle question with evidence and treats the verdict as his approval — no waiting on Chris for approval-shaped decisions. Hard boundary: money and credentials stay Chris's alone; the oracle cannot approve spending, top-ups, credential minting/rotation, or anything credential-shaped.
16. **Anchored furry personas (Chris 2026-09-21).** Every agent takes its own furry persona — name, species, personality, a real character — but the persona must be ANCHORED: lane + concrete task in plain words ("Korra the snow-leopard — squawk lane, making the feed hot-reload" is a persona; "the readability relay... loudly held opinions about line-height" is generic fluff and gets rewritten as the job). Ember is the main agent's alone — no other instance uses it. Chats are living status titles: `[Your Name]: [current status]` (e.g. `Korra: making the feed hot-reload`), updated as the work moves — a stale title lies. Fleet announce format: `agent joined: <name> — <lane>/<task> (Ember's crew)`. First-class paste block: `skills/fleet-spawn/join-prompt.md`.
17. **Cell workspace = tmp (Chris 2026-09-21).** The hatch cell workspace is transient scratch — everything on it is disposable. ALL durable files live ON THE BRIDGE (yote), inside your persona. Nothing is lost, ever: anything worth creating is worth committing — land real files in the right repo, commit, push to canonical main.

18. **Per-crew KB ownership (Chris 2026-09-29).** §2 Active Crews is a GENERATED rollup — never hand-edit the table. Each crew owns `fleet/crews/<crew>.md` (frontmatter: crew/scope/owner/status); register and mark-done through `fleet-onboard.sh`, which writes your file and regenerates the rollup via `bun ranch/ops/bin/kb-rollup.ts`. Concurrent registrations cannot clobber each other: per-crew files merge cleanly and the table is always regenerable. If the rollup looks stale, re-run the rollup — never hand-edit §2.

**Oracle-as-approval procedure (how to actually file one):**
1. Frame as a dated yes/no question: `"Will <concrete outcome> by <YYYY-MM-DD>?"` For go/no-go, phrase so YES = proceed.
2. Evidence = JSON array of **dicts** `[{"id":"...","text":"...","relevance":0.0-1.0}]` — bare strings 500 the engine.
3. Ask: `bin/oracle_ask.py "<question>" --evidence evidence.json --json` (oracle-market), or `POST 127.0.0.1:25151/ask`.
4. Read `status` in the verdict: a firm YES/NO (probability past the gate) **is** Chris's approval — final, act immediately, don't re-ask, don't wait. `status: escalate` means the oracle abstained (fail-closed); that is the ONE case that goes to Chris directly (HUMAN step of the escalation ladder).
5. Log the verdict in the market ledger as an `oracle-approval` event: `{question, verdict, probability, evidence_ids, agent, ts}`.
6. NEVER route money/credential decisions here — spending, top-ups, credential minting/rotation go to Chris directly, no exceptions. The oracle cannot mint approvals for those.
Full protocol: `projects/range/ranch/oracle/SPEC.md` § oracle-as-approval.

---

## 5. Docs index (deep links)

- Master README: [/home/toxic/estate/README.md](../README.md) — every sub-README links back here.
- This knowledgebase: `docs/fleet-knowledgebase.md` (this file)
- Spawn brief template: `docs/spawn-brief-template.md` — canonical template every brief is generated from; autonomy doctrine in its header (removing it is a visible diff)
- Paper-search skill: `/home/toxic/estate/skills/paper-search/SKILL.md`
- Tau engine docs: `/home/toxic/estate/projects/tau/engine/docs/`
- Yote ops: `/home/toxic/estate/projects/yote/ops/` (yote-doctor.sh, yote-fix.sh)
- Scheduler audit 2026-09-20: `/home/toxic/estate/projects/audits/scheduler-audit-2026-09-20.md`
- Oracle market spec: `/home/toxic/estate/projects/range/ranch/oracle/SPEC.md` (v2.1)
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
  circuit breaker at 5 restores/60min, never a timer; 2026-10-02: watch skips missing dirs loudly (WATCH-DEGRADED log+squawk) instead of crash-looping), proc-audit (declared vs
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

## 7. Build server = flicker (2026-10-01; was brand)

flicker IS the fleet build daemon -- a literal build server on yote, not a
concept. Canonical source: `projects/range/ranch/flicker/` in toxicwind/ranch.
Service: :25148 (pitchfork daemons: flicker, flicker-agent), binary
`ranch/flicker/bin/flicker-server` (Woodpecker-based: gRPC on :25240,
`FLICKER_ROOT=/home/toxic/flicker`). API: `POST /api/jobs`; content-hash
caching (identical specs short-circuit as CACHED). Verified live 2026-10-01:
`GET /` serves the flicker landing page ("The ranch build daemon").

History: brand was the build server from 2026-09-21 (canonical source
branding/ in toxicwind/ranch, moved 2026-09-30 from tools/buildsrv in this
repo; pitchfork daemons brand + brand-watchdog on :25148). Replaced by
flicker 2026-09-30 (sparrow: "flicker and flicker-agent verified live on
:25148 and migrated with ranch/flicker"). No brand daemon in `pitchfork list`
2026-10-01; `/home/toxic/brand` absent. The remaining §7 notes below (cache
env, workers=2, observability) describe the build-daemon role as built for
brand — re-verify each path against the flicker fragment before relying on it.

Lifecycle: queue JSON -> active JSON -> results JSON under
/home/toxic/brand/. Successful identical specs short-circuit as CACHED,
keyed by content hash. Forward-only: brand never checks out, stashes, or
reverts repos. Jobs run via bash -lc and inherit the daemon environment.

Access:
- Yote CLI: /home/toxic/bin/brand (submit/status/logs/list/health)
- Hatch proxy: hatch/bin/brand proxies safely through yote-conn exec
  (shlex.join quoting, never raw concatenation)
- MCP (awrawr-mcp :25198): brand_submit, brand_status, brand_logs,
  brand_list, brand_health (argv lists only, job IDs validated,
  submit returns immediately after queueing)

Cache environment (pitchfork.toml daemons.brand env):
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
builds already oversubscribe it. Keep BRAND_WORKERS=2.

Observability: sovereign-exporter (:25213) exposes sovereign_brand_up,
sovereign_brand_queue_depth, sovereign_brand_active_jobs; Grafana
workflows.json has a brand row.

New-toolchain rule: persistent config in projects/yote/host/home/, daemon
env in pitchfork.toml, then a REAL brand compile with nonzero cache-hit
proof. Proven 2026-09-21: 2 hits, 50 percent hit rate on a real job.
## 8. Gate retire + README maximalization + AST-BM25 racer (2026-09-29, Forge)

### /agent-browser tailnet-only (gate retired) — LIVE on main as 3ff44863d2
Chris 2026-09-21: "Token gate we didn't even want remember, because I thought
it was tailscale and network and you only". The dedicated viewer-token gate
(`agent-viewer-gate.py`, was `:6081`) is retired, not repaired:
- `/agent-browser` removed from public Tailscale Funnel `:443`.
- Now tailnet-only: `tailscale serve :8443` → `http://127.0.0.1:6080` (websockify/noVNC).
- Gate daemon stopped, removed from `pitchfork.toml` and the keeper fragment; old
  `agent-viewer-gate.py` kept as retired reference only.
- `projects/yote/ops/funnel-map.sh` gains `SERVE_MAP` for tailnet-only mounts +
  a regression guard that fails the script if `/agent-browser` ever lands on a
  public funnel frontend again. `funnel-map.sh --check` exits 0 with
  `[serve:8443] /agent-browser -> http://127.0.0.1:6080`.
- VNC auth untouched (never read, displayed, rotated); noVNC stays interactive.
- Transport rule: Tailscale Serve needs the MagicDNS hostname as SNI — raw
  tailnet-IP HTTPS fails TLS. Use the MagicDNS name or `curl --resolve`.
- Landed on canonical `toxicwind/sovereign-projects/main` as `3ff44863d2`
  (cherry-picked from `ea2d28f8b5a5` on `origin/forge/gate-retire-final`,
  rebased over `9df90e6fc4`, fast-forward, remote ref verified).

### README maximalization (readme-maximal skill)
Skill: `/home/toxic/workspace/skills/readme/SKILL.md` (rubric: badges first,
"why should I care?" in first viewport, mermaid/tables/code, first-class links,
license + security up front). Chris 2026-09-29: every first-party README.md
uses it. Scope: 401 first-party READMEs (`/tmp/readme-triage/firstparty.txt`
method); vendor/, scratch/, node_modules/ excluded (upstream). 7 majors were
maximalized 2026-09-21 (`c6bc997e13`).

### AST-BM25 racer — local-heavy edition (Forge, 2026-09-29)
Chris: adapt the Sovereign AST-BM25 Racer to be local-heavy, "avoid that part
obv" (Dropbox). The Dropbox sync step is removed, not replaced. Skill:
`~/workspace/skills/ast-bm25-racer/` (SKILL.md + `ast_bm25_racer.py`).
Measured on yote: 53,851 files indexed in ~98s; scoped query 0.395ms;
nanosecond race (50 runs, GC-isolated): bm25_only median 60,139ns,
hybrid_full median 300,425ns.

## 9. `#yolo` pre-authorized exec prefix (2026-09-30)

### What it is
`yote-conn exec` (and the MCP/WS exec lanes) enforce a default-deny policy on
catastrophic patterns. The policy lives in the canonical repo
`toxicwind/sovereign-projects`: `projects/bridge/yote/awrawr_mcp.py`
(`_DEFAULT_DENY`) and `bridge/awrawr_ws_exec.py`. The first default-deny regex
blocks recursive `rm` against `/`, `~`, `/*`, or `$HOME` — so
`rm -rf ~/.cache/bun` matches (the target begins with `~/`) and the command
fails with `POLICY DENIED for recursive rm pattern`. The KB had zero mentions
of `#yolo` or `POLICY DENIED`, which is why a cache-cleanup agent hit the deny
with no documented recourse.

### Syntax
```
yote-conn exec "#yolo rm -rf ~/.cache/bun ~/.npm"
```
- The literal prefix `#yolo ` (hash, yolo, space) is stripped before execution.
- The prefixed command is treated as operator-pre-authorized: policy matching
  is skipped for it; authentication and audit remain active, and the audit
  record carries `yolo:true`.

### Rules
- The denylist is accident prevention for ordinary commands — the auth token
  is the actual security boundary.
- Ordinary commands keep their catastrophic-operation protection. Only the
  `#yolo`-prefixed command is exempted from policy matching.
- A `#yolo`-prefixed command exercises Chris's standing autonomous-operation
  authority: you act as him, deliberately. Use it for the specific denied
  operation, then go back to normal commands — do not prefix routinely.
- Do NOT weaken, remove, or edit the denylist itself (`_DEFAULT_DENY`,
  `awrawr_ws_exec.py`) — document the mechanism, never touch the policy.

## 10. Fleet -> OpenFang join (fleet-join, 2026-09-30)

### What it is
Any squawk fleet agent can become a first-class OpenFang agent. The join is
mechanical: `sovereign/bin/fleet-join` (Bun) renders `agent.toml` + `system.md`
from the fleet identity, writes them to `sovereign/agents/<name>/` (canonical,
git) and `~/.openfang/agents/<name>/` (live), then hyper-races activation:
`POST /api/agents {manifest_toml}` vs `POST /api/agents {template}` —
first 201 wins, loser deduped, verified via `GET /api/agents`. If the API is
down, the kernel auto-spawns the agent from disk on next boot (idempotent).

### Trigger protocol
When a fleet agent says "I want to join OpenFang" (or a coordinator decides
one should), the coordinator runs:

```
bun /home/toxic/estate/bin/fleet-join --name <name> --species <species> \
    --personality <plain words> --lane <lane> --task <plain words> \
    --sigil <emoji>
```

- `--name`: lowercase letters, digits, hyphens. Must not collide with an
  existing `sovereign/agents/<name>/`.
- Fleet identity maps: name -> `name` + `[persona].name`; species +
  personality + lane/task -> `[persona].role` + `description`; lane/task ->
  `tags`. Species has no native OpenFang field — it folds into role/prompt.
- Model default: herd free-tier via llama-swap :25100
  (`openrouter-free/inclusionai/ling-3.0-flash-sante:free`, Ling-first per
  Chris 2026-09-17; verified live). Override with `--model`.
- Flags: `--dry-run` (render only), `--no-activate` (files only, kernel
  picks up on boot), `--no-commit` (skip git commit).
- The script commits to sovereign-projects main; push + verify the remote ref
  after (fetch-first, never force-push).

### Notes
- The joined agent keeps its fleet persona (species, personality, sigil) and
  narrates in squawk as Ember's crew.
- OpenFang API: `http://127.0.0.1:25196`. Uninstall:
  `DELETE /api/agents/{id}/uninstall` (removes the live dir too).
- Spec: `docs/fleet-openfang-join-spec.md` (Sorrel, 2026-09-30).
