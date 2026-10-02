# Pitfalls — the failure-mode field guide

Borrowed from `majiayu000/claude-skill-registry` (ast-grep skill) and
`ampcode/amp-contrib` (ast-grep skill), verified live on this estate
2026-10-02. Read this before debugging "0 matches".

## 1. `sg` is not ast-grep on Linux

`/usr/bin/sg` is util-linux **setgroups** ("run command as different group").
ast-grep's own `sg` alias is deprecated upstream. **Always invoke `ast-grep`.**
The `forge audit` engine resolves via `AST_GREP_BIN`, then `ast-grep` on PATH —
never `sg`.

## 2. ast-grep is NOT regex

| You wrote | ast-grep saw | What you wanted |
|---|---|---|
| `foo\|bar` | bitwise-or of `foo` and `bar` | two separate searches |
| `.*foo` | not parseable | `$$$` in a node list, or `rg` |
| `\w+` | not parseable | `$VAR` for one identifier |
| `[a-z]` | character class, not parseable | `rg` |

Patterns must be **valid code**: `def $FN($$$):` fails on the trailing colon
(use `def $FN($$$)`); `function $NAME` without body fails (use
`function $NAME($$$) { $$$ }`).

## 3. Single-quote patterns in shell

`'$VAR'` not `"$VAR"` — double quotes let the shell expand `$VAR` to empty
before ast-grep sees it. In YAML inline rules, escape as `\$VAR`.

## 4. `--json` and `--update-all` are mutually exclusive (silently)

`ast-grep run -p P -r R --json --update-all` returns JSON but **does not write**.
Audit work is read-only anyway — but if you ever add a rewrite path, do two
passes: `--json=compact` to preview, then `--update-all` to apply.

## 5. `--lang` must match the file

ast-grep infers language from extension, but an explicit `--lang ts` on a
`.tsx` file silently skips JSX. With `--stdin`, `--lang` is **required**.

## 6. Relational rules need `stopBy: end`

`inside`/`has` stop at the first non-matching node unless you add
`stopBy: end`. Without it, "X calls Y" misses calls nested deeper than one
level. (amp-contrib's #1 rule.)

## 7. Zero hits ≠ refuted

A structural miss means "no node of that shape in the searched tree" — the
tree may be scoped wrong (check `--root` and globs), the language may be
wrong, or the claim may live in config/text (use `rg`, recipe 5). Verdicts:
**VERIFIED** (quoted node), **NOT-FOUND** (searched, nothing), **INCONCLUSIVE**
(search itself was malformed or mis-scoped). Never "refuted" from a miss.

## 8. Meta-variable capture is the proof

`--json=compact` returns `metaVariables.single.PORT.text`. For port claims the
verdict hinges on the **captured value**, not the match count — 50
`app.listen($PORT)` hits with `$PORT = 3000` do not verify "listens on 25104".

## 9. Quote `$SPEC` in import patterns

`import $$$ from $SPEC` binds `$SPEC` to the **import clause** (`{ PORT }`),
not the module specifier — a real ast-grep binding quirk, verified 2026-10-02.
Write `import { $$$ } from "$SPEC"` (or `import $DEF from "$SPEC"`,
`import * as $NS from "$SPEC"`, `import "$SPEC"`) and the capture is the clean
specifier text (`./router_config.ts`, quotes stripped).
