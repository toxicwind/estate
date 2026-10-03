---
name: ffs-grep-root-not-path
description: "`ffs grep` takes `--root`, never a path positional — and never chain a loop over an unverified ffs invocation"
condition: ["ffs\\s+grep\\s+[^\\s|;&]*\\s+['\\\"][^'\\\"]+['\\\"]\\s+/home/toxic", "ffs\\s+grep\\s+\\S+\\s+\\S+\\s+--root"]
scope: "tool"
---

`ffs grep <needle> --root <dir>` takes **no path positional argument**. Passing a path positionally makes it search your CWD and silently return nothing, which reads as "no matches" — that is how two sweeps reported zero stale `sovereign` references when the tree was full of them. Always `--root`.

Corollary, from the same failure: **do not build a loop or pipeline over a command whose output shape you have not confirmed on one invocation.** Run `ffs grep --help`, run one real call, read the output, and only then loop. A `for` loop over an unverified invocation produced empty results twice and was mistaken for "the directory is clean."

Two more from this session:
- `ffs grep --limit` defaults to **200** and `--format json` does not return the shape you assumed. Confirm the output shape before parsing it.
- `ffs find` takes no `-g/--compact`; check `ffs find --help` separately from `ffs grep --help`.

If a sweep returns zero hits, that is a hypothesis to check, not a result. Re-run one query with `--root` explicitly and show the real output.