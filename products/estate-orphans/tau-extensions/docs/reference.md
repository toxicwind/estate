# Patch language

The grammar, header shape, and enforced invariants for hashline patches
and the shipped extension surface.

## Patch grammar

- Human-readable grammar and rule set: [`src/vendor/prompt.md`](../src/vendor/prompt.md).
  This file is also what the extension ships to the model as the tool
  description, so it is the authoritative statement of what a well-formed
  patch looks like.
- Machine grammar (Lark-style, informational): [`src/vendor/grammar.lark`](../src/vendor/grammar.lark).
- Diagnostic strings: [`src/vendor/messages.ts`](../src/vendor/messages.ts).

## Operations

| Header             | Body        | Effect                                                       |
| ------------------ | ----------- | ------------------------------------------------------------ |
| `SWAP N.=M:`       | `+` rows    | Replace original lines `N` through `M` (inclusive).          |
| `DEL N` / `DEL N.=M` | none      | Delete a single line or an inclusive range.                  |
| `INS.PRE N:`       | `+` rows    | Insert body immediately before line `N`.                     |
| `INS.POST N:`      | `+` rows    | Insert body immediately after line `N`.                      |
| `INS.HEAD:` / `INS.TAIL:` | `+` rows | Insert at start / end of file.                          |
| `REM`              | none        | Delete the whole file named by the section header.           |
| `MV DEST`          | none        | Move/rename the section file to `DEST`.                      |
| `*.BLK` variants   | —           | Parsed but not applied in v1 (no tree-sitter resolver).      |

Every body row is `+TEXT` (verbatim, including leading whitespace).
`+` alone adds a blank line. There are no `-old` or context rows.

## Section header

```
[PATH#TAG]
```

- `PATH` is the target file path relative to the working tree. Quote it if
  it contains spaces.
- `TAG` is a 4-hex snapshot fingerprint minted at the last `read`/`search`.
  It is required. Missing or stale tags reject the section with a
  re-`read` instruction; hashline never creates files.

## Enforced invariants

- Every section carries a fresh tag (`src/vendor/patcher.ts`).
- Multi-file patches are all-or-nothing at preflight
  (`src/vendor/apply.ts`, `src/vendor/patcher.ts`).
- Same-path sections against the same snapshot merge before applying
  (`src/vendor/input.ts`).
- Empty `SWAP` and `INS` bodies are rejected at parse time with a
  suggestion to use `DEL` instead (`src/vendor/parser.ts`).
- Unsupported block ops throw with a fallback suggestion
  (`src/vendor/messages.ts` → `UNRESOLVED_BLOCK_*`).
- Tag hashing is LF-normalized with trailing `[ \t\r]` stripped, so
  CRLF/BOM/whitespace-only differences do not invalidate a tag; the
  original ending + BOM are restored on write (`src/vendor/normalize.ts`).

## Public entry point

The extension entrypoint is `extensions/pi/index.ts`. It registers a
single tool named `hashline` and delegates to the vendored core under
`src/vendor/`.
