# Skill Frontmatter Audit

## Purpose
Audit all SKILL.md files in the sovereign skills directory against the actual SkillFrontmatter interface supported by the coding-agent engine code.

## Frontmatter Spec (from skill.ts)
The `SkillFrontmatter` interface in `engine/packages/coding-agent/src/capability/skill.ts` supports:
- `name`: string (lowercase, hyphenated)
- `description`: string (multi-line `description: >` format)
- `globs`: string[] (for rules, not skills)
- `alwaysApply`: boolean (for rules, not skills)
- `hide`: boolean (excludes from system prompt listing)
- `disableModelInvocation`: boolean (normalized from `disable-model-invocation`)
- `[key: string]: unknown` (any additional fields)

## Procedure
1. Find all SKILL.md files: `find skills/ -name "SKILL.md" -not -path "*/node_modules/*" -not -path "*/.github/*"`
2. Extract YAML frontmatter and check each field against the spec
3. Fix any issues:
   - Remove quotes from `name` fields
   - Replace underscores with hyphens in names
   - Convert single-line descriptions to `description: >` multi-line format
   - Ensure `name` matches directory name
   - Add `Triggers on:` keywords to descriptions
4. Run the frontmatter audit script: `bash skills/frontmatter-audit.sh`

## Audit Script
Location: `skills/frontmatter-audit.sh`
Usage: `bash skills/frontmatter-audit.sh`
Output: All SKILL.md files with PASS/FAIL for name and description frontmatter.