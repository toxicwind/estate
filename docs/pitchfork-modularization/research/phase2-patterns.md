# Phase 2 — Config-modularization pattern borrow
Magpie · 2026-09-30 · GitHub-wide ranked search + upstream verdict

## Ranked hits

Ranked by recency + relevance (Chris's rule). Every mechanism below was read
in the actual implementation, not just the README.

### 1. systemd drop-ins — systemd/systemd (16.8k★, pushed 2026-09-30)
<https://github.com/systemd/systemd>
`src/shared/conf-parser.c`, `config_parse_many_files()`: pins and fstats every
drop-in first, dedupes by inode (symlink-aware — a main file symlinked as a
drop-in is read only once), reads the main unit file, then all
`unit.service.d/*.conf` drop-ins in sorted filename order; later keys override
earlier ones. Precedence is lexical filename across dirs (`/etc` beats `/usr`
via separate dir search order). Hot-reload: none automatic — `daemon-reload`
re-parses everything. Multi-writer: each package owns its own file; writers
must write atomically (tmp + rename); there is no in-config locking.

### 2. supervisord `[include]` — Supervisor/supervisor (9.1k★, pushed 2025-12-21)
<https://github.com/Supervisor/supervisor>
`supervisor/options.py:582-611`: an `[include]` section with a `files` setting
holding whitespace-separated glob patterns, resolved relative to the main
config file's directory, globbed, **sorted**, and read into the same
ConfigParser in order — later files override earlier sections. No match is a
warning, not an error. `%(here)s` is rebased per included file; included files
cannot themselves include. Hot-reload granularity: `reread` (parse/validate
only) + `update` (restart only changed) — explicit two-phase with a daemon
diff. Multi-writer: none built-in; includes exist precisely so packagers own
separate files instead of fighting over one.

### 3. docker compose multi-file merge — docker/compose (38.3k★) + compose-spec/compose-go (pushed 2026-09-29)
<https://github.com/docker/compose> <https://github.com/compose-spec/compose-go>
Explicit ordered file list (`-f base.yml -f override.yml`, `COMPOSE_FILE`,
auto `compose.override.yml`). `override/merge.go` `MergeYaml`: a per-path
strategy registry (`mergeSpecials`). Default: mappings deep-merge with the
override winning per key, sequences `appendWithoutDuplicates`, scalars
override. Specials: `command`/`entrypoint`/`healthcheck.test` = full replace;
env/labels = key-value merge. Hot-reload: `up` re-merges; watch mode exists.
Multi-writer: each file owned separately; order is explicit on the command
line, so precedence is never ambiguous.

### 4. k3s `config.yaml.d` — k3s-io/k3s (34k★, pushed 2026-09-28)
<https://github.com/k3s-io/k3s>
`pkg/configfilearg/parser.go`, `dotDFiles()`: reads `<config>.d/*.yaml|*.yml`
via `os.ReadDir` (lexical order), appended after the main `config.yaml`; the
main file or at least one drop-in must exist. Simple last-wins merge.
Hot-reload: none — read at startup, restart required. Multi-writer: lexical
filename = precedence control (`00-base.yaml`, `99-local.yaml`).

### 5. runsvdir directory-of-services — g-pape/runit (pushed 2026-09-30)
<https://github.com/g-pape/runit>
No config file at all: one subdirectory (or symlink to a directory) per
service in a scan dir. `runsvdir` re-scans at least every 5s when the dir's
mtime/inode changes, starts a `runsv` per new entry (max 1000, dot-names
skipped), sends TERM when an entry disappears. Precedence: N/A — one service
per directory entry, no merging, no conflicts by construction. Hot-reload:
inherent — symlink in a dir and the service starts within 5s. Multi-writer:
perfect — ownership is by directory entry, there is no shared file.

### Negative results (verified, not assumed)
- overmind (DarthSim/overmind, 3.7k★, pushed 2025-04-04): single `Procfile`,
  no include mechanism.
- pm2: single ecosystem file, no include mechanism.
- Conclusion: among process supervisors, supervisord's `[include]` is the
  exception — conf.d-style splitting is a systemd/k3s idiom, not a supervisor
  idiom. Nobody has a per-field merge-strategy table except compose.

## pitchfork upstream verdict

- Upstream: <https://github.com/jdx/pitchfork>. Latest release **v2.29.0**
  (2026-09-29); we run **2.25.0** — 4 versions behind.
- **No include / drop-in / conf.d / extends mechanism exists in any version
  through 2.29.0.** Verified three ways: (a) the 1595-line config reference
  contains zero occurrences of "include", "drop-in", or "extends"; (b) the
  CHANGELOG 2.25.0→2.29.0 adds nothing config-composition-shaped (argv-array
  run, oneshot, cron-status, proxy hostnames — no includes); (c) `gh search
  issues -R jdx/pitchfork` for include/conf.d/drop-in returns zero open and
  zero closed issues. `pitchfork --help` (2.25.0, verbatim): no include flags;
  the closest subcommand is `config  Attach externally generated configuration
  to a project.`
- What natively exists: a **directory-hierarchy** merge (system config
  `/etc/pitchfork/config.toml` → user `~/.config/pitchfork/config.toml` →
  per-directory `.config/pitchfork.toml` → `.config/pitchfork.local.toml` →
  `pitchfork.toml` → `pitchfork.local.toml`, later wins) — per-directory, not
  per-file.
- 2.25.0 added **external config attachments**
  (`pitchfork config add <file> --dir <project>`, plus `PITCHFORK_CONFIG` env
  path list): generated files attached per project, registered attachments
  override ordinary project files, ancestor attachments load before child ones,
  files within an entry load in listed order. Registered under
  `[namespaces.<ns>] config=[...]` in the user global config. Designed for
  generated files, not hand-written drop-ins — but it is the closest native
  hook and the natural sink for a generated merged config.
- Upgrading 2.25.0→2.29.0 does **not** change any of this — verified precisely
  above. A conf.d mechanism must be built on top (generator → attachment, or
  pre-merge before pitchfork reads), or petitioned upstream.

## Borrow recommendations

Cross-cutting steals (apply to all three designs):
- **Precedence = lexical filename order** (systemd, supervisord, k3s all agree).
  Use `NN-name.toml` prefixes (`00-base`, `50-team`, `99-local`).
- **Hot-reload granularity = supervisord's two-phase**: parse+validate all
  fragments (report per-file errors, never a partial merge) → diff daemons →
  restart only changed. Never restart the world on one file's edit.
- **Multi-writer safety = one-writer-per-file + atomic rename + a single
  serialized apply step** (systemd's discipline). No locking inside the files.
- **Empty-glob is a warning, not an error** (supervisord's idiom).

### Design A — pitchfork.d drop-ins merged at load
Steal **systemd's drop-in discipline + k3s's naming + supervisord's loader**:
`pitchfork.d/*.toml`, main `pitchfork.toml` first, then drop-ins in sorted
filename order, deep-merge `[daemons.<name>]` tables (later wins per key),
`[settings]`/`[env]` merged the same way. Loader: glob → sort → parse each →
validate → merge → hand one merged doc to pitchfork (via `PITCHFORK_CONFIG` or
attachment). Daemon-per-file is the recommended granularity; multi-daemon
files allowed but discouraged.

### Design B — generated config from per-daemon manifests
Steal **runsvdir's directory-of-services model**: `daemons.d/<name>.toml`, one
manifest per daemon — no merge conflicts by construction for daemons; only
shared `[settings]`/`[env]` need a merge (use design A's rules for those).
New file = new daemon with no reload dance; deleted file = daemon removed.
Feed the generated merged file to pitchfork through its **native**
`pitchfork config add` attachment (2.25.0+) — zero new code on the pitchfork
side, and pitchfork already re-discovers attachments for cron/hooks/watches/
proxy auto-start. Generator must write atomically (tmp + rename); pitchfork's
mtime-based config cache picks it up.

### Design C — mise.local.toml fragments composed upward
Steal **compose's per-path merge-strategy table** (`mergeSpecials`): don't use
one global merge rule. Default: mappings deep-merge (later fragment wins per
key), sequences append-with-dedup, scalars override; special-case fields that
must fully replace (`run`, `command`-like strings) vs fields that merge
(`env`, labels). Compose fragments in directory order (root → leaf, mirroring
pitchfork's existing hierarchy); keep the strategy table explicit and
documented, not implicit. This is the only design where per-field strategies
matter — A and B can stay last-wins.
