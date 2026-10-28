# EXHUMER REPORT ? entropy / hotspots / brittleness

**Run**: 20261016T030439Z-27f514 ? **Agent**: e5b8cab5 ? **Cycle**: 1 ? **Repo**: /home/toxic/development/estate (hash 40469387b7)
**Snapshot**: ?PE:pe_ce21ca2b8454b434? (snap_c1_pe_ce21ca2b8454b434.b64) ? head="", dirty=NOT_A_GIT_REPO
**Independence**: investigated directly; no other outbox/ file was read. Sibling reports (OPERATOR_PROOFPLAN.md, SURGEON_CLUSTERS.md) were observed present at probe time but deliberately not opened.

## 1. Top-5 hot / risky items

| # | Item | Evidence | Risk |
|---|------|----------|------|
| 1 | No git repo | state.json `"dirty": "NOT_A_GIT_REPO"`; `git status` ? `fatal: not a git repository (or any parent up to mount point /)` | No history/diff/rollback; every cycle is a cold start; churn + dirty metrics permanently degenerate |
| 2 | Hardcoded absolute paths | `"repo_root": "/home/toxic/development/estate"` in BOTH manifest.json and hub/registry.json | Repo is unrelocatable; hub maps exactly one root; a move/rename orphans all state |
| 3 | Single-writer lock files, no locking | repo.lock and hub/hub.lock are 0-byte, mode 644, root:root; nothing checks them (no code exists) | Two coordinators both "hold" the lock at once; last writer silently wins |
| 4 | No .gitignore | controlled `git init` test showed the only untracked entry as `?? .estate/` | First `git add -A` commits state.json, both locks, hub registry, artifacts, and sibling experts' reports |
| 5 | No tests, no source, no README | `find` for *.py / *.sh / *.md / *test* / .gitignore inside repo ? 0 hits | Nothing validates the .estate schema; entropy grows every cycle with zero feedback signal |

## 2. Brittle constants / hardcoded paths / suspicious env reads (exact values)

- state.json: `"head": ""`, `"dirty": "NOT_A_GIT_REPO"`, `"cycle": 0`, `"done": false`, `"next": ""` ? sentinel strings used as data; `done` never flips without human action.
- manifest.json: `"repo_root": "/home/toxic/development/estate"`, `"created_utc": "2026-10-16T03:04:39Z"`, `"agent_id": "e5b8cab5"`, `"run_id": "20261016T030439Z-27f514"` ? absolute path plus run identity baked into a mutable state file that is rewritten every cycle.
- hub/registry.json: `"active_coord_tmux": "estate_40469387b7_coord"` ? **no tmux server is running** (`error connecting to /tmp/tmux-0/default`); the registry advertises a phantom coordinator session.
- repo.lock / hub.lock: 0 bytes, no PID / timestamp / host inside ? lock-file existence is the entire mutual-exclusion protocol.
- Permission asymmetry: repo dirs are root-owned 755 (`drwxr-xr-x root root`) while the parent `/home/toxic` is `drwx------ toxic toxic` ? a root-owned tree inside a user-private home; any non-root tool touching the repo hits EACCES.
- Env reads: NO CHRONOS_* / REPO / AGENT / RUN_ID / CYCLE variables are set in the ssh session ? all context flows by file convention only, so any tool expecting env injection silently no-ops or falls back to defaults.
- Snapshot artifact: `status` field is raw git stderr (`fatal: not a git repository...`) and `touched` is a full `git diff --no-index` usage dump ? the snapshot tool persists error text as data instead of guarding failures.
- Existing ignore convention /home/toxic/.agentignore lists `**/*.lockb`, `**/node_modules/`, `**/.git/`, `**/target/` ? notably it does NOT cover `.estate/`, so even the house ignore rules would commit the skeleton.

## 3. Failure paths (what breaks first)

**A. Repo stays empty.** The snapshot loop yields head="" / NOT_A_GIT_REPO forever; `cycle` increments but `actions[]` carries no signal; downstream experts diff nothing; `done` stays false indefinitely. First visible break: any step that shells `git diff`/`git log` and treats a non-zero exit as fatal ? it aborts on cycle 2, not cycle 1.

**B. Two coordinators race.** state.json is read-modify-written with no honored lock (nothing checks repo.lock). Concurrent cycles: (1) clobber `actions[]` and `cycle`, (2) overwrite `manifest.last_seen_utc` / `agent_id` mid-run, (3) the registry's single `active_coord_tmux` entry names only one session, orphaning the second coordinator into the same state with no owner. No atomic tmp+rename is used, so truncated/corrupt JSON is the likely end state.

**C. .estate committed by accident.** With no .gitignore, `git add -A` stages `.estate/` ? state.json, both lock files, hub/registry.json, every artifact b64, and sibling experts' outbox/*.md. Per-cycle churn then explodes (state.json mutates every cycle), other experts' reports leak into history, absolute paths get baked into the object store, and 0-byte lock files become tracked conflict magnets.

## 4. Tooling warnings observed (one-line fix hypothesis each)

| Warning | Observed | Fix hypothesis |
|---------|----------|----------------|
| Python 3.14.7 utcnow deprecation | Reproduced live: `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal... Use timezone-aware objects` | Replace `utcnow()` with `datetime.now(datetime.UTC)` in snapshot/state writers |
| git 2.55.0 default-branch hint | `hint: Using 'master' as the name for the initial branch... will change to "main" in Git 3.0` | `git config --global init.defaultBranch main` before the first init |
| git 2.55.0 missing global config | `fatal: unable to read config file '/root/.gitconfig': No such file or directory` (ssh runs as root) | Write a minimal /root/.gitconfig or set GIT_CONFIG_GLOBAL so every ssh-invoked git stops failing |
| Snapshot error-as-data | status/touched fields contain git usage text (?PE:pe_ce21ca2b8454b434?) | Guard with `git rev-parse --is-inside-work-tree` before status/diff; store a short sentinel instead of stderr |
| Phantom tmux in registry | registry.json `active_coord_tmux: estate_40469387b7_coord` but no tmux server/socket exists | Re-check liveness each cycle (`tmux has-session`) instead of trusting the stored name |

## 5. What SURGEON should target first (prioritized)

1. **Initialize git and commit a .gitignore excluding `.estate/`** ? immediately kills failure path C and restores real diff/churn signal every other expert depends on; must land before any source file. Note the house .agentignore does not cover `.estate/`, so the repo needs its own rule.
2. **Make state.json writes atomic and lock-honoring** ? write to a tmp file + `mv`, and give repo.lock real semantics (flock or O_EXCL create, PID written inside). Today's 0-byte lock is decorative and failure path B is wide open.
3. **De-hardcode paths and fix the snapshot tool's git handling** ? resolve repo_root from the repo's own location instead of the manifest constant, replace `utcnow()` with tz-aware UTC, and guard git calls so snapshots stop storing usage dumps as data.
