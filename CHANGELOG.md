# Changelog

## 2026-09-30 — README deconfusion (ranch flatten)

- Deconfused against `origin/main` (`a4058ca79e`): the ranch flattened to one
  directory per component on 2026-09-30, so every `stockyard/` / `remuda/`
  path in this README was stale. Fixed: Tier 2 table, name-collisions table,
  repo-layout tree, key-components sections, docs index, conventions.
- `projects/range/ranch/corral/` (absorbed in-tree) and `projects/guidellm/`
  (renamed to roundup, moved into the ranch) removed from the Tier 2 table.
- The `projects/range/ranch` gitlink in this repo's index is stale — a fresh
  clone leaves that directory empty; the live ranch is `toxicwind/ranch`.
- `projects/sigma/` (billion-context fork) is gone from this tree and
  `pitchfork.toml` has no sigma/bili daemon; the compression section is now
  marked historical. Remnants: `tools/bili-deploy.sh`,
  `config/tau/agent/config.yml`.
- Daemon count re-checked: **79** pitchfork `[daemons.*]` sections.
- Added `CHANGELOG.md`, `CODE_OF_CONDUCT.md`.

## 2026-09-27 — Full verification pass

- Every port row, layout path, component path, task definition, and relative
  link re-checked against the live tree on `forge/gate-retire-final`
  (76 daemons at the time).
