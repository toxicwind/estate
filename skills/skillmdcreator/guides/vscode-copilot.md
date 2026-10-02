# Using SKILL.md with VS Code Copilot

GitHub Copilot in VS Code supports the Agent Skills standard via the `.agents/skills/` folder in your workspace. Skills loaded this way provide context for Copilot Chat and inline suggestions.

## Installation

Skills are **project-scoped** in VS Code Copilot — they live inside the workspace rather than a global user folder.

### Step-by-step

1. Open your project in VS Code.

2. Create the skills directory:

   ```bash
   mkdir -p .agents/skills
   ```

3. Save your SKILL.md file:

   ```bash
   mv ~/Downloads/your-skill.md .agents/skills/
   ```

4. Reload the VS Code window (`Cmd/Ctrl + Shift + P` → "Developer: Reload Window"). The skill is now available to Copilot Chat.

## Global profile across projects

Because Copilot loads skills per-project, you have two options for a personal profile:

**Option A — copy it into each project** (simple, works everywhere)

```bash
cp ~/my-skill.md /path/to/project/.agents/skills/
```

**Option B — add it to your dotfiles** and symlink it into each project

```bash
ln -s ~/dotfiles/my-skill.md .agents/skills/my-skill.md
```

Option B is cleaner if you maintain many projects and want to update your profile in one place.

## Verifying it works

Open Copilot Chat and ask:

```
What do you know about my background and preferences?
```

If Copilot responds with details from your SKILL.md, it loaded correctly.

## Excluding from version control

If your SKILL.md contains personal details you don't want committed to the repo, add it to `.gitignore`:

```
# .gitignore
.agents/skills/my-personal-profile.md
```

Or ignore the whole `.agents/` directory if skills are personal per-developer:

```
.agents/
```

For team-wide skills (e.g. project conventions), commit them to the repo so the whole team benefits.

## Related docs

- [VS Code Agent Skills documentation](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [Agent Skills open standard](https://agentskills.io)
- [Generate a SKILL.md automatically](https://skillmdcreator.ai)