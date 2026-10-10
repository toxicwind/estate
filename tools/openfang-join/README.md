# openfang-join

Admit a fleet (squawk) agent into OpenFang as a first-class agent. One command:
render `agent.toml` + `system.md`, run the V1–V5 validation gate, write the
canonical `estate/agents/<name>/` manifest, spawn via the OpenFang API,
verify Running.

```sh
openfang-join --name <name> --species <s> --personality <p> \
  --lane <lane> --task <task> --sigil <emoji> [--desc <d>] \
  [--from <existing-agent>] [--model <m>] [--provider <p>] \
  [--dry-run] [--rejoin] [--commit] [--push]
```

## Safety design

- **Validation gate (V1–V5)** runs on every join: TOML parses, required fields,
  name uniqueness across `estate/agents/` + `~/.openfang/agents/` + live API,
  persona completeness, sanity. Any failure **refuses** the join.
- **`--commit`** commits the two manifest files in the shared checkout.
- **`--push`** never pushes from the shared checkout. It fetches fresh
  `origin/main`, builds the commit in a throwaway detached worktree pinned at
  that exact SHA (containing only the two new files), pushes `HEAD:main`,
  verifies via `git ls-remote`, and removes the worktree. No force-push, ever.
  This structurally removes the old merge-base footgun, which could pass for
  any branch containing main.

## Layout

- `openfang-join` — the tool (Bun, `#!/usr/bin/env bun`)
- `bin/openfang-join` (gitignored, yote-local) symlinks here so the bare
  command keeps working.

Fixed 2026-09-30: `res.text()` TypeError on the commit path (res is already a
string); push path rebuilt around the isolated-worktree design.
