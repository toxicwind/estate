# Using SKILL.md with OpenAI Codex CLI

OpenAI's [Codex CLI](https://github.com/openai/codex) adopted the Agent Skills open standard shortly after Anthropic published it. Codex reads skills from the standard skills folder structure.

## Installation

Codex looks for skills in:

- **Personal (global)**: `~/.codex/skills/your-skill.md`
- **Project-specific**: `.codex/skills/your-skill.md` in your workspace

### Step-by-step

1. Create the skills directory:

   ```bash
   mkdir -p ~/.codex/skills
   ```

2. Save your SKILL.md file:

   ```bash
   mv ~/Downloads/your-skill.md ~/.codex/skills/
   ```

3. Restart Codex or start a new session. The skill is loaded based on its description.

## Multiple AI tools, one profile

If you use Claude Code, Copilot, Cursor, and Codex, you don't need to maintain four different profile files. Keep one SKILL.md in a central location and symlink it:

```bash
# Central location
mkdir -p ~/dotfiles
cp ~/my-skill.md ~/dotfiles/

# Symlink into each tool's folder
ln -s ~/dotfiles/my-skill.md ~/.claude/skills/my-skill.md
ln -s ~/dotfiles/my-skill.md ~/.codex/skills/my-skill.md
```

Edit `~/dotfiles/my-skill.md` and every tool picks up the change.

## Verifying it works

Ask Codex something about your profile:

```
What do you know about my stack and working preferences?
```

If Codex responds with details from your SKILL.md, it loaded correctly.

## Related docs

- [Codex CLI on GitHub](https://github.com/openai/codex)
- [Agent Skills open standard](https://agentskills.io)
- [Generate a SKILL.md automatically](https://skillmdcreator.ai)