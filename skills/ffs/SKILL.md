---
name: ffs
description: The estate's ONLY search/read surface — one CLI over a persistent on-disk index (Bigram, Bloom, Symbol, Outline). Use for finding files by name, matching content, resolving symbols to definitions, tracing callers/callees, ranking blast radius, reading files budget-aware, and warming indexes. Using fd/rg/find/grep/cat instead is a doctrine violation, not a fallback.
---

# ffs

Every find/grep/read in the estate goes through ffs. One index, one grammar,
no per-command semantics to re-learn.

<critical>
- NEVER `fd`/`rg`/`find`/`grep`/`cat` — a doctrine violation, not a fallback.
- Pick the RIGHT subcommand for the job; the wrong one is a defect.
- `--limit 5-20` aggressively — the scan cost is independent of the limit.
- Search returned nothing that should exist? `ffs index`, then retry — stale index.
- `ffs read <path>` is budget-aware OUTLINE by default; `--full` for raw.
</critical>

## Pick the subcommand

| You want | Run | Notes |
|---|---|---|
| Find a file by name fragment | `ffs find <needle>` | substring, case-insensitive; `--scored` adds role/socle |
| Match by shape/glob | `ffs glob '**/<pattern>'` | shell glob: `**`, `*`, `?`, `[…]` |
| Content match, one pattern | `ffs grep <regex>` | ripgrep semantics; `--group` groups by enclosing symbol |
| Content match, many needles | `ffs multi-grep` | Aho-Corasick literal AND/OR; fastest for OR |
| Read a file without flooding context | `ffs read <path>` | outline by default; `--full` raw; `path:N` drill; `--budget <N>` |
| Sketch one file's structure | `ffs outline <path>` | tree-sitter; `--style agent/…` |
| Resolve a symbol to its definition | `ffs symbol <name>` | AST, not substring; `symbol Foo*` = prefix glob |
| Who refers to this symbol | `ffs callers <name>` | `--hops N` BFS (≤5) |
| What does this symbol call | `ffs callees <name>` | `--depth N` |
| Defs + usages in one shot | `ffs refs <name>` | full defs + paged callers |
| Full card per definition | `ffs flow <name>` | def+signature+body+callees+callers |
| Peers at same scope | `ffs siblings <name>` | `--include-imports` |
| Imports + dependents of a file | `ffs deps <path>` | import graph |
| Rank blast radius of a change | `ffs impact <symbol>` | score = direct×3 + imports×2 + transitive |
| See the whole workspace | `ffs map` / `ffs overview` | file counts + token estimates |
| Warm the indexes | `ffs index` | build Bigram/Bloom/Symbol/Outline caches |
| Recall the guide | `ffs guide` | the embedded 288-line doc |

Global flags: `--root <dir>`, `--format text|json`; paged listing commands take
`--limit N --offset N` (JSON returns `total/offset/has_more`).

## Worked examples

```bash
# Where does ValidateAndRoute live?
ffs symbol ValidateAndRoute

# Who calls it, two hops out?
ffs callers ValidateAndRoute --hops 2

# All functions matching a prefix
ffs symbol "meta_*"

# Cheap content sweep across the estate
ffs grep "kappacode" --root /home/toxic/estate --limit 20

# Read a file's shape before reading the file
ffs outline src/route/executor.ts
```

## Failure shapes you own

WRONG: `rg kappacode /home/toxic/estate` — re-scans the tree; ffs's index
already knows. (And rg ignores the doctrine.)
RIGHT: `ffs grep kappacode --root <dir> --limit 20`.

WRONG: `ffs grep` returns nothing → conclude "no matches".
RIGHT: nothing + it should exist → `ffs index` (stale index), retry.

WRONG: `ffs read giant-file.ts` for the 4,000-line dump.
RIGHT: `ffs read giant-file.ts` (outline) → `path:142` to drill to the region.

## Not your job

Index internals (bigram tables, bloom filters, tree-sitter grammars), cache
warm-up policy, MCP transport. `ffs guide` if a subcommand's semantics are
unclear.
