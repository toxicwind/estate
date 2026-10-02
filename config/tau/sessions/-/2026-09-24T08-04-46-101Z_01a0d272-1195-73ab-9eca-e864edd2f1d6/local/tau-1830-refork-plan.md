# Clean tau re-fork at upstream v18.3.0 — plan

## Context

`~/sovereign/projects/tau` is currently the OLD tau fork (fork point `v18.1.18`, `current_version: "18.2.8"`, local mirror stale at `v18.2.6`). It was restored from `/home/toxic/deprecated-tau-20260924T083357Z` for one reason only: to write `docs/porting-from-oh-my-pi.md` (done; backup copy at `/tmp/keep-tau-doc/porting-from-oh-my-pi.md`). The user directive is: deprecate the old tree again and recreate `projects/tau` clean by pulling upstream `v18.3.0` (tag sha `62bc57be1b03ef0802a33cf7f5f530e534527531`, published 2026-09-24T02:21:31Z, confirmed latest via `gh release list -R can1357/oh-my-pi --json`). End state: `projects/tau` is a pristine `v18.3.0` tree plus preserved tau-owned files, `config.yaml` fork point `v18.3.0`, merge scripts re-based, old tree back under the deprecation root, change committed and pushed in `~/sovereign`. Tau has no nested `.git`; it is tracked directly by the `~/sovereign` repo.

## Approach

### Step 1 — Preflight (read-only, abort on mismatch)

Run and confirm each expected value before touching anything:

1. `cat /tmp/deprecated-root.txt` → must print `/home/toxic/deprecated-tau-20260924T083357Z`; `ls "$DEP" | grep -c '^sovereign__projects__tau'` → must print `0` (slot free for re-deprecation).
2. `git -C ~/scratch/oh-my-pi-upstream rev-parse v18.3.0` → must print `62bc57be1b03ef0802a33cf7f5f530e534527531`.
3. `git -C ~/scratch/oh-my-pi-upstream ls-tree v18.3.0 docs/porting-from-pi-mono.md` → must print a blob line (template present at the new fork point).
4. `ls -d ~/sovereign/projects/tau/.git` → must FAIL (no nested repo; if a `.git` exists, stop — nesting assumption broken).
5. `cmp -s /tmp/keep-tau-doc/porting-from-oh-my-pi.md ~/sovereign/projects/tau/docs/porting-from-oh-my-pi.md && echo DOC_OK` → must print `DOC_OK`.

### Step 2 — Preserve tau-owned files (old tree → /tmp/tau-preserve-1830/)

Create `/tmp/tau-preserve-1830/` and copy exactly these (parents included, no node_modules anywhere):

- `docs/porting-from-oh-my-pi.md`
- `upstream-changes/` (whole dir: config.yaml, scripts/, patches/, modules/, README.md)
- `launcher/` (whole dir)
- `MIRROR-DIFF-vs-upstream.md`
- `README-FORK.md`

Verify with `find /tmp/tau-preserve-1830 -type f | wc -l` (must be > 10) and `grep -r node_modules /tmp/tau-preserve-1830 --include='*' -l | wc -l` (must be 0; just a path-name sanity check — copy commands below never touch node_modules).

### Step 3 — Re-deprecate the old tree (sovereign index + filesystem)

1. `git -C ~/sovereign rm -r --quiet projects/tau` — removes all sovereign-tracked tau files from index and worktree. Untracked leftovers (node_modules, dist, .omp, target, *.bak, *.tmp) stay on disk; that is expected.
2. `DEP=$(cat /tmp/deprecated-root.txt); mv ~/sovereign/projects/tau "$DEP/sovereign__projects__tau"` — moves the leftover-untracked remainder into deprecation. Untracked is preserved, never deleted.
3. Verify: `ls -d ~/sovereign/projects/tau` must FAIL (original gone); `ls "$DEP/sovereign__projects__tau/package.json"` must succeed; `git -C ~/sovereign status --porcelain -- projects/tau | grep -v '^D ' | head` must print nothing (only deletions staged under that path).

### Step 4 — Re-fork clean at v18.3.0 (mirror → projects/tau)

1. `mkdir -p ~/sovereign/projects/tau`
2. `git -C ~/scratch/oh-my-pi-upstream archive v18.3.0 | tar -x -C ~/sovereign/projects/tau/` — pristine tree, no `.git`, no node_modules, no build output.
3. Verify: `test -f ~/sovereign/projects/tau/package.json && test -f ~/sovereign/projects/tau/docs/porting-from-pi-mono.md && test ! -e ~/sovereign/projects/tau/.git && echo FORK_OK` must print `FORK_OK`; `python3 -c "import json;d=json.load(open('/home/toxic/sovereign/projects/tau/package.json'));print(d['name'])"` must print `omp`.

### Step 5 — Restore preserved tau-owned files into the fresh tree

Copy each preserved path from `/tmp/tau-preserve-1830/` back to the same relative path under `~/sovereign/projects/tau/` (docs/porting-from-oh-my-pi.md, upstream-changes/, launcher/, MIRROR-DIFF-vs-upstream.md, README-FORK.md). Verify `test -f ~/sovereign/projects/tau/docs/porting-from-oh-my-pi.md && test -f ~/sovereign/projects/tau/upstream-changes/config.yaml && test -d ~/sovereign/projects/tau/launcher && echo RESTORE_OK`.

### Step 6 — Re-base config and merge scripts to v18.3.0 (exact edits)

`config.yaml` (`~/sovereign/projects/tau/upstream-changes/config.yaml`): the `engine.dir` value is stale — no `engine/` subdir exists (verified missing); the fork tree lives at the tau root, which holds `packages/` directly.

1. Line 9 `fork_point_tag: v18.1.18` → `fork_point_tag: v18.3.0`.
2. Line 10 `current_version: "18.2.8"` → `current_version: "18.3.0"`.
3. Line 19 `dir: /home/toxic/sovereign/projects/tau/engine` → `dir: /home/toxic/sovereign/projects/tau`.
4. Line 4 comment `Verified fork point: upstream tag v18.1.18 (MIRROR-DIFF-vs-upstream.md §2).` → `Verified fork point: upstream tag v18.3.0 (nightly re-fork 2026-09-24; prior v18.1.18 in MIRROR-DIFF-vs-upstream.md §2).`

`merge.sh` (`upstream-changes/scripts/merge.sh`): line 15 `ENGINE=/home/toxic/sovereign/projects/tau/engine` → `ENGINE=/home/toxic/sovereign/projects/tau`; line 17 `BASE_TAG=v18.1.18` → `BASE_TAG=v18.3.0`; in the rsync block add `--exclude='upstream-changes/' --exclude='launcher/' --exclude='MIRROR-DIFF-vs-upstream.md' --exclude='README-FORK.md'` so future overlays don't feed tau-owned scaffolding into the worktree as pseudo-delta.

`ingest.sh` (`upstream-changes/scripts/ingest.sh`): line 14 `ENGINE=/home/toxic/sovereign/projects/tau/engine` → `ENGINE=/home/toxic/sovereign/projects/tau`; line 15 `BASE_TAG=v18.1.18` → `BASE_TAG=v18.3.0`; in the python skip tuple add `'/upstream-changes/'`, `'/launcher/'`.

`promote.sh` (`upstream-changes/scripts/promote.sh`): line 12 `ENGINE=/home/toxic/sovereign/projects/tau/engine` → `ENGINE=/home/toxic/sovereign/projects/tau`; in the adopt rsync block add `--exclude='upstream-changes/' --exclude='launcher/' --exclude='MIRROR-DIFF-vs-upstream.md' --exclude='README-FORK.md'`.

### Step 7 — Re-apply tau divergences from the deprecated copy (guarded)

Source root for old tau files: `$DEP/sovereign__projects__tau` where `DEP=$(cat /tmp/deprecated-root.txt)`. Ground truth is the §"Tau Ground-Truth Divergences" table in `docs/porting-from-oh-my-pi.md`.

1. `bre.rs` (tau-deleted): `rm ~/sovereign/projects/tau/crates/pi-builtins/src/bre.rs`. Verify `test ! -e` passes.
2. For each of `crates/pi-builtins/src/grep.rs`, `crates/pi-builtins/src/sed.rs`, `packages/ai/src/auth-storage.ts`: first run `git -C ~/scratch/oh-my-pi-upstream diff --quiet v18.2.6..v18.3.0 -- <path>`:
   - Exit 0 (upstream untouched 18.2.6→18.3.0): `cp "$DEP/sovereign__projects__tau/<path>" ~/sovereign/projects/tau/<path>` verbatim — provably safe.
   - Exit 1 (upstream changed the file): still `cp` the tau version (tau owns the divergence per the porting doc), then append one line to that file's row context by adding a `> NOTE 2026-09-24: upstream v18.3.0 also touched this file; tau divergence kept verbatim, needs semantic review` line directly under the `### Tau Ground-Truth Divergences` heading in `docs/porting-from-oh-my-pi.md` naming the file. Do not attempt a semantic merge.
3. `packages/ai/src/auth-storage/` split dir and `packages/coding-agent/src/debug/`: leave as the fresh `v18.3.0` tree has them; both rows are already `REVIEW_NEEDED` in the porting doc — do not create, delete, or invent either.
4. Scope rename (`@oh-my-pi/*` → `@toxicwind/*`, currently 0 files renamed), binary `~/.local/bin/tau`, and config `~/.tau`: explicitly out of scope — touch none of them, run no `bun install`, run no build, run no tau binary.

### Step 8 — Stage, commit, push in ~/sovereign

1. `git -C ~/sovereign add -A projects/tau` (the prior `git rm` deletions plus the fresh tree fold into one change; the ~15k pre-existing staged renames under `projects/tau` are unrelated prior state — do not unstage or resolve them).
2. `git -C ~/sovereign status --porcelain -- projects/tau | wc -l` — record the number in the final report.
3. `git -C ~/sovereign commit -m "chore(tau): clean re-fork at upstream v18.3.0 (deprecate pre-18.3.0 tree)" -m "Old tree preserved at $(cat /tmp/deprecated-root.txt)/sovereign__projects__tau. Fork point v18.1.18 -> v18.3.0 (62bc57be). Tau divergences re-applied per docs/porting-from-oh-my-pi.md ground-truth table."`
4. `git -C ~/sovereign push origin $(git -C ~/sovereign branch --show-current)`

## Critical files & anchors

- `sovereign/projects/tau/upstream-changes/config.yaml` — lines 9–10 (fork_point_tag, current_version), line 18–19 (engine.dir); sole source of fork-point truth the scripts should read.
- `sovereign/projects/tau/upstream-changes/scripts/merge.sh` — lines 13–18 (UC/MIRROR/ENGINE/WORKROOT/BASE_TAG) plus rsync excludes; synthetic DAG builder.
- `sovereign/projects/tau/upstream-changes/scripts/ingest.sh` — lines 12–16 (paths/BASE_TAG) plus python skip tuple; airlock classifier.
- `sovereign/projects/tau/upstream-changes/scripts/promote.sh` — lines 11–13 (UC/ENGINE/WORKROOT) plus adopt rsync; gated adopter.
- `sovereign/projects/tau/docs/porting-from-oh-my-pi.md` — §"Tau Ground-Truth Divergences" table; only divergence authority, every row has a re-apply command.

## Verification

End-to-end proof after Step 8, all from `~/sovereign`:

1. `ls -d projects/tau packages 2>/dev/null; ls deprecated 2>/dev/null || echo no-deprecated-in-repo` — fresh `projects/tau` exists in-repo; deprecation root stays outside the repo (it lives at `/home/toxic/deprecated-tau-…`, never under `~/sovereign`).
2. `git -C ~/scratch/oh-my-pi-upstream diff --stat v18.3.0 -- projects 2>/dev/null; diff -rq --exclude=.git --exclude=node_modules --exclude=upstream-changes --exclude=launcher --exclude=porting-from-oh-my-pi.md --exclude=MIRROR-DIFF-vs-upstream.md --exclude=README-FORK.md --exclude=bre.rs --exclude=grep.rs --exclude=sed.rs --exclude=auth-storage.ts <(git -C ~/scratch/oh-my-pi-upstream archive v18.3.0 | tar -t | sort) <(cd projects/tau && find . -path ./node_modules -prune -o -type f -print | sort)` — simplified check: `for f in package.json docs/porting-from-pi-mono.md Cargo.toml bun.lock; do cmp -s <(git -C ~/scratch/oh-my-pi-upstream show v18.3.0:$f) projects/tau/$f && echo "SAME $f" || echo "DIFF $f"; done` — all four must print SAME.
3. `grep -E 'fork_point_tag|current_version' projects/tau/upstream-changes/config.yaml` — must show `v18.3.0` and `"18.3.0"`.
4. `grep -n 'tau/engine' projects/tau/upstream-changes/config.yaml projects/tau/upstream-changes/scripts/*.sh | wc -l` — must print 0 (no stale engine subpath references).
5. `test ! -e projects/tau/crates/pi-builtins/src/bre.rs && echo BRE_GONE; grep -c REVIEW_NEEDED projects/tau/docs/porting-from-oh-my-pi.md` — must print BRE_GONE and 3.
6. `git -C ~/sovereign log --oneline -1` shows the chore(tau) commit; `git -C ~/sovereign status --porcelain -- projects/tau | wc -l` is 0 after commit (or only pre-existing unrelated entries the implementer names in the report).

## Assumptions & contingencies

- `git archive v18.3.0 | tar -x` is assumed to reproduce the tag tree byte-identical (upstream publishes no LFS/smudge filters affecting text; verification check 2 proves it — if any of the four files prints DIFF, stop and report, do not proceed to commit).
- If `git archive` fails (mirror unreachable/corrupt), do: `git -C ~/scratch/oh-my-pi-upstream fetch --tags origin && retry once`; if still failing, `git clone --branch v18.3.0 --depth 1 https://github.com/can1357/oh-my-pi.git /tmp/tau-fresh-1830 && rm -rf /tmp/tau-fresh-1830/.git` and copy its contents into `projects/tau/` instead of the archive pipe, then continue at Step 4.3.
- If `git push` fails (auth/network), leave the commit in place, verify everything else, and report `PUSH_FAILED` with the exact stderr — do not retry more than once, do not force-push.
- `~/.local/bin/tau`, `~/.local/bin/omp`, `~/.tau`, `~/.omp` are runtime artifacts of the old build and stay untouched; the fresh tree has no built binary until a later explicit build — report `BINARY_STALE` (expected) rather than treating it as failure.
