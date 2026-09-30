# SOVEREIGN REORG PLAN — shingle → hatch/agents/ember, shingle-workspace collision resolved

**Status:** PLAN ONLY — staged for one-command execution. Do not run `REORG-EXECUTE.sh` without reading this doc.
**Re-validation 2026-09-20 (worker track, against live state):** 4 flaws found and fixed before execution —
systemd-run --user broken (cutover now operator-driven), `git mv` on untracked `runtime-cell.md` (track-aware move),
stash-guard path wrong + needs daemon restart, pitchfork respawn storm on the bridge daemon (verified fallback).
Runner-profiles shipment (runners.yml, bin/squawk-{profile,trace,follow}, 5 keys, wrapper --profile + FLEET_KEYS_DIR
fix) confirmed reorg-safe and folded into the manifest (§2 row 1a, §7).
**Author:** worker track 11 (sovereign reorg plan), 2026-09-19.
**Acceptance criteria:** zero bridge downtime, zero squawk downtime, every old hardcoded path keeps resolving, full rollback possible.

---

## 0. Why this layout (paper research)

Two production-monorepo layout sources ground the tree:

1. **all-source-os `MONOREPO_STRUCTURE.md`** (https://github.com/all-source-os/all-source/blob/HEAD/docs/MONOREPO_STRUCTURE.md) —
   top-level homes per concern: `apps/` (deployable services, incl. a `control-plane/`), `sdks/`, `crates/`, `packages/`,
   `deploy/`, `docs/`, `scripts/`, `tooling/`. Justification for our tree: **every top-level child gets a named home
   for what it IS** (service vs. docs vs. scratch), and deployable/production services are never mixed into scratch dirs.
2. **kanggle `monorepo-lab` `platform/repository-structure.md`** (https://github.com/kanggle/monorepo-lab/blob/HEAD/platform/repository-structure.md) —
   hard rules: service directories live under named homes, **no new top-level directory without updating the layout doc**,
   docs carry ADRs. Justification: this file *is* the layout SSOT (the repo previously had none — part of why
   `shingle-workspace` drifted into being both scratch and the live bridge home), and moves are done with compat shims,
   not flag days.

Applied: `bridge/` (production service home), `hatch/` (the hatch-cell side of the world, with `agents/ember/` as the
Ember agent home and `docs/` for hatch/bridge/cell docs), `scratch/` (explicitly non-production staging — the old
`shingle-workspace` renamed, since its content is 95% staging scripts with one production file that gets extracted).

---

## 1. Target tree

```
/home/toxic/sovereign/
├── hatch/                              # NEW — hatch (cell) side of the world, material that lives on yote
│   ├── agents/
│   │   └── ember/                      # ← /home/toxic/shingle MOVED here (the Ember operational home)
│   │       ├── bin/squawk              #   (unchanged contents: chat/, coord/, squawk-relay/,
│   │       ├── chat/                   #    squawk-root/, todos.md, directives.md, keys.quarantine-*, ...)
│   │       ├── coord/
│   │       ├── squawk-relay/
│   │       ├── squawk-root/
│   │       ├── todos.md
│   │       └── directives.md
│   └── docs/                           # hatch/bridge/cell docs consolidated here
│       ├── README.md
│       ├── bridge-docs/                # ← shingle-workspace/bridge-docs/
│       ├── ws-exec-8379-audit-20260914.md      # ← docs/
│       ├── connector-bridge-routing-d4734168.md # ← docs/
│       └── runtime-cell.md             # ← docs/Meta/Muse AI/Jarvis/runtime-cell.md
├── bridge/                             # NEW — production home of the live hatch↔yote exec bridge
│   ├── README.md
│   └── awrawr_ws_exec.py               # ← shingle-workspace/awrawr_ws_exec.py (canonical, tracked)
├── scratch/                            # ← shingle-workspace RENAMED (explicitly non-production)
│   ├── README.md                       #   ("staging — not a service home; do not add daemon run paths here")
│   ├── awrawr_ws_exec.py -> ../bridge/awrawr_ws_exec.py   # compat file symlink (installed post-restart)
│   └── ...                             #   (all other staging content unchanged)
├── shingle-workspace -> scratch        # compat dir symlink
├── bin/                                # + io-rate-reaper, iowait-gate, orphan-reaper, safe-rg,
│                                       #   saturation-watchdog, oracle-judge, git-lfs  (← scratch/bin/, consolidated)
├── pitchfork.toml                      # hand-edited: 3 run/env paths → canonical; stale GENERATED header fixed
└── ...                                 # every other current child keeps its home (see §2)
```

**Decision: `shingle-workspace` → `scratch/` + bridge extraction (not `bridge/` or `servers/` rename).**
The dir is ~150 items of staging scripts (patch_*.py, model*.py, *_staging dirs, audits, one-off sweeps) with exactly
one production file (`awrawr_ws_exec.py`, the live `/exec-ws` bridge). Renaming the whole dir to `bridge/` or `servers/`
would *enshrine* scratch as a service home — the opposite of production-grade. So: the production file gets a real
production home (`bridge/`), and the rest is honestly named `scratch/`. Compat symlinks preserve every old path (§5).

**Decision: canonical bridge at `sovereign/bridge/`, not `sovereign/hatch/bridge/`.**
The bridge server is a yote-side production service supervised by pitchfork (like every other daemon in `pitchfork.toml`);
`hatch/` holds hatch-*cell* material (docs, agent homes, cell runtime). Grouping by *what runs where*, not by *what it's
for*, matches the monorepo sources above. (Considered alternative `hatch/bridge/` — rejected: it would bury a
pitchfork-supervised yote service inside the cell-material tree, confusing the next reader about where it executes.)

---

## 2. Per-item move table (source → dest)

| # | Source | Dest | Kind |
|---|--------|------|------|
| 1 | `/home/toxic/shingle` (whole tree) | `/home/toxic/sovereign/hatch/agents/ember` | `mv` (rename(2)) |
| 1a | *(inside row 1's tree — rides along, verified 2026-09-20)* runner-profiles shipment: `squawk-root/runners.yml` (v1, 6 profiles), `bin/squawk-profile`, `bin/squawk-trace`, `bin/squawk-follow`, 5 new `0600` keys in `squawk-root/keys/`, updated `bin/squawk` (`--profile`, `FLEET_KEYS_DIR=$ROOT/keys` bugfix) | same relative paths under ember home | rides in the atomic `mv`; all paths resolve via `$SQUAWK_ROOT` + `readlink -f`/`realpath` (reorg-safe by design) |
| 2 | *(new)* `/home/toxic/shingle` | symlink → `/home/toxic/sovereign/hatch/agents/ember` | compat |
| 3 | `/home/toxic/sovereign/shingle-workspace/awrawr_ws_exec.py` | `/home/toxic/sovereign/bridge/awrawr_ws_exec.py` | `cp -p` first (see §6), header note updated |
| 4 | `/home/toxic/sovereign/shingle-workspace/bin/*` (7 tools, zero external refs — verified 2026-09-19) | `/home/toxic/sovereign/bin/` | `mv` per file (collision-checked) |
| 5 | `/home/toxic/sovereign/shingle-workspace/bridge-docs/` | `/home/toxic/sovereign/hatch/docs/bridge-docs/` | `mv` |
| 6 | `/home/toxic/sovereign/shingle-workspace` (remainder) | `/home/toxic/sovereign/scratch` | `mv` (rename(2)) |
| 7 | *(new)* `/home/toxic/sovereign/shingle-workspace` | symlink → `scratch` | compat |
| 8 | `/home/toxic/sovereign/docs/ws-exec-8379-audit-20260914.md` | `/home/toxic/sovereign/hatch/docs/` | `git mv` |
| 9 | `/home/toxic/sovereign/docs/connector-bridge-routing-d4734168.md` | `/home/toxic/sovereign/hatch/docs/` | `git mv` |
| 10 | `/home/toxic/sovereign/docs/Meta/Muse AI/Jarvis/runtime-cell.md` | `/home/toxic/sovereign/hatch/docs/runtime-cell.md` | `git mv` |
| 11 | `pitchfork.toml` (in place) | 3 path updates + header fix (§6) | hand-edit (generator retired) |
| 12 | `tools/fleet-ops/cron-mirror/README.md` historical note, `xfer-report-20260915/REPORT.md` | — | left as history; still resolves via symlink |
| 13 | `bench-wt-tau/pitchfork.toml` (stale worktree copy, `.shingle` refs) | — | left; non-live worktree artifact |
| 14 | `sovereign/projects/range/ranch/squawk-ws/squawk_ws_server.py:42` default `SQUAWK_CHAT_ROOT` | — | optional hygiene one-liner (env overrides in prod) |

**Named homes for all other current sovereign children** (nothing orphaned; nothing else moves):
- **Orchestration:** `pitchfork.toml`, `config/` (ports.env SSOT), `stack/` (service scripts), `mise/`, `agents/` (bash-agent-merged, coyote, shingle-pilot), `profiles/`
- **Services & code:** `src/`, `tools/`, `projects/`, `fleet/`, `gear/`, `9router`, `bin/`, `lib/`, `scripts/`
- **Data/state (do not reorganize):** `data/`, `logs/`, `qdrant_data/`, `prometheus-data/`, `brain/`, `snapshots/`
- **Docs/research:** `docs/`, `research/`, `audit/`, `audit-output/`, `architecture.d2`, `appinfo.json`
- **Skills/rules:** `skills/`, `sovereign-skills/`, `ast-grep-rules/`
- **Lane/worktree dirs (dated `*-20260914`, `wt-*`, `stash-*`, `merge-*`, `worktrees/`, `buildsrv-test*`):** stay as-is; future consolidation candidate, explicitly out of scope for this reorg
- **Runtime/build:** `node_modules/`, `tests/`, `test/`, `tools-2/`, `coverage/`, `output/`, `xfer-report-20260915`, `analysis-*`
- **Special:** `yote -> projects/yote` (symlink, untouched), `tailscale/`, `forensics-srv/`
- **Out of scope (not sovereign children):** `/home/toxic/cell-backup-*` (hatch cell backups), `/home/toxic/awrawr_ws_exec.py` (synced fallback copy of the bridge — keep, per pitchfork.toml comment), `/home/toxic/kimi-auto`, `/home/toxic/paper-poller`, `/home/toxic/refusal-hunt`, `/home/toxic/gemini-mcp`, `/home/toxic/whatsapp-mcp`, `/home/toxic/boundless`, `/home/toxic/ws-exec-tunnel.py`

---

## 3. Survey findings (what the plan is built on — verified live 2026-09-19)

- **Supervisor:** `pitchfork supervisor run --boot` (PID 1006), unit `pitchfork.service` with `WorkingDirectory=/home/toxic/sovereign` → every `dir = "."` in pitchfork.toml = `/home/toxic/sovereign`. Relative `dir`s (e.g. `projects/yote`) resolve under it.
- **Live `.shingle` references (production):**
  - `pitchfork.toml:290` — `[daemons.squawk-feed]` `run = "exec /home/toxic/.shingle/squawk-relay/run-feed.sh"`
  - `pitchfork.toml:350` — `[daemons.squawk-ws]` `env SQUAWK_CHAT_ROOT="/home/toxic/.shingle/squawk-root"`
  - `pitchfork.toml:274/282` — `[daemons.squawk-relay-sink]` / `[daemons.squawk-relay-forward]` `run`+`dir` under
    `/home/toxic/.shingle/squawk-relay/` (missed by the 2026-09-19 survey; resolve via the compat symlink chain —
    left on old paths deliberately, canonicalization is future hygiene)
  - `projects/range/ranch/squawk-ws/squawk_ws_server.py:42` — `CHAT_ROOT` default `/home/toxic/.shingle/squawk-root` (env overrides)
  - `fleet/dispatch_fallback.py:26` — `DEFAULT_DIRECTIVES = "/home/toxic/.shingle/directives.md"`
  - `shingle/bin/squawk` wrapper — defaults `ROOT=/home/toxic/.shingle/squawk-root`, `CHAT_PY=/home/toxic/.shingle/chat/chat.py`
  - hatch-side `~/workspace/bin/squawk:19` — `SQUAWK_ROOT = "/home/toxic/.shingle/squawk-root"` (publishes via bridge; unaffected, resolves through symlink)
  - `shingle/squawk-health.sh`, `shingle/directives.md`, `shingle/todos.md`, `shingle/coord/work/*` — internal self-refs (append-only logs; left as history)
- **Live `shingle-workspace` references (production):**
  - `pitchfork.toml:367` — `[daemons.awrawr-ws-exec]` `run = "... /home/toxic/sovereign/shingle-workspace/awrawr_ws_exec.py"`
  - `tools/stash-guard/stash-guard.py:82` — exclude list contains `"shingle-workspace/"` (gitignore-style patterns
    matched against `git status` paths, NOT an inotify watch; real path is `tools/stash-guard/`, the plan's
    `tools/fleet-ops/` prefix was wrong — corrected 2026-09-20)
  - everything else: `.bak` files, `xfer-report`, READMEs, `.tau` logs, worktree copies (history)
- **Symlink status quo:** `/home/toxic/.shingle -> shingle` (relative, in `/home/toxic`). After the move, `/home/toxic/shingle`
  becomes a symlink → `sovereign/hatch/agents/ember`, and `.shingle` keeps resolving through it (double-hop symlinks are fine).
- **inotify:** `squawk-ws` watches `SQUAWK_CHAT_ROOT`; `squawk-relay/watcher.py` polls channel files. `mv` of a *parent* dir does not
  change child inodes → watches survive **iff the move is rename(2), never copy+delete**. The script enforces `mv` and
  verifies inodes before/after.
- **Cron:** no cron daemon on yote (`crontab` not installed); scheduling is systemd user timers + hatch-side crons
  (bridge-watchdog 5m, squawk-monitor 5m). `squawk-watchdog.timer` runs `/home/toxic/.local/share/squawk-watchdog/squawk-watchdog.sh`
  (no `.shingle` refs — verified).
- **Git:** `/home/toxic/sovereign` is a git repo with uncommitted changes, including `M shingle-workspace/awrawr_ws_exec.py`
  (the live bridge). `docs/Meta/Muse AI/Jarvis/runtime-cell.md` is UNTRACKED (`git mv` refuses untracked sources —
  the script uses a track-aware move helper). Baseline commit+push is step 1 of execution.
- **pitchfork `awrawr-ws-exec` is in a respawn storm (observed 2026-09-20):** supervisor marks the daemon `errored`
  and spawns a doomed copy every ~10–20s, each dying instantly with `EADDRINUSE` because a live holder
  (pitchfork child, serves the bridge fine) owns `127.0.0.1:8379`. The cutover restart must be verified live;
  fallback is killing the stale holder PID via a fresh bridge call — the next respawn then binds cleanly.
- **`systemd-run --user` is broken on yote (verified 2026-09-20):** user manager reports `degraded`; a probe timer
  fired but its transient service unit never materialized (no-op). The delayed-restart design is therefore
  REPLACED: the bridge cutover is operator-driven from hatch after the script's bridge call returns (§4 Phase 7, §6).
- **pitchfork.toml header lies:** it says "GENERATED … DO NOT EDIT DIRECTLY — Run: bun run scripts/generate.ts", but
  `sovereign/AGENTS.md` (standing rule, 2026-09-14) retires the generator: the toml is hand-edited. Execution follows
  AGENTS.md and fixes the header comment in the same edit.

---

## 4. Ordered command sequence (what REORG-EXECUTE.sh does)

**Phase 0 — preflight (read-only, aborts on failure):** assert user is `toxic`; supervisor PID alive; `:8379` listening;
`git` repo present; capture inode manifest of `shingle/` and `shingle-workspace/`; list any process with cwd under the
moved trees (warn-only); resolve the pitchfork daemon id for `awrawr-ws-exec` via `pitchfork list` (fail loud if unknown).

**Phase 1 - baseline:** targeted git add of the reorg paths only (reorg_add() in the script -- never git add -A:
the tree is shared with ~8 active workers; a blind add sweeps in their in-flight lockfiles and secret-bearing logs,
tripping the repo pre-commit hook. The lockfile rule is bypassed via the hook's documented PI_ALLOW_LOCKFILE_CHANGE=1;
the secret-entropy rule is never bypassed -- other tracks' dirty files stay in the working tree, owned by their workers),
then commit + push (push may WARN-fail if yote git auth is down -- commits stay local).

**Phase 2 — build new homes:** `mkdir -p hatch/agents hatch/docs bridge`; drop `README.md` in each.

**Phase 3 — Ember move (atomic rename):** `mv /home/toxic/shingle hatch/agents/ember` then
`ln -s /home/toxic/sovereign/hatch/agents/ember /home/toxic/shingle`. Verify inode manifest: every pre-move path
keeps its inode (concurrent additions tolerated — 8 workers append to these trees). The runner-profiles shipment
(§2 row 1a) rides along in this `mv`; its `readlink -f`/`realpath` resolution keeps working through the symlink chain.

**Phase 4 — bridge extraction (copy-first, zero downtime):** `cp -p shingle-workspace/awrawr_ws_exec.py bridge/awrawr_ws_exec.py`;
update its header "Tracked copy" note to the new path. The running daemon keeps serving the old path (already in memory).

**Phase 5 — scratch consolidation:** move `shingle-workspace/bin/*` → `sovereign/bin/` (collision-checked);
`shingle-workspace/bridge-docs/` → `hatch/docs/bridge-docs/`; move the three hatch docs (§2 #8–10) with the
track-aware helper (`git mv` if tracked, `mv` + `git add` if untracked — `runtime-cell.md` is untracked);
then `mv shingle-workspace scratch` + `ln -s scratch shingle-workspace`.

**Phase 6 — config updates (hand-edit, generator stays retired):**
- `pitchfork.toml`: 3 path replacements → canonical (§6), header comment fix; backup `pitchfork.toml.pre-reorg-<ts>`; validate with `python3 -c "import tomllib..."`.
- `tools/stash-guard/stash-guard.py`: exclude `"shingle-workspace/"` → `"scratch/"` (+ add `"bridge/"`),
  then `pitchfork restart sovereign/stash-guard` so the running daemon picks up the new list (edit alone is inert).
- `fleet/dispatch_fallback.py`: `DEFAULT_DIRECTIVES` → canonical ember path.
- Commit + push: `reorg: shingle→hatch/agents/ember, shingle-workspace→scratch, bridge/ canonical`.

**Phase 7 — operator-driven bridge cutover (systemd-run REPLACED):** `systemd-run --user` is broken on yote
(user manager `degraded`; transient units vanish — verified 2026-09-20), so the script schedules NOTHING. After the
script's bridge call returns, the hatch operator runs `pitchfork restart sovereign/awrawr-ws-exec` as a separate,
fire-and-forget bridge call (the response dies with the server — expected), then verifies 101 + `echo BRIDGE-LIVE`.
Fallback: if the port stays wedged, kill the stale holder PID via a fresh bridge call; the supervisor's ~20 s
respawn loop binds the next copy cleanly. Copy-first (Phase 4) guarantees the toml never points at a missing file.

**Phase 8 — post-restart (from hatch, after 101 verified):** swap the stale copy for the compat symlink:
`mv scratch/awrawr_ws_exec.py scratch/awrawr_ws_exec.py.pre-reorg && ln -s ../bridge/awrawr_ws_exec.py scratch/awrawr_ws_exec.py`;
then run the verification checklist (§7). The script prints this as its final block; it does not do it itself because
the restart it scheduled hasn't fired yet when the script exits.

---

## 5. Compat-symlink table

| Old path (must keep working) | Resolves to | Mechanism |
|---|---|---|
| `/home/toxic/shingle` | `/home/toxic/sovereign/hatch/agents/ember` | new symlink (replaces moved dir) |
| `/home/toxic/.shingle` | → `shingle` → ember home | existing relative symlink, untouched |
| `/home/toxic/.shingle/squawk-root` | `…/hatch/agents/ember/squawk-root` | via chain above |
| `/home/toxic/.shingle/squawk-relay/run-feed.sh` | `…/hatch/agents/ember/squawk-relay/run-feed.sh` | via chain above |
| `/home/toxic/sovereign/shingle-workspace` | `/home/toxic/sovereign/scratch` | new symlink |
| `/home/toxic/sovereign/shingle-workspace/awrawr_ws_exec.py` | `/home/toxic/sovereign/bridge/awrawr_ws_exec.py` | dir symlink → `scratch/awrawr_ws_exec.py` → file symlink `../bridge/…` (installed Phase 8) |
| hatch-side `~/workspace/bin/squawk` default `SQUAWK_ROOT` | unchanged path, resolves via chain | no change needed |

---

## 6. Atomic pitchfork.toml update procedure (bridge path)

The `[daemons.awrawr-ws-exec]` `run` line is read by the supervisor **only at daemon spawn**. Procedure:
1. `cp -p` the file to `bridge/` (Phase 4) — old path still valid, running daemon untouched.
2. Hand-edit `pitchfork.toml`: `shingle-workspace/awrawr_ws_exec.py` → `bridge/awrawr_ws_exec.py` (plus the two
   `.shingle` → ember-home updates, plus header fix). Validate TOML parses; keep timestamped backup.
3. Commit + push (Phase 6) -- targeted reorg_add(), same rationale as Phase 1.
4. Operator-driven `pitchfork restart` from hatch (Phase 7) — issued as its own bridge call AFTER the script's
   bridge call has returned, so the caller is never killed mid-flight (same hazard class as the AGENTS.md
   `awrawr-mcp.service` rule). Fire-and-forget: the command's response dies with the server — expected; the
   operator then polls for 101. (systemd-run --user was the original design; it is broken on yote.)
5. From hatch: WS handshake to `/exec-ws` must return **101**; run `echo BRIDGE-LIVE` via the bridge (proves the new path executes).
6. Only then: Phase 8 stale-copy → symlink swap.

There is no window where the daemon points at a missing file: at every instant, the path in the toml exists
(old path until restart, new path from `cp -p` onward).

---

## 7. Verification checklist

**On yote (script does these):**
- [ ] `realpath /home/toxic/shingle` = `/home/toxic/sovereign/hatch/agents/ember`
- [ ] `realpath /home/toxic/.shingle/squawk-root` = `…/hatch/agents/ember/squawk-root`
- [ ] `realpath /home/toxic/sovereign/shingle-workspace` = `/home/toxic/sovereign/scratch`
- [ ] inode manifest: `squawk-root/` and channel file inodes identical before/after (inotify continuity)
- [ ] `python3 -c "import tomllib; tomllib.load(open('pitchfork.toml','rb'))"` clean
- [ ] `pitchfork list` shows `awrawr-ws-exec`, `squawk-ws`, `squawk-feed` (ids as before)
- [ ] `git status` clean after final commit; pushed

**From hatch (parent runs after script):**
- [ ] `pitchfork restart sovereign/awrawr-ws-exec` issued as its own bridge call AFTER the script returned (fire-and-forget)
- [ ] WS handshake to `https://github-mcp-host.tailc9ac71.ts.net/exec-ws` → **101** (bridge live on new path)
- [ ] `exec.py 'echo BRIDGE-LIVE'` succeeds (proves the new canonical path executes)
- [ ] `exec.py 'md5sum /home/toxic/sovereign/bridge/awrawr_ws_exec.py'` matches the committed blob
- [ ] squawk publish round-trip: `squawk send fleet` (hatch CLI) → message file appears under new ember home; `squawk read fleet` returns it (proves symlink chain + inotify)
- [ ] runner-profiles: `exec.py '/home/toxic/shingle/bin/squawk profiles'` lists 6 profiles; `runners.yml` resolves via `readlink -f` at `…/hatch/agents/ember/squawk-root/runners.yml`; `FLEET_KEYS_DIR` = ember-home `squawk-root/keys`; a `--profile` post signs correctly (the wrapper's keys-dir bugfix survives the move)
- [ ] `exec.py 'systemctl --user is-active pitchfork'` and `pitchfork` daemon statuses green; `:25147` (squawk-ws) and `:8379` listening
- [ ] Phase 8 swap done; old exact bridge path resolves to the live file

---

## 8. Rollback plan

Every step is a rename(2) or symlink; the script writes `/home/toxic/sovereign/REORG-MANIFEST.txt` listing each
operation. Rollback (mechanical, reverse order):
1. If the bridge was already restarted on the new path: revert the toml `run` line, `pitchfork restart` again (from a
   non-bridge context — i.e. a separate bridge call issued after the previous one returned, or Chris's local shell),
   verify 101. (systemd-run is not used; there is no timer to cancel.)
2. `rm` the compat symlinks; `mv` dirs back (`scratch` → `shingle-workspace`, `hatch/agents/ember` → `/home/toxic/shingle`);
   `git mv` the docs back; restore `pitchfork.toml.pre-reorg-<ts>`.
3. `git commit -m "reorg: rollback" && git push`; re-run §7 checklist.
4. Data-loss risk is nil: no deletes except symlink removals; the one file "removed" in Phase 8 is first renamed to
   `*.pre-reorg`.

---

## 9. Red-team (3+ failure modes, each mitigated in the plan)

1. **inotify watches die on move.** *Mode:* someone implements the move as `cp -r` + `rm`, changing inodes; `squawk-ws`
   (watching `SQUAWK_CHAT_ROOT`) and the relay watcher go blind silently. *Mitigation:* the script uses only `mv`
   (rename(2)); Phase 0 captures an inode manifest and Phase 3 asserts it unchanged; §7 requires a live publish
   round-trip, which fails loudly if inotify broke.
2. **Restarting the bridge from inside a bridge call kills the caller.** *Mode:* `pitchfork restart sovereign/awrawr-ws-exec`
   issued through the WS exec server terminates the server mid-call; response lost, operator blind. (Same hazard class as
   the AGENTS.md `awrawr-mcp.service` rule.) *Mitigation:* copy-first + toml edit while the daemon runs the old image;
   the restart is operator-driven from hatch *after* the script's bridge call returns (fire-and-forget +
   poll for 101 — systemd-run is broken on yote); §6 proves there is no instant where the toml points at a missing file.
3. **Stale "GENERATED — DO NOT EDIT" header causes the next operator to run the retired generator.** *Mode:* header says
   run `bun run scripts/generate.ts`; AGENTS.md says the generator is retired and running it destroys live daemons.
   *Mitigation:* the header is fixed in the same atomic edit (Phase 6), citing AGENTS.md; the plan documents the
   discrepancy here so no one "fixes" it back.
4. **Double-hop symlink confusion** (`~/.shingle` → `shingle` → `sovereign/hatch/agents/ember`). *Mode:* a tool does naive
   string-prefix path comparison and fails to recognize the new home. *Mitigation:* §7 asserts `realpath` resolution;
   known consumers were audited — all use the path opaquely (open/poll/inotify), none do prefix matching (verified
   2026-09-19: squawk-ws server, feed runner, wrapper, hatch CLI, dispatch_fallback).
5. **Uncommitted working tree (incl. modified live bridge file) collides with the move.** *Mode:* moving files with
   dirty git state, then a bad commit loses the live bridge's uncommitted fix. *Mitigation:* Phase 1 commits + pushes
   the baseline *before* any rename; moves preserve working-tree state; Phase 6 commits again.

6. **`systemd-run --user` silently no-ops.** *Mode:* the delayed restart is scheduled, the timer "fires", but the
   user manager is `degraded` and the transient service unit never materializes — the cutover never happens and the
   operator believes it did. *Mitigation (2026-09-20):* verified broken with a probe timer; design replaced with an
   operator-driven restart from hatch after the script's bridge call returns (fire-and-forget + poll for 101).
7. **`git mv` on an untracked file aborts the script mid-reorg.** *Mode:* `docs/Meta/Muse AI/Jarvis/runtime-cell.md`
   is untracked; `git mv` exits 128 (`not under version control`) and `set -e` kills the script between renames.
   *Mitigation (2026-09-20):* track-aware move helper — `git mv` when tracked, `mv` + `git add` when not.
8. **Stash-guard excludes go stale silently.** *Mode:* the plan cited `tools/fleet-ops/stash-guard/stash-guard.py`
   (wrong path — real: `tools/stash-guard/`); the script's guarded `grep` skipped the edit without failing, and
   even a correct edit is inert until the daemon restarts. After the rename, `scratch/` would get guarded as WIP.
   *Mitigation (2026-09-20):* path corrected, exclude updated, `pitchfork restart sovereign/stash-guard` added.
9. **Pitchfork respawn storm on the bridge daemon.** *Mode:* supervisor marks `awrawr-ws-exec` errored while a live
   holder owns `:8379`; it spawns doomed EADDRINUSE copies every ~20 s. A naive `pitchfork restart` may not clear
   the wedge. *Mitigation:* verify 101 after restart; fallback is killing the stale holder PID via a fresh bridge
   call and letting the next respawn bind cleanly.
10. **Blind `git add -A` trips the secret-entropy hook.** *Mode:* with ~8 workers sharing the tree, a full-tree add
   sweeps in other tracks' in-flight lockfiles and secret-bearing logs (observed 2026-09-20: kimi JWTs in a
   worker's staged dumps); the pre-commit hook rejects the commit. The lockfile rule has a documented bypass
   (`PI_ALLOW_LOCKFILE_CHANGE=1`); the secret rule must NEVER be bypassed. *Mitigation (2026-09-20):* the script
   stages only its own paths (`reorg_add()`); other tracks' dirty files stay in the working tree. Flagged to the
   coordinator: a worker is leaving JWT-bearing files in the tree.

## 10. Execution needs (for the parent/coordinator)

- Run `REORG-EXECUTE.sh` **on yote as `toxic` via the bridge** (`exec.py 'bash /home/toxic/sovereign/REORG-EXECUTE.sh'`),
  or from Chris's local yote shell. Expected wall time: < 5 min (dominated by git push).
- After the script exits: run the hatch-side half of §7 — FIRST the operator-driven `pitchfork restart`
  (its own bridge call), then 101 handshake, `echo BRIDGE-LIVE`, squawk round-trip, runner-profile checks, Phase 8 swap.
- Open question for Chris (non-blocking): `bench-wt-tau/pitchfork.toml` is a stale worktree copy with old paths — left
  alone; say the word if it should be synced or deleted.
- The script is idempotent per-step (guards skip completed steps) but is **not** re-run safe across the delayed restart
  boundary — run once; use §8 to roll back, never re-run blindly.
