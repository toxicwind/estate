# mise + direnv coexistence — final design

Status: **FINAL** (2026-09-14). Hold lifted after the direnv/mise investigator's
findings; where earlier notes conflict, this document wins.

Supersedes: the kill-direnv workstream (cancelled — hook stays, `.envrc` files
stay), and the translate-`.envrc`-to-mise-`[env]` note (superseded — do NOT
duplicate `.envrc` vars into mise `[env]`).

## Why the boundary exists (failure mechanics, not just docs guidance)

Both tools hook the shell's directory-change/pre-command hooks and
snapshot/restore the environment. direnv records before/after in `DIRENV_DIFF`
(base64+zlib JSON) and **deletes PATH entries it doesn't recognize** on the
next hook run. mise's `src/direnv.rs` fights back with `add_path_to_old_and_new`
("trick direnv into thinking that this path has always been there… so it does
not remove it when it modifies PATH").

Concrete fallout:
- jdx/mise#70 → PR #73: mise wiped the entire PATH when PATH wasn't in
  DIRENV_DIFF.
- jdx/mise#2362: `use mise` + `source .venv/bin/activate` caused venvs to be
  "randomly deactivated" mid-session — the report that triggered formal
  deprecation.

Official stance: mise.jdx.dev/direnv carries a deprecated badge — do-not-use,
incompatibilities aren't bugs, direnv-compat PRs won't be accepted. The docs
concede simple coexistence (unrelated env vars) works fine. So: enforce the
boundary mechanically, don't rely on convention.

## Ownership

| mise owns | direnv owns |
|---|---|
| Tool versions + their PATH entries (shims) | Project env vars / secrets (`export`, dotenv) |
| ALL service/daemon env (`[env]`, `[vars]`, per-daemon `env`) | Interactive dev shells |
| Tasks, `[daemons]`, project diagnostics | Project-local PATH additions that don't overlap mise shims |

Rules:

1. **direnv NEVER fires for daemons.** Pitchfork services are mise-env-native;
   service env comes from mise `[env]`/`[vars]` only, never `.envrc`. (This
   constrains the `[daemons]` migration.)
2. **Never manage the same tool in both.** `layout python` + mise python is
   the canonical breakage (see #2362).
3. **Hook order: direnv-then-mise.** `.bashrc` already does this (direnv line
   44, mise line 46) — keep it. direnv's PATH additions land first; mise
   shims prepend after, so mise-managed tools win ties by order.
4. **Do NOT duplicate `.envrc` vars into mise `[env]`.** Tau's bash tool runs
   its own direnv preflight per command; double-sourcing the same var in both
   tools is last-writer-wins nondeterminism.
5. **Do NOT build mise-reads-`.envrc`.** Trust boundaries stay separate:
   direnv's allow-list vs mise's trust. Neither tool parses the other's config.
6. **Mechanical enforcement:** `scripts/env-boundary-check.sh` scans `.envrc`
   files for tool-management patterns (`layout python/node/conda`, `use mise`,
   venv activation) and fails loudly when mise manages that runtime in scope
   (global config + nearest project `mise.toml`). Wire into `mise doctor
   project` named checks at cutover; until then run it directly.

## Tau constraint (must be preserved)

Tau has **zero** `.envrc` files of its own. "First-class direnv" means Tau's
coding agent natively consumes *users'* `.envrc` files via
`engine/packages/coding-agent/src/exec/direnv.ts` — runs `direnv export json`,
honors the allow-list, strips `DIRENV_*` for a clean baseline. Nothing in this
design touches that path: no `.envrc` is deleted, moved, or duplicated.

## direnv-when-present decision

direnv is **not installed** on awrawr-pc (the `.bashrc` hook is a guarded
no-op). Decision: **document the lane as direnv-when-present; do NOT install
direnv.** Rationale:

- The only `.envrc` files on the box are upstream checkouts (jetify/devbox,
  infisical) whose backing tools (devbox, nix) are also absent. Installing
  direnv alone would turn inert files into loud failures on every `cd`
  (`devbox: command not found`, `use flake` with no nix) — strictly worse.
- The guarded hook (`command -v direnv >/dev/null 2>&1 && …`) already
  implements direnv-when-present; installing later is a one-command,
  zero-config change.
- No live consumer needs it: Tau's direnv path only matters for user projects
  with allowed `.envrc` files, and the service plane is mise-native by rule 1.

## Current audit state (2026-09-14)

- `scripts/env-boundary-check.sh` → **BOUNDARY OK**. Both project `.envrc`
  files pass: devbox (devbox-generated env: nix go/fd/git, `GOENV=off`,
  `CGO_ENABLED=0`, `$PWD/dist` PATH) and infisical (`use flake`: python312Full,
  nodejs_20, …) — mise manages neither toolchain in those scopes (global mise
  config manages only pitchfork), and neither file uses `layout`/`use mise`/
  venv activation.
- Sovereign `[env]` (`_.file = config/ports.env`, `SCOUT_*`) has no overlap
  with either `.envrc`.
- Fresh login shell: PATH zero dupes (idempotent `.bashrc.env`), mise shims
  resolve exactly once, `mise doctor` clean apart from known pre-existing
  items (mise 2026.9.7 available; missing `qdrant-server` shim).

## Shell note

`~/.bashrc.env` PATH construction was made idempotent (prepend-if-missing +
dedupe) on 2026-09-14 and verified. The file is git-ignored (`*.env`) and
there is no local sovereign-end4 checkout — the fix is live but uncommitted;
canonical repo home still to be decided.

## Implementation status (2026-09-17)

### What shipped
- `dots/.bashrc.env` (sovereign-end4) auto-loads `~/.secrets` at shell startup: 89 vars, nounset-safe, exported, never overwrites existing vars.
- `~/.config/environment.d/10-shell.conf` fixed to absolute paths so systemd user services receive `BASH_ENV` (literal `%h` was broken).
- Verified: clean noninteractive shell 4 -> 151 env vars; clean interactive shell 151 vars.

### Coverage matrix (specifications)
| Surface | Credential env | Notes |
|---|---|---|
| Interactive login shell | yes, via `.bashrc` -> `.bashrc.env` | 151 vars |
| Noninteractive bash -c / bridge exec | yes, via `BASH_ENV` -> `.bashrc.env` | 151 vars after bridge restart |
| systemd user services (new) | yes, via `environment.d` | needs `systemctl --user daemon-reload` |
| Already-running daemons (pitchfork, bridge) | no, env is a snapshot at spawn | restart required to pick up new vars |
| Gradle builds | yes, via env `GITHUB_ACTOR`/`GITHUB_TOKEN` | upstream settings reads `gpr.user`/`gpr.key` with env fallback; no tokens in files |
| Daemon/service env (rule 1) | mise / per-service config | shell loader is for shells, not daemons |

### Hard limits
- `~/.secrets` is mode 0600 and never committed (`.gitignore` token-scrub block: `*.pat`, `github_*_pat.json`, `.env*`, `*secret*`, `*token*`).
- Secret values never land in shell history, logs, or chat-visible configs; always passed ephemerally (e.g. `gh auth token`).
- Env vars are process snapshots: credential rotation requires restarting consumers.
