# sovereign-skills

Skill definitions, agent recipes, and behavioral conventions for the Sovereign
ecosystem — consumed by Pi, Tau, and subagents. Keep definitions atomic,
self-contained, and deterministic.

See `AGENTS.md` for the repo rules: verify live before claiming, fail loud
(never silence errors), prefer `fd`/`rg` over `find`/`grep`.

## Contents

| Path             | What it is                                                                                  |
| ---------------- | --------------------------------------------------------------------------------------------- |
| `engine-audit.ts`| Audits the Tau engine fork against upstream oh-my-pi; emits structured diff dataframes        |
| `AGENTS.md`      | Contributor rules for this repo                                                               |

```bash
# Audit the Tau engine vs upstream
bun run sovereign-skills/engine-audit.ts
```

## Adding a skill

1. Create `skills/<name>/SKILL.md` — atomic, self-contained, deterministic
2. Add `references/` for routing tables
3. Register in `skills.json`
