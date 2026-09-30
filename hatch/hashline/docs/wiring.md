# hashline first-class wiring

Goal (Chris 2026-09-30): hashline is the **first-class edit tool for all agents
and subagents** — binary first, MCP where the harness supports it; raw
str_replace/sed for content edits is the fallback, not the default
(a fallback is not a rollback).

## 1. Skill (done)

`~/workspace/skills/hashline/SKILL.md` on the cell — full coverage: all 11
subcommands + flags, complete op table, MCP (6 tools, schemas, newline-delimited
framing), daemon mode, config/env, measured proof.

## 2. Fleet knowledgebase — exact proposed diffs (main agent applies)

File: `/home/toxic/sovereign/docs/fleet-knowledgebase.md` (canonical
toxicwind/sovereign-projects, main).

**A. §4 Standing rules — append as rule 18** (after rule 17, before the
"Oracle-as-approval procedure" paragraph):

```markdown
18. **hashline is the first-class edit tool (Chris 2026-09-30).** Every agent edits files with hashline — binary first, MCP where the harness supports it; raw str_replace/sed for content edits is the fallback, not the default (a fallback is not a rollback). Workflow: `hashline read <file>` → copy the `line:hash` anchors → `hashline patch` (`SWAP`/`DEL`/`INS.*`/block ops). Stale reads hard-fail: re-read, re-anchor, retry — never force. Structural find: `hashline find-block <file> <anchor>`. MCP: `hashline mcp` (stdio, newline-delimited JSON-RPC, 6 tools). No text-search surface exists by design — grep/rg/ffs for search, hashline for the edit. Skill: `~/workspace/skills/hashline/SKILL.md`. Project: `/home/toxic/sovereign/hatch/hashline/`.
```

**B. §5 Docs index — append two lines** (after the paper-search skill line):

```markdown
- hashline skill: `~/workspace/skills/hashline/SKILL.md` (cell) — first-class edit tool: binary CLI + MCP server
- hashline project: `/home/toxic/sovereign/hatch/hashline/` (README, discovery, runbook, wiring)
```

## 3. Spawn-brief template — exact paragraph (main agent applies)

File: `/home/toxic/sovereign/docs/spawn-brief-template.md`, in
`### Operating rules`, as a new bullet after the "Box routing." bullet:

```markdown
- **hashline first for every edit.** `hashline read <file>` → anchor (`42:a3`) → `hashline patch` — binary first, MCP (`hashline mcp`) where your harness supports it. Raw str_replace/sed for content edits is the fallback, not the default — a fallback is not a rollback. Stale anchor? Re-read, re-anchor, retry; never force. No text-search in hashline by design: grep/rg/ffs to find, hashline to change. Skill: `~/workspace/skills/hashline/SKILL.md`.
```

## 4. join-prompt (optional, proposed)

`skills/fleet-spawn/join-prompt.md` step 4 area — one line alongside the squawk
mechanism so new agents learn the edit tool in the same breath as the chat tool:

```markdown
Edit files with hashline first (`hashline read` → anchor → `hashline patch`); raw editing is the fallback, not the default. Skill: `~/workspace/skills/hashline/SKILL.md`.
```

## 5. Standing files

AGENTS.md / SOUL.md / IDENTITY.md / USER.md / MEMORY.md are main-agent-only —
proposed above, not edited. The KB + brief-template edits are also main-agent
applies (this lane doesn't touch sovereign-projects).
