# Rename Roundup — Fork Rebranding Engine

Bun-native, safe, ordered rebranding across a repository's tracked files **and**
filenames. Built for the rename a naive search-replace would destroy: short
tokens like `omp` that hide inside `complete`, `prompt`, `component`.

## Overview

When maintaining downstream forks (`toxicwind/tau` from `can1357/oh-my-pi`,
`toxicwind/sigma` from `billion-context`, `herd` from `llama-swap`), keeping
branding, package imports, and documentation aligned means updating thousands
of files without corrupting words that merely contain the old token.

`rename.ts` does this from an explicit **pairs file**:

```
substr:  oh-my-pi => tau       # distinctive token, plain substring
word:    omp => tau            # whole word only — "complete" survives
prefix:  pi- => tau-           # word prefix — pi-shell becomes tau-shell
exclude: OMP_NUM_THREADS       # never rewritten (real OpenMP variable)
```

## Features

- **Match modes**: `substr` / `word` (`\b`) / `prefix` per token, plus `exclude`.
- **Case-variant matrix**: every rule auto-expands to UPPER and Capitalized.
- **Filenames too**: renamed with `git mv`, deepest-first, collisions reported.
- **Binary & lockfile protection**: skips images, wheels, `.so`, `bun.lock`, etc.
- **Dry-run**: previews content changes and renames without writing.
- **`--commit`**: wraps the run in one git commit — rollback is one command.
- **Idempotent**: re-running changes nothing.

## Usage

```bash
# Preview
bun run rename.ts --repo /home/toxic/tau --pairs tau-rename.pairs --dry-run

# Execute, one atomic commit
bun run rename.ts --repo /home/toxic/tau --pairs tau-rename.pairs \
  --commit "rename: oh-my-pi/omp -> tau (full fork rebrand)"
```

## Rollback

- With `--commit`: `git reset --hard HEAD~1`
- Without: `git checkout -- .` + revert the logged `R` renames
