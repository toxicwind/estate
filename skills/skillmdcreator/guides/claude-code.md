# Using SKILL.md with Claude Code

[Claude Code](https://claude.com/claude-code) is Anthropic's official CLI and IDE integration for Claude. It has native support for the Agent Skills standard — drop a SKILL.md file in the right folder and Claude automatically loads it when relevant.

## Installation

Claude Code looks for skills in two places:

- **Personal (global)**: `~/.claude/skills/your-skill.md` — loaded in every project
- **Project-specific**: `.claude/skills/your-skill.md` — only loaded in that project

For a personal profile (who you are, how you work), use the global path. For project-specific context, use the project path.

### Step-by-step

1. Create the skills directory if it doesn't exist:

   ```bash
   mkdir -p ~/.claude/skills
   ```

2. Save your SKILL.md file:

   ```bash
   mv ~/Downloads/your-skill.md ~/.claude/skills/
   ```

3. Start or restart Claude Code. The skill is loaded automatically based on its `description` field — Claude reads the description to decide when to activate it.

## How Claude Code uses the description

The `description` in your YAML frontmatter is not just a label — it's an instruction telling Claude *when* to load the skill. Be specific:

**Good:**
```yaml
description: Load when working on React, Node.js, or API design for web applications. Use for code reviews, architecture decisions, and debugging full-stack issues.
```

**Too vague:**
```yaml
description: About me
```

With a specific description, Claude activates the skill contextually — e.g. when you open a React project or ask about API design — without you having to do anything.

## Verifying it works

Ask Claude Code something directly related to your profile:

```
What do you know about my stack and preferences?
```

If Claude responds with details from your SKILL.md, it loaded correctly. If not, check that:

- The file is in `~/.claude/skills/` (not `~/.claude/` directly)
- The YAML frontmatter is valid (no tabs, `---` on both sides)
- The `description` field is present and specific

## Multiple skills

You can have multiple SKILL.md files — for example, one for your engineering work and one for a side project. Claude Code will load the right one based on context:

```
~/.claude/skills/
├── engineering-profile.md
├── side-project-startup.md
└── writing-style.md
```

## Related docs

- [Official Claude Code docs](https://code.claude.com/docs/en/skills)
- [Agent Skills open standard](https://agentskills.io)
- [Generate a SKILL.md automatically](https://skillmdcreator.ai)