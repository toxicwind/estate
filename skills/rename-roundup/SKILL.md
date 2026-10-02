---
name: rename-roundup
description: >
  Full-blown fork renaming and rebranding engine. Safely rewrites URL anchors,
  package identifiers, documentation, and case variants across all git-tracked files
  in a repository or fork. Triggers on: "rename roundup", "fork rename",
  "rename fork", "rebrand fork", "rename repo tokens", "full blown rename".
---

# Rename Roundup / Fork Rename Engine

## Purpose
Performs an automated, ordered, case-preserving rebranding pass across a repository checkout.
Ensures fork-hosted URLs, documentation references, environment variables, and code tokens are systematically updated without corrupting binary assets or package lockfiles.

## Execution Order
1. **URL Anchors**: Replace repository upstream URLs with fork URLs (e.g. `github.com/vllm-project/guidellm` -> `github.com/toxicwind/roundup`).
2. **Uppercase / Constant Identifiers**: Replace ALL_CAPS variants (`GUIDELLM` -> `ROUNDUP`).
3. **Title / CamelCase Identifiers**: Replace Capitalized variants (`GuideLLM` / `Guidellm` -> `Roundup`).
4. **Lowercase Identifiers**: Replace lowercase package/module tokens (`guidellm` -> `roundup`).

## Usage

### Default (Roundup Fork)
```bash
python3 /home/toxic/estate/skills/rename-roundup/rename.py
```

### Parameterized (Any Fork / Rebrand)
```bash
python3 /home/toxic/estate/skills/rename-roundup/rename.py \
  --repo /path/to/repo \
  --old guidellm \
  --new roundup \
  --old-org vllm-project \
  --new-org toxicwind
```

## Safety Invariants
- Operates only on `git ls-files` tracked files (never touches untracked scratch).
- Skips binaries, wheels, compiled objects, shared libraries, and lockfiles (`.png`, `.gif`, `.whl`, `.so`, `.pyc`, `uv.lock`, `bun.lock`).
- Ignores build outputs (`build/`, `*.egg-info`).
- Atomic utf-8 read and overwrite only when textual changes occurred.
