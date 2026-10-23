---
name: estate-repo-update
description: Add or onboard a repo into the ranch as a standalone peer in the meta manifest (NOT a git submodule). Add a repo by ensuring it is a standalone git repo and adding it to .meta-themes.yaml (its themed holder), then run bun toolkit/gen-meta-manifest.ts to regenerate .meta.yaml — never `git submodule add`.
---

# Metá Peer Onboarding (replaces submodule doctrine)

## When to use this skill

Use when you need to:

1. Add a NEW repository to the ranch as a first-class peer
2. Onboard an EXISTING clone (previously a submodule or standalone) into the meta manifest
3. Understand why a repo shows stale/ghost submodule pointers
4. Regenerate the estate manifest after adding/renaming a repo

This replaces the retired `estate-submodule-update` doctrine. The ranch uses
the **meta model**: repos are PEERS in `ranch/.meta.yaml`, each an independent
clone with its own history — NOT `git submodule` links. The old flow (`git
submodule add` + `.gitmodules` + `git submodule update --init --recursive`) is
dead here; submodules cause detached-HEAD churn, orphan gitlinks, and stale
pointers. Stop adding them.

## Prerequisites

- A real, standalone git repo (has its own `.git`, a `main` branch, pushed to
  `https://github.com/toxicwind/<name>.git`)
- `bun` + `bun toolkit/gen-meta-manifest.ts` availability inside the ranch
- The repo directory already cloned at its permanent path under
  `/home/toxic/estate/ranch/<path>`
- The farm repo checked out (your working dir is `ranch`)

## Steps

### 1. Make the repo a standalone git repo (if not already)

```bash
# If it is not yet a repo:
cd /home/toxic/estate/ranch
mkdir -p <path>
cd <path>
git init
git add -A
git commit -m "Initial commit: [description]"
git branch -M main
gh repo create toxicwind/<name> --public --source=. --remote=origin --push
```

### 2. Ensure NO submodule pointer exists for it

If the repo path was previously a submodule, unlink the gitlink pointer
(keep the working dir — do NOT delete the clone):

```bash
# From the PARENT repo only if it still treats path as a gitlink (mode 160000):
git rm --cached <path>      # unlinks the pointer, leaves the directory + clone
git rm --cached .gitmodules # only after ALL submodule entries are gone
```

The directory stays; it becomes a standalone peer already known to the
manifest. Never `rm -rf` a repo directory.

### 3. Register it as a peer in its themed holder

Edit `/home/toxic/estate/ranch/.meta-themes.yaml` (DATA, not code):

- Add a list item under the right holder (the bounded-context column the repo
  is responsible for — `olympus`, `ranch-structure`, `gatehouse-mcp`, etc.).
- `submodules`, `tools`, `vendor` are NEVER holders — those are tracking, not
  domain. Use a real domain holder or the honest `general` fallback.
- Exact path beats top-level: `map[path] ?? map[topLevel] ?? general`.

```yaml
# .meta-themes.yaml, under e.g. research:
research:
  - "my-new-repo" # <- added as a standalone peer
```

### 4. Regenerate the manifest

```bash
cd /home/toxic/estate/ranch
bun toolkit/gen-meta-manifest.ts   # writes .meta.yaml from themes + on-disk peers
```

Verify the count embeds the new repo: the generator prints
`wrote ... with N projects in M categories`. Every on-disk repo the theme map
knows is emitted; nothing should be silently dropped. Spot-check
`nvim .meta.yaml` → the repo is under its holder with its `repo:` URL.

### 5. Verify peer state (NOT submodule status)

```bash
cd /home/toxic/estate/ranch
meta context                      # per-repo branch/clean/dirty across all peers
meta git update                   # clone missing + pull all (replaces git submodule update)
meta exec -- git -C <name> branch --show-current   # it is a normal peer branch
```

## Verification

- `git -C <name> remote get-url origin` → the expected `toxicwind/<name>.git`
- `.meta.yaml` contains the repo under its themed holder, not under `general`
  (unless honest fallback), with a real `repo:` URL
- The parent repo's `git ls-files --stage <name>` shows the paths as regular
  files **or absent** — NOT a `160000` gitlink commit
- No `[submodule ...]` section for `<name>` remains in any `.gitmodules`
- The repo's working dir is intact (never deleted)

## Tips

- Repos are peers: `meta git update` / `meta git status` / `meta exec`
  are the fleet commands — never `git submodule update --init`.
- `.meta.yaml` is GENERATED — edit `.meta-themes.yaml` data, run the generator,
  never hand-edit `.meta.yaml` (hand edits are lost on regen).
- Existing clone that was never a peer? Just add it to `.meta-themes.yaml` and
  regenerate — no gitlink exists to unlink.
- Use conventional commits (`chore(ranch)`, `docs(meta)`, `feat(meta-peer)`).
- Restart any meta-dependent supervised service after a binary/regen swap so
  the running estate adopts the change.
