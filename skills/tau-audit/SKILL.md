---
name: tau-audit
description: "Run the complete tau audit suite: tau-audit.sh (15 checks), tau-tmux audit.ts (7 checks), and frontmatter-audit.sh (69 SKILL.md files). All pass means the environment is clean."
---

# tau-audit Skill

Run all three audit suites to verify the tau environment is clean.

## Commands

```bash
# Full audit suite
bash ~/.local/bin/tau-audit.sh                          # 16 checks: config, skills, engine, bridge, drift
bun run ~/sovereign/skills/tau-tmux/helper/audit.ts     # 7 checks: launcher, version, routers
bash ~/sovereign/skills/scripts/frontmatter-audit.sh    # 69 SKILL.md frontmatter checks
```

## Expected Results
- tau-audit.sh: **16/16 checks passed** (16th: live agent config matches the committed blob -- ~/.tau/agent is bind-mounted to config/tau/agent, so only the git blob is a real baseline; catches session model-switch clobbering)
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
7. **Live config clobbered (drift check)**: a running session persisted a model switch into
   `~/.tau/agent/config.yml`. Diff against the committed blob
   (`git show HEAD:config/tau/agent/config.yml`); the working-tree copy is bind-mounted
   to the live file, so it can never serve as the baseline. Restore with
   `git checkout -- config/tau/agent/config.yml` only after confirming the session
   intent, then re-run the audit.

## Key Paths
- Config: `~/.tau/config.yml` (live default model: `modelRoles.default` in `~/.tau/agent/config.yml`)
- Skills: `~/.tau/skills` -> `~/sovereign/skills`
- Launcher source: `~/sovereign/scripts/omp-pin` (installed: `~/.local/bin/tau`, `~/.local/bin/omp`)
- Engine: bun-global `@oh-my-pi/pi-coding-agent` (`~/.bun/install/global/node_modules/...`)
- Extensions: `~/.tau/extensions/` (vansrouter.ts, strict-bash-guard.ts)
- Bridge port: 25204 (pitchfork-managed)
- Audit scripts: `~/sovereign/scripts/tau-audit.sh`, `skills/tau-tmux/helper/audit.ts`, `skills/scripts/frontmatter-audit.sh`
