# Zed sync strategy: embedded QED snapshot ↔ `toxicwind/sovereign-zed`

Status 2026-09-20 (zed-qed). This is the plan, not the execution — the
merge itself is a separate, scheduled operation (see §5).

## 1. What the two trees are

| | `projects/qed/zed` (embedded) | `toxicwind/sovereign-zed` |
|---|---|---|
| Form | Snapshot vendored into sovereign-projects | Full-history fork of `zed-industries/zed` |
| History in sovereign-projects | 2 commits (imported 2026-09-07, `1900610cf3` de-submodule) | Not present |
| Shared ancestry | **None** — file copy, not subtree/filter-repo | Full upstream + fork history |
| Version (workspace `Cargo.toml`) | 0.61 (app 1.13.0-era) | 0.61 (app 1.17.0-era) |
| Sovereign deltas | Schema-normalizer extraction (`a87f5e5189`), provider set | Custom providers (pre-extraction triplicated normalizers) |
| Diff surface (2026-09-20) | 697 differing files, 16 paths only here, 299 only there | — |

Neither tree is blindly replaceable: the embedded tree carries today's
committed repair (`a87f5e5189`); the fork carries newer upstream (1.17.0)
plus full history.

## 2. Goal

One canonical zed tree with **full history preserved** (no snapshot
re-imports, no squashed ancestry), sovereign customizations retained,
and a repeatable forward-sync path.

## 3. Strategy: subtree graft, then re-apply deltas

1. **Provenance pin.** Identify the `sovereign-zed` commit the snapshot
   was taken from (compare `crates/zed/Cargo.toml` version + `git log -S`
   on distinctive files; tree-hash comparison if needed). Record it here.
2. **Graft history.** In sovereign-projects:
   ```bash
   git remote add sovereign-zed https://github.com/toxicwind/sovereign-zed.git
   git fetch sovereign-zed main
   git subtree add --prefix=projects/qed/zed sovereign-zed main
   ```
   This imports the fork's full history and merges it with the snapshot.
   Expect conflicts in ~697 files — resolve by taking the **fork's**
   version except for the QED-owned delta list (§4).
3. **Re-apply QED deltas** (§4) on top of the merged tree.
4. **Proof.** Run the full QED proof pipeline
   (`cargo check --package zed`, zedra workspace check, biome).
5. **Retire the snapshot mindset.** Future syncs are `git subtree pull`.

## 4. QED-owned deltas to preserve (as of `a87f5e5189`)

- `zed/crates/language_models/src/schema_normalizer.rs` (+ `mod` in
  `language_models.rs`) — triplicated Outlines normalizer extracted from
  `provider/{openai_mcpproxy,openai_mcpproxy_nvidia,nvidia}.rs`, incl. the
  nullable-recursion fix (`["object","null"]` keeps array form).
- `projects/qed/zedra/*` workspace repair (sibling tree, unaffected by
  the graft but verify paths still resolve post-merge).
- `projects/qed/README.md` verify section, `zed/AUDIT.md` canonical path.

## 5. Scheduling

Do NOT run the graft during fleet-wide upgrade windows (today's `-Syu`
is an example) or while other crews hold dirty QED state. Announce in
squawk fleet before starting; the merge conflicts touch the same 697
files every QED worker reads.

## 6. Non-goals

- No PRs against `zed-industries/zed` (fork policy).
- No force-push; fetch-first throughout.
- No replacement of either tree without the graft — a fresh snapshot
  would destroy the history this strategy exists to preserve.
