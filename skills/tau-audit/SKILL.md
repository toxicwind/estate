---
name: tau-audit
description: "Run the complete tau audit suite: tau-audit.sh (15 checks), tau-tmux audit.ts (7 checks), and frontmatter-audit.sh (69 SKILL.md files). All pass means the environment is clean."
---

# tau-audit Skill

Run all three audit suites to verify the tau environment is clean.

## Commands

```bash
# Full audit suite
bash ~/.local/bin/tau-audit.sh                          # 15 checks: config, skills, engine, bridge
bun run ~/sovereign/skills/tau-tmux/helper/audit.ts     # 7 checks: launcher, version, routers
bash ~/sovereign/skills/scripts/frontmatter-audit.sh    # 69 SKILL.md frontmatter checks
```

## Expected Results
- tau-audit.sh: **15/15 checks passed**
- tau-tmux audit.ts: **7/7 checks passed**
- frontmatter-audit.sh: **69 pass, 0 fail**

## Common Fixes
If audits fail:
1. **TAU_HOME path issues**: Ensure TAU_HOME defaults to `$HOME/.tau` not `$HOME`
2. **tau command broken**: `tau`/`omp`/`pi` are aliases to `~/.local/bin/tau`, which is the
   `~/sovereign/scripts/omp-pin` launcher. Reinstall from the repo script if missing:
   `install -m 0555 ~/sovereign/scripts/omp-pin ~/.local/bin/tau ~/.local/bin/omp`
3. **Launcher detection**: tau is a bash pin script (not ELF); it execs the bun-global
   `@oh-my-pi/pi-coding-agent` install. Never fall through to a random omp on PATH.
4. **Frontmatter**: All SKILL.md must carry `name: slug-name` and `description:` frontmatter
   (see `skills/scripts/frontmatter-audit.sh`).
5. **Bridge not running**: `pitchfork start awrawr-ws-exec`
6. **Skills symlink missing**: `ln -sf ~/sovereign/skills ~/.tau/skills`

## Key Paths
- Config: `~/.tau/config.yml` (live default model: `modelRoles.default` in `~/.tau/agent/config.yml`)
- Skills: `~/.tau/skills` -> `~/sovereign/skills`
- Launcher source: `~/sovereign/scripts/omp-pin` (installed: `~/.local/bin/tau`, `~/.local/bin/omp`)
- Engine: bun-global `@oh-my-pi/pi-coding-agent` (`~/.bun/install/global/node_modules/...`)
- Extensions: `~/.tau/extensions/` (vansrouter.ts, strict-bash-guard.ts)
- Bridge port: 25204 (pitchfork-managed)
- Audit scripts: `~/sovereign/scripts/tau-audit.sh`, `skills/tau-tmux/helper/audit.ts`, `skills/scripts/frontmatter-audit.sh`
