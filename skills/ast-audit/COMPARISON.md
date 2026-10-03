# AST audit skill — global GitHub search, comparison, merge

Chris's order (2026-10-02): *"Port path command is not enough, must use some
sort of ast audit skill, find one on global GitHub using code search and
compare multiple and merge with skill that does this."*

Search method: `gh search code` + `gh search repos` (yote, authed as
toxicwind), plus `browser.open` reads of the winning skill files. Absence-proof
per the lazy-no doctrine: GitHub code search, repo search, and direct reads —
not a single catalog query.

## Candidates evaluated

### 1. ast-grep — ast-grep/ast-grep (16,104 stars, Rust, MIT) — WINNER (engine)

Structural search / lint / rewrite over tree-sitter grammars, 25 languages.
`--json=compact` emits file, 0-based line/col ranges, matched text, and
captured meta-variables (`$PORT`, `$SPEC`) — exactly the evidence shape a
claim-verifier needs. Single 52 MB static binary, millisecond queries,
already packaged for every OS. Official MCP server exists
(ast-grep/ast-grep-mcp, 471 stars) but the CLI's JSON mode is cheaper for
agents than an MCP round-trip.

- Languages: 25 (ts/tsx/js/py/go/rs/java/c/kotlin/swift/...).
- Precision: structural — `app.listen($PORT)` never matches a comment
  mentioning "app.listen".
- Speed: ms per query; no index to build, no daemon.
- Agent cost: one subprocess call, JSON out. Trivial.
- Verdict: the engine everything else should be built on.

### 2. majiayu000/claude-skill-registry — ast-grep skill (merged: discipline)

A full agent skill (`skills/other/ast-grep/SKILL.md` + `ast_grep_helper.py`):
offline pattern validation (catches regex-misuse before calling `sg`),
two-pass write safety (`--json` and `--update-all` are silently exclusive),
the sg/setgroups collision warning, and the syntax-vs-bytes decision tree.
**Merged:** pitfalls §1–§8, the decision rule, validate-before-search and
dry-run-before-apply invariants, the "0 matches" debug order.

### 3. ampcode/amp-contrib — ast-grep skill (merged: rule workflow)

`.agents/skills/ast-grep/SKILL.md`: NL→rule translation workflow,
test-before-search (example file first), rewrite methods, and the hard-won
`stopBy: end` rule for relational queries.
**Merged:** `scripts/rules/calls.yml` template, the two-pass call-edge design,
`stopBy: end` in every `inside`/`has` rule, recipe §2 and §6.

### 4. srijanshukla18/xray (54 stars, MIT) — evaluated, not merged

MCP for AI assistants: map → find → impact progressive discovery over
ast-grep, stateless, per-commit symbol caching. Good shape, but: only 4
languages documented, `what_breaks` impact analysis is **name-based text
search** (not AST — the exact weakness Chris flagged), and MCP-only
(would need a client where a subprocess suffices). Its progressive-disclosure
philosophy informed the evidence-cap (`--top`) design. Rejected as the base;
xray's own architecture doc confirms ast-grep as the right core engine.

### 5. semgrep — semgrep/semgrep (16,840 stars) — evaluated, rejected

Deep AST analysis with type inference and a huge rule corpus. But: heavy
install (Python + binary, rules ecosystem), seconds-per-scan latency,
built for security findings — not for answering "does X call Y" in an
agent loop. Overkill for claim verification; ast-grep is 10–100× cheaper
per query.

### 6. tree-sitter via MCP — majiayu000 registry tree-sitter skill — evaluated, rejected

Raw tree-sitter through `mcp_server_tree_sitter`: project registration,
per-project state, `get_ast`/`run_query` tools. Maximum power, maximum
friction — and the skill doc carries noise (astrology-style "GF(3)" filler),
a quality signal against it. ast-grep already wraps tree-sitter with a
pattern language agents can write; raw tree-sitter queries are a level
agents should not have to drop to.

## What was built (the merge)

**Local skill that "does this": pattern-forge** — it had absorbed
ast-bm25-racer / dynamic-ast-probe / code-racer-swe (all AST-ish retrieval)
but had no real AST: Python extraction was lexical, and its own SKILL.md
admits adding tree-sitter would break its zero-dependency rule. ast-grep is
an external binary (already on both boxes), so no dependency was added.

New `forge audit` leg (`pattern-forge/src/audit.ts`, pure Bun):

```
forge audit --root <dir> --claim "sovereign router listens on port 25104"
forge audit --root <dir> --claim "deploy calls push"
forge audit --root <dir> --claim "router imports router_config"
forge audit --root <dir> --pattern 'app.listen($PORT, $$$)' --lang ts
forge audit --root <dir> --rule scripts/rules/calls.yml
```

Claim router: port-bind (captured `$PORT` must equal the claimed port),
call-edge (two-pass: X's definition range → `Y($$$)` inside it),
import-edge (specifier substring on the captured `$SPEC`), symbol-definition.
Verdicts: VERIFIED (quoted node) / NOT-FOUND / INCONCLUSIVE. Exit codes
0 / 1 / 2. `forge doctor` gains an `audit (ast-grep)` check.

New skill doc: `~/workspace/skills/ast-audit/` — SKILL.md (workflow),
`references/claim-recipes.md` (claim → pattern cookbook),
`references/pitfalls.md` (9 field-verified gotchas, incl. two found live:
ast-grep exits 1 with valid `[]`; unquoted `$SPEC` binds the import clause).

## Verified live (2026-10-02)

- Cell + yote: ast-grep 0.45.3 (cell vendored to `~/.local/bin/ast-grep`
  from the official release; yote via mise shims). `/usr/bin/sg` on the cell
  is util-linux setgroups — the engine never calls `sg`.
- Synthetic: port-bind VERIFIED with `$PORT="25100"` capture; call-edge
  VERIFIED (`push()` inside `deploy()`); NOT-FOUND paths return honest notes.
- Real estate code (yote, `/home/toxic/estate/ranch/mesh/router/sovereign-router`):
  "router imports router_config" → VERIFIED, `$SPEC="./router_config.ts"`,
  router_ui.ts:1. "sovereign router listens on port 25104" → bind sites
  found as `Bun.serve({ port: PORT })` (router.ts:183), port symbolic —
  the audit correctly refused to claim the literal and pointed at config/env;
  follow-up pattern `export const PORT = $EXPR` → VERIFIED,
  `parseInt(_portRaw, 10)` (router_config.ts:59), `_portRaw` from
  `SOVEREIGN_ROUTER_PORT` env. This is the whole point: curl would have said
  "port open" and stopped; the AST gave the full bind chain.
- `forge doctor`: `PASS audit (ast-grep)`; all 23 existing pattern-forge
  tests pass (`bun test tests/`).

## How to invoke

```bash
# one claim, human-readable evidence
forge audit --root /home/toxic/estate/ranch --claim "X calls Y"

# scripting
forge audit --root <dir> --claim "..." --json | jq .verdict
```

Full workflow: `~/workspace/skills/ast-audit/SKILL.md`.
