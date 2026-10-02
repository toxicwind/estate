# skill-frontmatter-audit

Audit and fix SKILL.md frontmatter against the SkillFrontmatter spec.

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Audits all SKILL.md files in the sovereign skills directory against the actual SkillFrontmatter interface supported by the coding-agent engine code. Fixes YAML frontmatter issues: removes quotes from `name` fields, replaces underscores with hyphens in names, converts single-line descriptions to `description: >` multi-line format, ensures `name` matches directory name, and adds `Triggers on:` keywords to descriptions.

## What It Does

- **Find all SKILL.md files**: `find skills/ -name "SKILL.md" -not -path "*/node_modules/*" -not -path "*/.github/*"`
- **Extract YAML frontmatter** and check each field against the SkillFrontmatter spec
- **Fix common issues**:
  - Remove quotes from `name` fields
  - Replace underscores with hyphens in names
  - Convert single-line descriptions to `description: >` multi-line format
  - Ensure `name` matches directory name
  - Add `Triggers on:` keywords to descriptions
- **Run the frontmatter audit script**: `bash skills/frontmatter-audit.sh`
- **Output**: All SKILL.md files with PASS/FAIL for name and description frontmatter

## Frontmatter Spec (from skill.ts)

The `SkillFrontmatter` interface in `engine/packages/coding-agent/src/capability/skill.ts` supports:

- `name`: string (lowercase, hyphenated)
- `description`: string (multi-line `description: >` format)
- `globs`: string[] (for rules, not skills)
- `alwaysApply`: boolean (for rules, not skills)
- `hide`: boolean (excludes from system prompt listing)
- `disableModelInvocation`: boolean (normalized from `disable-model-invocation`)
- `[key: string]: unknown` (any additional fields)

## Audit Script

- **Location**: `skills/frontmatter-audit.sh`
- **Usage**: `bash skills/frontmatter-audit.sh`
- **Output**: All SKILL.md files with PASS/FAIL for name and description frontmatter

## Quick Audit

```bash
# Run the audit script from the skills directory
bash skills/frontmatter-audit.sh

# Output shows each SKILL.md with PASS/FAIL for:
# - name field (lowercase, hyphenated, matches directory)
# - description field (multi-line description: > format, has Triggers on: keywords)
```

## License

Open Claw — see `skill.toml` for details.

## Security

- No credential handling; pure frontmatter validation
- Only modifies YAML frontmatter; does not change SKILL.md body content
- Audit script is read-only until fix decisions are made