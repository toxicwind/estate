# tau-audit

**Run the complete tau audit suite** – verify the environment is clean with three complementary checks: tau-audit.sh (16 checks), tau-tmux audit.ts (7 checks), and frontmatter-audit.sh (68 SKILL.md frontmatter checks).

## Why This Matters

A tau environment that has drifted, corrupted session configs, or inconsistent SKILL.md frontmatter can lead to:
- Model switch persistence in live agent config
- Broken launcher scripts or missing binaries
- Missing or malformed metadata across the skill set

This skill catches all of the above and ensures the environment stays baseline‑clean.

## Audit Suites

### 1. `tau-audit.sh` – 15 Checks

Runs `~/.local/bin/tau-audit.sh`, which validates:
- Configuration consistency
- Skills symlink integrity
- Engine and launcher detection
- Bridge availability
- Drift detection against committed blobs
- Session model‑switch clobbering prevention

**Expected:** 15/16 checks passed (the 16th checks live agent config matches the committed blob, bind‑mounted to config/tau/agent).

### 2. `tau-tmux audit.ts` – 7 Checks

Runs `bun run ~/sovereign/skills/tau-tmux/helper/audit.ts`, covering:
- Launcher correctness
- Version verification
- Router routing integrity

**Expected:** 7/7 checks passed.

### 3. `frontmatter-audit.sh` – 68 Checks

Runs `bash ~/sovereign/skills/scripts/frontmatter-audit.sh`, validating that every SKILL.md carries proper frontmatter:
- `name: slug-name` (no quotes/underscores)
- `description: >` (multi‑line when needed)
- `Triggers on:` keywords present

**Expected:** 68 pass, 0 fail.

## Quick Start

```bash
# Run the full audit suite
bash ~/.local/bin/tau-audit.sh
bun run ~/sovereign/skills/tau-tmux/helper/audit.ts
bash ~/sovereign/skills/scripts/frontmatter-audit.sh
```

### Interpreting Results

- **All suites green** – Environment is clean; no remediation needed.
- **Any failures** – Follow the **Common Fixes** section below to resolve each issue.

## Common Fixes

| Issue | Fix |
|-------|-----|
| **TAU_HOME path issues** | Ensure `TAU_HOME` defaults to `$HOME/.tau` not `$HOME`. |
| **tau command broken** | Reinstall from repo script: `install -m 0555 ~/sovereign/scripts/omp-pin ~/.local/bin/tau ~/.local/bin/omp`. |
| **Launcher detection** | `tau` is a bash pin script (not ELF); it execs the bun‑global `@oh-my-pi/pi-coding-agent` install. |
| **Frontmatter** | All SKILL.md must carry `name: slug-name` and `description:` frontmatter. |
| **Bridge not running** | Start: `pitchfork start awrawr-ws-exec`. |
| **Skills symlink missing** | `ln -sf ~/sovereign/skills ~/.tau/skills`. |
| **Live config clobbered (drift check)** | Diff against committed blob: `git show HEAD:config/tau/agent/config.yml`. Restore with `git checkout -- config/tau/agent/config.yml` after confirming session intent. |

## Key Paths

| Path | Purpose |
|------|---------|
| `~/.tau/config.yml` | Live default model config |
| `~/.tau/skills` → `~/sovereign/skills` | Skills symlink |
| `~/sovereign/scripts/omp-pin` | Launcher source (installed as `~/.local/bin/tau`, `~/.local/bin/omp`) |
| `~/sovereign/projects/tau/engine/packages/coding-agent/dist/tau` | Binary |
| `~/sovereign/projects/tau/launcher/tau` | Launcher symlink |
| Bridge port `25204` | pitchfork‑managed WS endpoint |
| Audit scripts | `~/s/.local/bin/tau-audit.sh`, `skills/tau-tmux/helper/audit.ts`, `scripts/frontmatter-audit.sh` |

## Configuration

- **Default model** – Set in `~/.tau/config.yml` (`modelRoles.default`) and `~/.tau/agent/config.yml`.
- **Skill symlink** – Must point to `~/sovereign/skills`; missing link causes many audit failures.
- **Bridge** – Ensure pitchfork is running with `pitchfork start awrawr-ws-exec`.

## Development & Contributing

- **Add new checks** – Extend audit scripts with clear expectations and add frontmatter where applicable.
- **Fix drifts** – Resolve config mismatches before committing changes.
- **Testing** – Run the full suite after any environment change.

## License & Support

- **License** – See the project's LICENSE file for details.
- **Support** – Open issues or tickets for audit failures in the main repository.

## Status

Version: **0.1.0**
Last updated: 2026-10-02

## Related Projects

- [fix-omp-launcher](fix-omp-launcher/)
- [fix-tau-session-corruption](fix-tau-session-corruption/)
- [gatehouse-mcp](gatehouse-mcp/)
- [router](router/)
- [tau-binary-build](tau-binary-build/)
- [tau-fork-pinning](tau-fork-pinning/)
- [zipfs-vault](zipfs-vault/)