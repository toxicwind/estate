# Rename Roundup — Fork Rebranding Engine

Automated, safe, ordered case-preserving token and URL replacement tool for repository forks.

## Overview
When maintaining downstream forks (such as `toxicwind/roundup` or `toxicwind/sigma`), keeping branding, package imports, and documentation aligned with the new name requires updating hundreds of files without breaking binary formats or upstream tracking anchors.

`rename.py` automates this across all git-tracked files in a repository.

## Features
- **URL-First Precedence**: Rewrites documentation links, homepage links, and issue trackers before bare token substitution to prevent partial string collisions.
- **Case-Variant Matrix**:
  - `UPPER_CASE`: Constants and environment variables (`GUIDELLM` -> `ROUNDUP`).
  - `TitleCase`: Classes and documentation headers (`GuideLLM` -> `Roundup`).
  - `lower_case`: Module paths, commands, and package names (`guidellm` -> `roundup`).
- **Binary & Lockfile Protection**: Skips `.png`, `.gif`, `.whl`, `.so`, `.pyc`, and lockfiles (`uv.lock`, `bun.lock`).
- **Dry-Run Mode**: Inspect affected files and replacement preview without writing to disk.

## Command Line Usage
```bash
# Run against toxicwind/roundup (default target)
python3 rename.py

# Run against custom target repository
python3 rename.py --repo /home/toxic/estate/sigma --old billion-context --new sigma --dry-run
```
