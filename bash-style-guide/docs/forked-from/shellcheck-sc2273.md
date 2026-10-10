# ShellCheck SC2273

Source: https://www.shellcheck.net/wiki/SC2273

## Rule adopted

- Section dividers use `# --- NN - name ---`. Never a bare run of `=====`
  without a `#` prefix.

## Quoted text from upstream

> Problematic code: =======
> Correct code: Either resolve the merge conflict, or use `# =======`
> for a border.
> Rationale: ShellCheck found a series of =======s. If this was supposed
> to be a border or separator, use a comment.
