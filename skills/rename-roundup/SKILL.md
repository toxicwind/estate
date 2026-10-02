---
name: rename-roundup
description: >
  Full-blown fork renaming and rebranding engine (Bun-native). Safely rewrites
  URL anchors, package identifiers, documentation, and case variants across all
  git-tracked files AND filenames in a repository or fork. Handles dangerous
  short tokens via whole-word/prefix modes (omp -> tau without touching
  "complete"). Triggers on: "rename roundup", "fork rename",
  "rename fork", "rebrand fork", "rename repo tokens", "full blown rename".
---

# Rename Roundup / Fork Rename Engine

Bun-native fork rebranding. One engine, one implementation: `rename.ts`
(the old Python version was retired — Bun is the implementation).

## Why pairs files

A naive search-replace destroys repos when the old brand is a short token:
`omp` lives inside `complete`, `prompt`, `component`, `compact`. The pairs
file gives each token a match mode:

```
substr:  OLD => NEW    plain substring (distinctive tokens: oh-my-pi, @scope, URLs)
word:    OLD => NEW    whole word \bOLD\b (omp, OMP, Omp — skips "complete")
prefix:  OLD => NEW    word prefix \bOLD (pi- -> tau-, Pi- -> Tau-)
exclude: TOKEN         never rewritten (OMP_NUM_THREADS — real OpenMP variable)
# lines starting with # are comments
```

Every substr/word/prefix rule auto-expands to UPPER and Capitalized variants.
Rules apply in file order. Exclusions are placeholder-armored before any rule.

## Usage

```bash
# Full rename via pairs file (preferred)
bun run ~/workspace/skills/rename-roundup/rename.ts \
  --repo /home/toxic/tau --pairs /home/toxic/estate/docs/tau-rename.pairs \
  --dry-run

# For real, wrapped in one commit (atomic rollback: git reset --hard HEAD~1)
bun run ~/workspace/skills/rename-roundup/rename.ts \
  --repo /home/toxic/tau --pairs /home/toxic/estate/docs/tau-rename.pairs \
  --commit "rename: oh-my-pi/omp -> tau (full fork rebrand)"

# Legacy simple mode (substring semantics, roundup-style renames)
bun run ~/workspace/skills/rename-roundup/rename.ts \
  --repo /path/to/repo --old guidellm --new roundup \
  --old-org vllm-project --new-org toxicwind --dry-run
```

## Safety invariants

- Operates only on `git ls-files` tracked files (never untracked scratch).
- Skips binaries by extension, lockfiles (`bun.lock`, `uv.lock`, ...),
  build outputs (`build/`, `dist/`, `target/`, `node_modules/`, `.git`).
- Filenames renamed with `git mv` (history preserved), deepest-first.
- Collisions (target exists, git mv failure) are reported, never forced.
- `--dry-run` previews content changes AND renames. Exit 2 on collisions.
- Idempotent: re-running changes nothing.

## Rollback

- With `--commit`: `git reset --hard HEAD~1` (or `git revert`).
- Without: `git checkout -- .`, then revert the `R` renames from the log.

## Provenance

Borrowed pattern check 2026-10-02 (GitHub-wide): existing tools
(renamebyreplace, File-Renaming-Tool, renamify, cschleiden/replace-tokens)
cover filename-only or token-only replacement; none combine word-boundary
code-safe token modes + git-tracked-only + git-mv filename renames + paired
commit/rollback. Ours stands. Prior art: DocSpring/renamify (case-aware,
built-in undo) informed the pairs-file + commit design.
