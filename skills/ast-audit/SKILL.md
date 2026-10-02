---
name: ast-audit
description: >
  Verify claims about code against the actual abstract syntax tree — not curl,
  not ls, not grep. Given a claim ("port 25100 serves herd", "function X calls
  Y", "module A imports B"), runs structural ast-grep queries and returns
  VERIFIED / NOT-FOUND with quoted evidence (file, line, AST node, captured
  meta-variables). Triggers on: verify claim, audit code, prove it, README
  audit, API surface audit, does X call Y, what listens on port N.
---

# ast-audit — claim verification against the AST

Port/path/curl probes tell you a port is open. They never tell you **what code**
put it there. This skill closes that gap: every claim about code is checked
with structural (AST) queries, and the verdict ships with quoted evidence —
file, line range, the matched AST node, and the captured meta-variables.

Engine: `ast-grep` 0.45.3 (tree-sitter, 25 languages), installed on both boxes:
- yote: `/home/toxic/.local/share/mise/shims/ast-grep`
- cell: `~/.local/bin/ast-grep` (vendored 2026-10-02 from the official release)

**Always invoke `ast-grep`, never `sg`.** On Linux `sg` is util-linux
`setgroups`; ast-grep itself deprecates the `sg` alias. The engine resolves
the binary via `AST_GREP_BIN` env, then `ast-grep` on PATH.

## The workflow

```
1. CLASSIFY the claim  -> which structural question is it?
2. QUERY the AST       -> forge audit --root <dir> --claim "<claim>"
3. READ the evidence   -> file:line, matched node, $META captures
4. VERDICT              -> VERIFIED | NOT-FOUND | INCONCLUSIVE (never bare "yes")
```

## Usage

```bash
# Natural-language claim -> structural verification
forge audit --root /home/toxic/estate/tools/sovereign-router \
  --claim "sovereign router listens on port 25104"

# Direct structural pattern (you write the AST shape)
forge audit --root /home/toxic/estate/ranch --pattern 'app.listen($PORT, $$$)' --lang ts

# Full YAML rule for relational claims ("X calls Y")
forge audit --root /home/toxic/estate/ranch --rule scripts/rules/calls.yml

# JSON evidence for scripting
forge audit --root <dir> --claim "herd serves port 25100" --json
```

Example output:

```
=== audit: "sovereign router listens on port 25104" -> VERIFIED (2 hits) ===
  router.ts:87:2-87:31  Bun.serve({ port: 25104, ... })
    $PORT = "25104"
  config.ts:12:0-12:22  export const PORT = 25104
    $PORT = "25104"
```

## Claim types the router understands

| Claim shape | Structural question | AST strategy |
|---|---|---|
| "X listens on / serves port N" | where is N bound? | `listen`/`serve`/`Bun.serve` patterns; `$PORT` capture must equal N |
| "function X calls Y" | does X's body contain a call to Y? | find `def X`/`function X`, then `Y($$$)` with `inside` X's range |
| "module A imports B" | is there an import edge A->B? | import/require patterns, specifier contains B |
| "class X defines method Y" | symbol shape | class pattern with `has` method Y |
| "config key K = V" | text value, not structure | falls back to `rg` (see decision rule) |

Full pattern cookbook: `references/claim-recipes.md`.
Failure modes and gotchas: `references/pitfalls.md`.

## The decision rule (borrowed, field-tested)

Ask: **does the answer depend on the language's syntax tree, or just bytes?**

- Syntax shape (call, definition, import, control flow) -> **ast-grep** (this skill)
- Bytes (string contents, comments, config values, filenames) -> **rg**
- Meaning (what does this variable refer to, does it throw) -> LSP / type checker

When in doubt, run both and let the evidence decide. A claim is VERIFIED only
when the AST node is quoted — a matching `rg` line is supporting evidence,
never the verdict.

## Rules that are not optional

1. **Patterns are code, not regex.** `$VAR` = one AST node, `$$$` = zero or more
   nodes. `\w`, `.*`, `|` are not parseable — the query fails, silently or not.
2. **Single-quote patterns in shell.** `'$VAR'` — double quotes let the shell
   eat `$VAR` before ast-grep sees it.
3. **A claim with zero AST hits is NOT-FOUND, not refuted.** Absence of a
   structural match is not proof of absence — say what was searched.
4. **Quote the node.** Every VERIFIED verdict names file, line range, and the
   matched text. No evidence, no verdict.

## Merge provenance

Built 2026-10-02 per Chris's order ("port path command is not enough — use an
AST audit skill; find one on global GitHub, compare multiple, merge"). Winner:
**ast-grep** (ast-grep/ast-grep, 16k stars, MIT). Borrowed: pattern-validation
and pitfall discipline from `majiayu000/claude-skill-registry` ast-grep skill;
rule-authoring workflow (test-before-search, `stopBy: end`) from
`ampcode/amp-contrib`; progressive map->find->impact shape from
`srijanshukla18/xray`. Engine merged into pattern-forge as `forge audit`
(see `../pattern-forge/src/audit.ts`). Full comparison: `COMPARISON.md`.
