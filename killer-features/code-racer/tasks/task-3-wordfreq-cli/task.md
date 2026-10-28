# Task 3 — Word Frequency CLI

Write a command-line program that reports the most frequent words in a text.

**Deliverable:** `solution.py` — the harness runs it as
`python3 solution.py [--top N] [--min-len K] [FILE]`.

## Behavior

```
usage: solution.py [--top N] [--min-len K] [FILE]
```

- Reads text from `FILE`, or from **stdin** when no file is given.
- Tokenization: find all runs of ASCII letters/digits with the regex `[a-z0-9]+`
  applied to the **lowercased** text. (So `"Hello, HELLO! don't"` → `hello`, `hello`, `don`, `t`.)
- Discards tokens shorter than `--min-len` (default `1`).
- Counts the remaining tokens, sorts by **count descending**, ties broken by
  **word ascending** (plain string comparison).
- Prints the first `--top` entries (default `10`), one per line, as:

  ```
  <word> <count>
  ```

## Exit codes and errors

- Success → exit `0`.
- `--help` → exit `0` (argparse default text is fine).
- Missing/unreadable file → print an error to **stderr**, exit `2`.
- Invalid arguments (e.g. `--top` not an integer, negative values) → exit `2`.

## Examples

```
$ printf 'b a b\nA c b' | python3 solution.py --top 2
b 3
a 2

$ python3 solution.py --min-len 3 essay.txt
the 42
and 31
```

## Notes

- Only the standard library may be used.
- The program must be executable directly: `if __name__ == "__main__":` guard.
- The hidden acceptance tests invoke the CLI as a subprocess and check stdout,
  stderr, and exit codes exactly.
- `--top 0` prints nothing and exits `0`. An empty input prints nothing, exit `0`.
- Resource limits: `limits.yaml` / `limits.json` in this directory.
