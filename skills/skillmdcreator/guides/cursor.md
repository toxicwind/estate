# Using SKILL.md with Cursor

[Cursor](https://cursor.com) supports the Agent Skills standard alongside its native `.cursorrules` format. You can use a SKILL.md in Cursor the same way you would in any Agent Skills-compatible tool.

## Installation

Skills live in `.cursor/skills/` inside your project:

```bash
mkdir -p .cursor/skills
mv ~/Downloads/your-skill.md .cursor/skills/
```

Restart Cursor or reload the window. Cursor will pick up the skill on next activation.

## SKILL.md vs `.cursorrules`

Cursor has two context mechanisms and they solve different problems:

| | SKILL.md | .cursorrules |
|---|---|---|
| **Purpose** | Who you are, how you work | Project-specific rules |
| **Scope** | Personal (portable across tools) | Project-specific |
| **Format** | Agent Skills standard (markdown + YAML) | Plain text rules |
| **Portability** | Works with Claude Code, Copilot, Codex too | Cursor-only |

If you want your context to work in multiple AI tools, prefer SKILL.md. If it's strictly Cursor-specific rules (e.g. "always use the project's custom test runner"), `.cursorrules` is fine.

You can use both simultaneously — they don't conflict.

## Personal profile across projects

Cursor loads skills per-project, so your personal profile needs to be available in every project. Two approaches:

**Symlink from a central location** (recommended):

```bash
mkdir -p ~/dotfiles
mv my-skill.md ~/dotfiles/
cd /path/to/any/project
mkdir -p .cursor/skills
ln -s ~/dotfiles/my-skill.md .cursor/skills/my-skill.md
```

**Script it** — add a one-liner to your shell profile that sets it up for new projects automatically.

## Gitignore recommendation

Personal skills shouldn't be committed to project repos. Add to `.gitignore`:

```
.cursor/skills/my-personal-profile.md
```

Or ignore the whole folder if skills are always personal:

```
.cursor/skills/
```

## Verifying it works

Open Cursor Chat (`Cmd/Ctrl + L`) and ask:

```
What do you know about my preferences and background?
```

If Cursor mentions details from your SKILL.md, it loaded correctly.

## Related docs

- [Cursor documentation](https://docs.cursor.com)
- [Agent Skills open standard](https://agentskills.io)
- [Generate a SKILL.md automatically](https://skillmdcreator.ai)