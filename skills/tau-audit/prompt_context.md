# tau-audit Skill

Run all three audit suites to verify the tau environment is clean.

## Commands

```bash
# Full audit suite
bash ~/.local/bin/tau-audit.sh          # 15 checks: config, skills, engine, bridge
bun run ~/sovereign/skills/tau-tmux/helper/audit.ts  # 7 checks: launcher, version, routers
bash ~/sovereign/skills/frontmatter-audit.sh          # 68 SKILL.md frontmatter checks
```

## Expected Results
- tau-audit.sh: **15 pass, 0 warn, 0 fail**
- tau-tmux audit.ts: **7/7 checks passed**
- frontmatter-audit.sh: **68 pass, 0 fail**

## Common Fixes
If audits fail:
1. **TAU_HOME path issues**: Ensure TAU_HOME defaults to `$HOME/.tau` not `$HOME`
2. **Binary path**: tau binary is at `engine/packages/coding-agent/dist/tau` (not `tau`)
3. **Launcher detection**: tau is an ELF binary, use `file -b` not string grep for detection
4. **Frontmatter**: All SKILL.md must use `name: slug-name` (no quotes/underscores), `description: >` (multi-line), and `Triggers on:` keywords
5. **Bridge not running**: `pitchfork start awrawr-ws-exec`
6. **Skills symlink missing**: `ln -sf ~/sovereign/skills ~/.tau/skills`

## Key Paths
- Config: `~/.tau/config.yml`
- Skills: `~/.tau/skills` → `~/sovereign/skills`
- Binary: `~/sovereign/projects/tau/engine/packages/coding-agent/dist/tau`
- Launcher: `~/sovereign/projects/tau/launcher/tau` (symlink to binary)
- Bridge port: 25204 (pitchfork-managed)
- Audit scripts: `~/.local/bin/tau-audit.sh`, `skills/tau-tmux/helper/audit.ts`, `skills/frontmatter-audit.sh`