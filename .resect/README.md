# resect — estate code-aware mv (first-class)

`@mherod/resect` v1.9.0 (TS compiler-API) is the estate's canonical move/rename
primitive. Installed globally (bun): `~/.bun/bin/resect`, PATH surface
`~/.local/bin/resect`, bin manifest rows `resect` + `resect-mcp`.

## Estate-wide project map (resect --project targets)
| Product | tsconfig | Notes |
|---|---|---|
| pens/olympus/products/kappa/kappa-code | tsconfig.json (root, 43 found) | 38 pkgs; use `-p .` + `--workspace` |
| pens/olympus/products/kilo | tsconfig.json | |
| pens/olympus/products/tau | tsconfig.json | |
| pens/ranch (root) | tsconfig.json | loose component dirs |
| pens/geode/products/chalcopyrite | tsconfig.json | |

## Batch moves
`resect move --batch <moves.json> -p <project> --workspace --journal`
- one project load, one verify gate; `--journal` → `resect undo`
- files: batch files land here as `<topic>-moves.json`

## Gotchas
- Non-TS repos (bornite/Go, thresher/Go, python) are OUT of resect scope — use
  `git mv` + rename-roundup pairs for those.
- resect refuses uncommitted worktrees without `--force`; commit first.
