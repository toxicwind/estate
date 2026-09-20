# Tau launcher (canonical)

This directory is the **single canonical source** for the `tau` launcher.
`tau audit` verifies the live install matches this copy byte-for-byte.

| File | Purpose |
|---|---|
| `tau` | The launcher: profile loading/migration, collapse chain (TAU_BIN → PATH → ./tau → dist/omp → bun src), `vendor`/`audit`/`tmux` subcommands |
| `tau-audit.sh` | `tau audit` — read-only hyper-fix audit (config, skills, engine, bridge) |
| `tau-tmux.sh` | `tau tmux` — tmux session management for parallel experiments |
| `install.sh` | Reinstall to `$HOME/.local/bin` (default) — the durable reinstall path |
| `bin/test-collapse.sh` | Collapse-chain tests, run against this copy |
| `profiles/` | Stock profiles (`default.yml`, `kimi.yml`); user profiles live in `~/.tau/profiles/` |

Install: `./install.sh` (or `./install.sh --prefix /usr/local` for system-wide).
Never edit the installed copy in `~/.local/bin` directly — change this repo copy,
reinstall, and commit.
