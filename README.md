# Sovereign Stack — Mise 2026 Configuration

## What changed from the old shell-script approach

| Before (2023-style) | After (2026 mise) |
|---|---|
| `stack/ports.env` | `[env]` in `mise.toml` |
| `stack/profiles.sh` | `pc_args()` in `mise/tasks/_lib.sh` |
| `stack/lib.sh` | `mise/tasks/_lib.sh` |
| `stack/up.sh`, `down.sh`, `health.sh`, `build-compose.sh` | `mise/tasks/*` (file-based tasks) |
| `_.file` / `_.path` (deprecated) | `env._.file` / `env._.path` (current) |
| Hardcoded `/home/toxic` | `{{ env.HOME }}` / `{{ config_root }}` |
| No tool pinning | `[tools]` pins process-compose, python, jq |

## Files to DELETE from `stack/`

```bash
rm stack/{up.sh,down.sh,health.sh,build-compose.sh,lib.sh,profiles.sh,ports.env}
```

Keep in `stack/`:
- `base.yaml`
- `modules/*.yaml`
- `services/*.sh` (llama-herder.sh, rust-web.sh — these are service entrypoints, not orchestration)

## Commands

```bash
mise trust
mise install          # installs process-compose, python, jq
mise run build-compose
mise run up           # sovereign profile
mise run up-core      # minimal
mise run up-full      # everything
mise run health
mise run down
```

## Task discovery

```bash
mise tasks            # list all tasks
mise tasks --all      # including hidden/file-based
```

## File-based task convention

- Scripts live in `mise/tasks/`
- The filename IS the task name (`up`, `health`, etc.)
- Descriptions via `# MISE description="..."` comment
- Must be executable (`chmod +x`)
- Directory nesting becomes colons: `mise/tasks/db/migrate` → `mise run db:migrate`

## Env loading order

1. `[env]` in `mise.toml` (ports, URLs)
2. `env._.file` → `.env.local`, `~/.secrets`, `~/.openfang/secrets.env`
3. `env._.path` → adds bin directories to PATH
4. Task scripts inherit everything

## Secrets

- `.env.local` — project-local non-secrets (can be in git)
- `~/.secrets` — machine-local secrets (never in git)
- `~/.openfang/secrets.env` — openfang-specific secrets
- All marked with `redact = true` so values are masked in logs
