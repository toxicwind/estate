# skillmd-examples

> A collection of real-world SKILL.md examples and installation guides for AI coding tools.

A **SKILL.md** is a structured profile that tells AI tools who you are — your skills, experience, and how you work. When you add one to your environment, tools like Claude Code, VS Code Copilot, Cursor, and Codex give you better, more relevant output from the first message.

This repo contains:

- **Example SKILL.md files** for different roles
- **Installation guides** for the major AI coding tools
- Everything you need to hand-write your own

Need one generated automatically from your CV? Try [skillmdcreator.ai](https://skillmdcreator.ai) — it builds a personalised SKILL.md in 60 seconds from your CV, a job description, or a short form.

---

## Examples

| Role | File |
|------|------|
| Full-Stack Engineer | [examples/fullstack-engineer.md](examples/fullstack-engineer.md) |
| Data Analyst | [examples/data-analyst.md](examples/data-analyst.md) |
| Product Manager | [examples/product-manager.md](examples/product-manager.md) |
| Marketing Director | [examples/marketing-director.md](examples/marketing-director.md) |
| UX Designer | [examples/ux-designer.md](examples/ux-designer.md) |

## Installation guides

| Tool | Guide |
|------|-------|
| Claude Code | [guides/claude-code.md](guides/claude-code.md) |
| VS Code Copilot | [guides/vscode-copilot.md](guides/vscode-copilot.md) |
| Cursor | [guides/cursor.md](guides/cursor.md) |
| OpenAI Codex | [guides/codex.md](guides/codex.md) |

---

## What is a SKILL.md?

SKILL.md files follow the **Agent Skills open standard** — a YAML frontmatter block plus markdown content that any compatible AI tool can load as context.

```markdown
---
name: your-profile-name
description: When to load this skill (used by AI tools to decide)
---

# Your Name — Role

## Expertise areas
- Skill 1
- Skill 2

## How you work
- Preference 1
- Preference 2
```

The `description` field is important — AI tools read it to decide when to activate the skill. Make it specific about when the profile should be loaded.

### Where to put it

- **Claude Code**: `~/.claude/skills/your-skill.md` (personal) or `.claude/skills/your-skill.md` (project)
- **VS Code Copilot**: `.agents/skills/your-skill.md` in your project
- **Cursor**: `.cursor/skills/your-skill.md` in your project
- **Any AI chat**: paste the content directly as context

See the [installation guides](guides/) for step-by-step setup.

---

## Writing your own

1. Pick the example closest to your role
2. Copy it and replace every section with your own details
3. Be specific — "5 years React, focused on complex SPAs" beats "JavaScript"
4. Include preferences — how you like to work, what you avoid, your tooling
5. Save it to the right folder for your AI tool

### Tips

- **Be specific about experience**: years, scale, specific projects
- **Name your tools**: exact versions and libraries you use
- **State your preferences**: what you like, what you avoid, decision criteria
- **Keep it scannable**: AI tools read markdown well; use bullets and headers
- **Don't exaggerate**: the file is for the AI to help you, not a sales pitch

---

## Generate one automatically

Writing a good SKILL.md from scratch takes an hour and most people understate their experience.

[**skillmdcreator.ai**](https://skillmdcreator.ai) reads your CV (or a job description, or a short form) and produces a structured SKILL.md in 60 seconds — following the same patterns as the examples here but tailored to your actual background.

- Free preview before you pay
- $9 one-time for the full file
- $15 Pro for two persona variants
- GDPR compliant, data deleted after generation

---

## Contributing

Got a great SKILL.md for a role not covered here? Open a PR. Examples should be:

- Realistic (not aspirational fantasy)
- Specific (named tools, real years, actual preferences)
- Generic enough that others in the role will recognise themselves

## License

MIT — use these examples however you like.