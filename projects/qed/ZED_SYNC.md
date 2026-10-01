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
2. **Graft history.** In sovereign-projects, on a fresh branch, announced
   in squawk fleet (§5):
   ```bash
   git remote add sovereign-zed https://github.com/toxicwind/sovereign-zed.git
   git fetch sovereign-zed main

   # Pin the snapshot before touching it.
   git tag qed-zed-snapshot-$(date +%Y%m%d)

   # `git subtree add` refuses an existing prefix
   # (receipt 2026-10-01: `fatal: prefix 'X' already exists.`), so move
   # the snapshot aside and commit the removal first.
   git mv projects/qed/zed projects/qed/zed.snapshot
   git commit -m "qed: stage snapshot aside for sovereign-zed subtree graft"

   # Import the fork's full history under the canonical prefix.
   git subtree add --prefix=projects/qed/zed sovereign-zed main
   ```
   The snapshot remains in git at `projects/qed/zed.snapshot` on this
   branch. Expect conflicts in ~697 files — resolve by taking the
   **fork's** version except for the QED-owned delta list (§4).
3. **Re-apply QED deltas** (§4) on top of the graft. The QED delta commits
   sit on top of the snapshot, so cherry-pick them onto the merged tree:
   ```bash
   for c in a87f5e5189 db4179319a 7ac0dc03b6; do git cherry-pick -n "$c"; done
   ```
   Conflict strategy per file class:
   - Sovereign-authored files (`schema_normalizer.rs`, `zedra/*`,
     `README.md`, `ZED_SYNC.md`) — take the QED version outright.
   - `settings_ui` 2-line `autonomous_edits` fix — apply by hand if the
     fork's provider page drifted.
   - Provider files where the fork still carries the triplicated
     normalizers — do NOT take the old extraction patch; redo the
     extraction (`schema_normalizer.rs` + nullable-recursion fix) against
     the fork's current provider files, then delete the triplicated code.
   Remove `projects/qed/zed.snapshot` and commit only after the proof
   pipeline (§3.4) passes.
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

## 7. Validated notes (2026-10-01, QED lane)

- `git subtree add --prefix=X` on an existing prefix fails:
  `fatal: prefix 'X' already exists.` — §3.2 now moves the snapshot
  aside first. The old single-command recipe was not executable.
- `toxicwind/sovereign-zed` exists and is reachable
  (`gh repo view toxicwind/sovereign-zed` returns
  `https://github.com/toxicwind/sovereign-zed`).
- `cargo fmt -p language_models` clean (3 pre-existing diffs in
  `provider.rs`, `provider/open_ai_compatible.rs`, `settings.rs` fixed
  2026-10-01).
- `README.md` mermaid/tree references corrected: the fork is
  `toxicwind/sovereign-zed`, not `toxicwind/zed` (no such repo in
  `gh repo list toxicwind`).
