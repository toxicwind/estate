# CARTOGRAPHER MAP - CHRONOS-FORGE v15.0 (cycle 1)
repo_hash=40469387b7  run_id=20261016T030439Z-27f514  agent_id=e5b8cab5  cycle=1
snapshot evidence ⟦PE:pe_ce21ca2b8454b434⟧ (snap_c1_pe_ce21ca2b8454b434.b64, gzip+b64)

## 1. Entrypoint graph
CURRENT REALITY: empty repo - NOT a git repo, 0 source files; state.dirty=NOT_A_GIT_REPO.
No runnable entrypoint exists today; only the .estate control plane is live.

INTENDED GRAPH (scaffolded repo) - CLI -> main -> routers/handlers -> IO boundaries:

  argv / flags
     |
     v
  +----------------------+     config precedence (#3): defaults<file<env<CLI
  | main / __main__      |<-------------------------------+
  +----------------------+
     |
     v
  +----------------------+
  | config module        |  -> one immutable Config
  +----------------------+
     |
     v
  +----------------------+        +-------------------------+
  | routers / dispatch   |------> | handlers (per CHRONOS   |
  |  command -> table    |        | step: BOOT/SNAP/CARTO..)|
  +----------------------+        +-------------------------+
     |                                    |
     v                                    v
  +--------------------------------------------------------+
  | IO boundary layer (single choke point; paths from Config)|
  | repo.lock hub.lock state.json manifest.json registry.json|
  | inbox/ outbox/ artifacts/                                 |
  +--------------------------------------------------------+

## 2. .estate state layout (ACTUAL paths verified this cycle)
Correction vs assumption: state/manifest/repo.lock live PER-REPO under
repos/<hash>/; only hub/registry.json + hub.lock are hub-level.

  path (relative to .estate/)            owner                 role
  --------------------------------------  --------------------  -------------------------
  hub/registry.json                       hub coordinator       repo_hash->repo_root, coord tmux
  hub/hub.lock                            hub coordinator       cross-repo serialization
  repos/40469387b7/manifest.json           bootstrap/provisioner identity: agent_id, run_id
  repos/40469387b7/repo.lock               any mutating expert   per-repo write mutex
  repos/40469387b7/state.json             coordinator/SNAPSHOT  cycle, head, dirty, actions[]
  repos/40469387b7/inbox/                 coordinator -> experts task intake
  repos/40469387b7/outbox/                experts               artifact emit (this file)
  repos/40469387b7/artifacts/             SNAPSHOT              snap_c1_*.b64, agent/run id

LOAD ORDER each cycle:
  1. hub/registry.json       READ   resolve repo_hash -> repo_root + coord tmux
  2. repos/<h>/manifest.json READ   bind agent_id + run_id
  3. repos/<h>/repo.lock     ACQUIRE blocking, before ANY repo mutation
  4. repos/<h>/state.json    READ then UPDATE (append action, bump cycle) under lock
  5. repos/<h>/inbox/        READ   drain assigned tasks
  6. repos/<h>/outbox/       WRITE  exactly one artifact per expert
  7. repos/<h>/artifacts/    READ prior snaps; WRITE snap_c<N>_*.b64 (SNAPSHOT)
  hub.lock only for cross-repo ops, taken AFTER repo.lock is held.

## 3. Config + env var precedence
No config file / env wiring exists yet (empty repo). INTENDED precedence (later wins):
  defaults  <  config file  <  environment  <  CLI flags
  - defaults:    compiled-in constants in the scaffold config module
  - config file: <repo>/estate.yaml (or .estate/config.json), optional
  - environment: CHRONOS_* vars (below)
  - CLI flags:   --repo-root/--repo-hash/--run-id/--agent-id/--cycle (highest)
  ENV VARS the scaffold must honor:
    CHRONOS_REPO_ROOT  (default /home/toxic/development/estate)
    CHRONOS_REPO_HASH  (default 40469387b7)
    CHRONOS_RUN_ID     (default 20261016T030439Z-27f514)
    CHRONOS_AGENT_ID   (default e5b8cab5)
    CHRONOS_CYCLE      (default 1)
  Merge into one immutable Config; IO layer reads paths only from Config.

## 4. IO boundaries + lock ordering
Per cycle READ : hub/registry.json, repos/<h>/manifest.json, repos/<h>/state.json,
                 repos/<h>/inbox/, repos/<h>/artifacts/snap_*.b64
Per cycle WRITE: repos/<h>/state.json (append action), repos/<h>/outbox/<EXPERT>.md,
                 repos/<h>/artifacts/snap_c<N>_pe_*.b64 (SNAPSHOT only)
LOCK ORDERING (deadlock-free):
  - repo.lock MUST be held before ANY mutation of repos/<h>/state.json or outbox/.
  - hub.lock  ONLY for cross-repo/hub ops; acquire AFTER repo.lock, never before.
  - global order repo.lock -> hub.lock; release reverse (hub.lock then repo.lock).
  - read-only probes take no lock; snapshot/coordinator mutations take repo.lock.

## 5. AFTER cluster A scaffold (verification targets for SURGEON/coordinator)
Once cluster A lands, the empty repo becomes a runnable tree whose graph is
CLI(argv) -> main.__main__ -> config module (defaults<file<env<CLI) -> routers/dispatch
table -> per-step handlers -> a single IO boundary layer. SURGEON verifies targets by
checking that (a) a CLI/main entry exists and folds flags+CHRONOS_* env into one Config;
(b) a router maps each CHRONOS step (BOOT/SNAP/CARTO/.../PROOF) to a handler; (c) every
filesystem touch (repo.lock, hub.lock, state.json, manifest.json, registry.json, inbox/,
outbox/, artifacts/) funnels through that one IO layer obeying repo.lock-before-mutation
then hub.lock-for-cross-repo ordering; and (d) no handler builds .estate paths inline.
state.json keeps advancing cycle with one appended action per step; head/dirty stay
git-unaware (NOT_A_GIT_REPO) until a real VCS is introduced.
