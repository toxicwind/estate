# bahamas10/bash-style-guide

Source: https://github.com/bahamas10/bash-style-guide

## Rules adopted

- Shebang: `#!/usr/bin/env bash`
- Conditionals: `[[ ... ]]` over `[ ... ]`
- Variables: quote every expansion
- Loops: brace expansion over `seq`
- Functions: no `function` keyword
- Arithmetic: `((...))` over `let`
- Tests: no `test` command

## Rules deliberately dropped

- Indentation: upstream uses tabs. The estate follows asc4asc (2 spaces).
  Rationale in README R-201.

## Quoted text from upstream

> Use 2 spaces for indentation.
> Columns not to exceed 80.
> No more than 2 consecutive newline characters.
> Don't change someone's comments for aesthetic reasons unless you are
> rewriting or updating them.
