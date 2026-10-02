# Skill Creator

&larr; **Back to top** <!-- for-the-badge alignment -->

## Badges

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## Hero

A Claude skill that creates other Claude skills. Add it to your environment and Claude learns how to build production-quality skills from scratch. Skills are reusable instruction sets that teach Claude how to perform specific tasks consistently — think of them as programming Claude's behavior using precise natural language, where the LLM is the interpreter and the skill is the source code.

## What This Skill Does

- **Skill creation**: Generate production-quality skills from intent capture through testing and packaging
- **Three-level loading**: Metadata (name + description in YAML frontmatter) always in context; SKILL.md body loaded when skill triggers; resources (scripts, references, assets) loaded on-demand
- **Description as trigger**: The skill description is the primary mechanism — Claude decides whether to activate a skill based on how well the description matches the user's request
- **Progressive disclosure**: Manage context efficiently across three levels of disclosure
- **Undertriggering prevention**: Teach Claude to write "pushy" descriptions that explicitly list trigger phrases, scenarios, and exclusions

## Features

| Feature | Detail |
|---|---|
| **Three-level loading** | Metadata always in context; SKILL.md body when triggered; resources on-demand |
| **Description triggers** | Description determines if/when a skill activates; explicit trigger phrases prevent undertriggering |
| **User-level or project-level** | Skills can be user-level (available across all projects) or project-level (scoped) |
| **Copy-paste production code** | Generated skills include StateGraph architecture, ReAct agent loops, tool binding patterns, state persistence, and iteration control |
| **Brand voice preservation** | Skills capture tone, structure preferences, vocabulary, and formatting standards for consistent content |
| **API style guide consistency** | Skills ensure consistent API design across teams with naming conventions, error handling, authentication, and versioning |

## Quick Start

```bash
# Create a user-level skill (available across all projects)
/skill-creator --user "Analytics with DuckDB"

# Create a project-level skill (scoped to current project)
/skill-creator --project "Analytics with DuckDB"

# Or via CLI
git clone git@github.com:somasays/skill-creator.git ~/.claude/skills/skill-creator
```

## Config

- Works best as a **user-level skill** — available across all your conversations and projects
- Claude Desktop App: Settings → Capabilities → Add skills; upload skill folder containing `SKILL.md` and supporting files
- Claude Code (CLI): `git clone git@github.com:somasays/skill-creator.git ~/.claude/skills/skill-creator`
- Use `/skill-creator --user "name"` for user-level or `/skill-creator --project "name"` for project-level

## Contributing

Found patterns that make skills better? PRs welcome. This skill works best when descriptions are explicit about triggers, secondary scenarios, and exclusions — helping Claude activate the right skill at the right time.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

## Security

- No credential handling; skill creation is pure instructional design
- Generated skills should follow the same security review process as any Claude-deployed code
- Descriptions should not contain sensitive or restricted content