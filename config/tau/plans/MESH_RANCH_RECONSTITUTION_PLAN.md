# Plan: Reconstitute and Rename Mesh/Ranch Tree

## Context
Reconstitute and rename the `mesh/ranch` tree according to the structural topology where `stockyard/` holds herd and flock, `barn/` holds shep, and mechanism folders are renamed appropriately. All references, symlinks, and retired names must be purged with verified builds, zero symlinks, zero retired names, and zero conflict markers.

## Approach
1. **Inventory & Map Modules**
   - Discover all module manifests and paths under `projects/mesh` and `projects/herd`.
   - Classify components by module identity, entrypoint, and config pointers.
2. **Merge & Resolve Duplicates**
   - Merge duplicate module groups (such as router/herd variants) per-file, writing `MERGE-DECISIONS.md` at survivor root.
3. **Rename & Move Folders**
   - Rename `ranch/routers` to `ranch/stockyard/`.
   - Rename `ranch/mcp` to `ranch/barn/`.
   - Move child components into their respective monorepos (`stockyard/herd`, `stockyard/flock`, `barn/shep`).
4. **Rewrite Configs**
   - Update all references in `pitchfork.toml`, `mise.toml`, `stack/services/*.sh`, systemd units, environment files, and launchers to eliminate retired names (`super-ralph`, `llama-swap`, `sovereign-swap`, `ranch/routers`, `ranch/mcp`).
5. **Purge Symlinks**
   - Delete all user-created symlinks under `~/sovereign` and `~/projects` after repointing callers directly to canonical paths.
6. **Verify**
   - Run builds and tests for touched Go and other language modules.
   - Assert zero symlinks, zero retired names, and zero conflict markers.

## Critical Files & Anchors
- `projects/mesh/ranch/` — target monorepo tree for stockyard and barn renames.
- `pitchfork.toml` — service paths and launcher references.
- `mise.toml` — task and task environment paths.

## Verification
- Run `fd -t l -H . ~/sovereign ~/projects | wc -l` (assert 0).
- Run `rg -c 'super-ralph|llama-swap|sovereign-swap' ~/sovereign ~/projects` (assert 0).
- Run `rg -c '^<<<<<<<|^=======|^>>>>>>>' ~/sovereign ~/projects` (assert 0).
- Run `go build ./... && go test ./...` in touched modules.

## Assumptions & Contingencies
- If binary filename `llama-swap` is required by an external launcher/process argv[0], retain the binary filename while placing source code under canonical `herd` directory.
