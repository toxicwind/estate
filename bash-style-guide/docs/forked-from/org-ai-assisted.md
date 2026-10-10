# org-ai-assisted/developer-meta-files

Source: https://github.com/org-ai-assisted/developer-meta-files/blob/master/agents/bash-style-guide.md

## Rules adopted verbatim

- R-001: ASCII only. No smart quotes, em dashes, zero-width spaces, emoji.
- R-010: strict-mode block.
- R-011: `var=$((expr))` not `(( expr ))`.
- R-012: under errexit, arithmetic that evaluates to zero exits the shell.

## Quoted text from upstream

> Source code and commit messages are ASCII only. No smart quotes, em
> dashes, zero-width spaces, emoji. Why: AI tools reflexively render text
> with cosmetic unicode (U+2014 em dash, U+2192 right-arrow); strip them.
> ASCII-only files make `LC_ALL=C grep -PlI "[^\x00-\x7F]"` a useful
> pre-push gate.

> R-012: Arithmetic assignment uses `var=$((expr))`, never `(( expr ))`.
> Under errexit, an arithmetic expression that evaluates to zero exits
> the shell.
