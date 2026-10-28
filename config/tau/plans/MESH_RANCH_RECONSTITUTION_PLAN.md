# Plan: Reconstitute and Rename Mesh/Ranch Tree

## Context
Reconstitute and rename the `mesh/ranch` tree according to the structural topology where `stockyard/` holds bornite and rhodochrosite, `barn/` holds shep, and mechanism folders are renamed appropriately. All references, symlinks, and retired names must be purged with verified builds, zero symlinks, zero retired names, and zero conflict markers.

## Approach
1. **Inventory & Map Modules**
   - Discover all module manifests and paths under `projects/mesh` and `projects/bornite`.
   - Classify components by module identity, entrypoint, and config pointers.
2. **Merge & Resolve Duplicates**
   - Merge duplicate module groups (such as router/bornite variants) per-file, writing `MERGE-DECISIONS.md` at survivor root.
3. **Rename & Move Folders**
   - Rename `ranch/routers` to `ranch/stockyard/`.
   - Rename `ranch/mcp` to `ranch/barn/`.
   - Move child components into their respective monorepos (`stockyard/bornite`, `stockyard/rhodochrosite`, `barn/shep`).
4. **Rewrite Configs**
   - Update all references in `pitchfork.toml`, `mise.toml`, `stack/services/*.sh`, systemd units, environment files, and launchers to eliminate retired names (`super-ralph`, `bornite`, `estate-swap`, `ranch/routers`, `ranch/mcp`).
5. **Purge Symlinks**
   - Delete all user-created symlinks under `/home/toxic/estate` and `~/projects` after repointing callers directly to canonical paths.
6. **Verify**
   - Run builds and tests for touched Go and other language modules.
   - Assert zero symlinks, zero retired names, and zero conflict markers.

## Critical Files & Anchors
- `projects/mesh/ranch/` — target monorepo tree for stockyard and barn renames.
- `pitchfork.toml` — service paths and launcher references.
- `mise.toml` — task and task environment paths.

## Verification
- Run `fd -t l -H . /home/toxic/estate ~/projects | wc -l` (assert 0).
- Run `rg -c 'super-ralph|bornite|estate-swap' /home/toxic/estate ~/projects` (assert 0).
- Run `rg -c '^<<<<<<<|^=======|^>>>>>>>' /home/toxic/estate ~/projects` (assert 0).
- Run `go build ./... && go test ./...` in touched modules.

## Assumptions & Contingencies
- If binary filename `bornite` is required by an external launcher/process argv[0], retain the binary filename while placing source code under canonical `bornite` directory.
