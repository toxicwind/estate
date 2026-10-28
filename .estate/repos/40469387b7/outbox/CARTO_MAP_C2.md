# CARTO_MAP_C2 - post-scaffold structure graph

[CHR|40469387b7|e5b8cab5|CARTOGRAPHER|20261016T030439Z-27f514|2|CARTO|L00001] {"event":"carto_start","cycle":2,"snapshot_pe":"pe_78b1e680b4774e5a","mode":"read-only"}
[CHR|40469387b7|e5b8cab5|CARTOGRAPHER|20261016T030439Z-27f514|2|CARTO|L00002] {"event":"graph_verified","ok":true,"branch":"main","head":"24fe5bbfb4f1200ad282b4ecee5d9079256f4450","tracked":3,"commits":2}

## 1. Graph vs reality - VERIFIED

```
git log --oneline --all --decorate
* 24fe5bb (HEAD -> main) cluster-a minimal scaffold
* 2d9b5cb (tag: pre-cluster) baseline-cycle1          <-- rollback anchor
git ls-files            : .gitignore  README.md  tests/smoke_test.sh   (3, exact)
git ls-files -s         : 100644 .gitignore | 100644 README.md | 100755 tests/smoke_test.sh
git status --porcelain  : (empty)  -> clean tree, nothing staged/modified
git status --ignored    : !! .estate/              -> whole control plane ignored
git check-ignore -v .estate/state.json
                       : .gitignore:1:.estate/  .estate/state.json  -> rule 1, dir-wide
```

- .estate is NOT tracked (absent from ls-files; ignored by .gitignore:1 rule `.estate/`).
- Worktree modes match index: tests/smoke_test.sh is 0755 and executable in place.
- Diff pre-cluster..HEAD = 3 files / +12 lines only: README.md(+5), .gitignore(+3),
  tests/smoke_test.sh(+4). Cluster-A applied exactly as aggregated; no collateral edits.
- Smoke gate live: `bash tests/smoke_test.sh` -> `SMOKE_OK`, rc=0. Gate is green.
- Baseline sentinel 2d9b5cb is an empty commit; tag `pre-cluster` points at it.

[CHR|40469387b7|e5b8cab5|CARTOGRAPHER|20261016T030439Z-27f514|2|CARTO|L00003] {"event":"ignore_verified","rule":".gitignore:1","pattern":".estate/","tracked_estate":false,"smoke":"SMOKE_OK"}

## 2. Entrypoint graph (ASCII)

AS-BUILT (post-scaffold) - exactly one executable entrypoint:

```
  $ bash tests/smoke_test.sh                     <-- ONLY executable entrypoint (100755)
        +-> set -euo pipefail
        +-> echo SMOKE_OK                        (stdout, no file IO)
        +-> exit 0                               => proof signal for cluster-A gate
        (argv: none | env: none | deps: bash only)
  .estate control plane - NOT an in-repo entrypoint, ignored
  /home/toxic/development/estate
    |-- .estate/hub/hub.lock , registry.json     (repo_hash 40469387b7 -> coord tmux)
    `-- .estate/repos/40469387b7/
           |-- repo.lock   inbox/ (empty)   state.json   manifest.json
           |-- artifacts/  outbox/
           `-- coordinator CLI = ssh pc-ts -> git / tests / state append (outside repo)
```

INTENDED next layer (SURGEON targets, verifiable by coordinator):

```
  $ python -m estate <cmd>                     (src/ layout, package entrypoint) -> v
  src/estate/__main__.py : def main(argv=None) -> int
        |-- argparse subcommands: smoke | map | proof | rollback
        |-- reads/writes ONLY under .estate/repos/<repo_hash>/
        `-- imports: config.py, state.py, io.py
  src/estate/config.py   : CLI flag > CHRONOS_* env > defaults
  src/estate/state.py    : append-only state.json.actions[] checkpoint
  src/estate/io.py       : append-only writes to outbox/ , artifacts/
  tests/smoke_test.sh     : unchanged shell gate; `python -m estate smoke` must also
                            print SMOKE_OK and exit 0 (dual gate, same signal)
```
[CHR|40469387b7|e5b8cab5|CARTOGRAPHER|20261016T030439Z-27f514|2|CARTO|L00004] {"event":"entrypoints","executable_now":["tests/smoke_test.sh"],"intended":["src/estate/__main__.py:main"]}

## 3. Config / env precedence - AS-BUILT vs INTENDED
| Source | AS-BUILT (now) | INTENDED (next layer) |
|---|---|---|
| CLI flag | n/a (no parser exists) | highest: `--repo-root`, `--cycle`, `--cluster` |
| CHRONOS_* env | ABSENT (0 vars set; only PWD matches the string) | middle: CHRONOS_REPO_ROOT, CHRONOS_REPO_HASH, CHRONOS_RUN_ID |
| In-repo config | none | none planned |
| Defaults | only source: smoke hardcodes SMOKE_OK/exit 0; git identity supplied inline by coordinator as `-c user.name=estate-forge -c user.email=forge@awrawr-pc` | fallback: defaults must keep smoke green with zero env |

Risk note: cycle-2 code reading CHRONOS_* must degrade to defaults - no CHRONOS_* variable is
exported in the ssh session, so proof must never depend on env presence.

## 4. IO boundaries per cycle + lock order + rollback anchor

```
REPO (git, tracked)          reads: log/status/ls-files/diff pre-cluster..HEAD
                             writes (cycle1 only): README.md .gitignore tests/smoke_test.sh
CONTROL PLANE (.estate/)    reads: state.json, manifest.json, outbox/AGGREGATE.md,
                                    artifacts/*.b64 (PE snapshots/proofs)
                             writes: repo.lock, hub.lock, registry.json,
                                     state.json (append), outbox/*.md, artifacts/*.b64
LOCK ORDER (mandatory, no inversion)
   1) .estate/repos/40469387b7/repo.lock   <-- acquire FIRST
   2) .estate/hub/hub.lock                 <-- acquire SECOND, release FIRST
   Both are 0-byte, content-free, no stale holders. Reverse order risks cross-repo deadlock.
ROLLBACK ANCHOR
   tag pre-cluster -> 2d9b5cb "baseline-cycle1" (empty commit)
   git reset --hard pre-cluster && git clean -fd
   => tracked tree returns to empty scaffold; .estate/ survives (ignored, not untracked)
      so control-plane state/outbox history persists across rollback.
   cycle1 proof_pe=pe_db0898a9fa7c9266 (git status -sb) is the re-verify target.
```

[CHR|40469387b7|e5b8cab5|CARTOGRAPHER|20261016T030439Z-27f514|2|CARTO|L00005] {"event":"io_boundary","locks":["repo.lock","hub.lock"],"order":"repo_then_hub","rollback_tag":"pre-cluster","rollback_commit":"2d9b5cb"}

## 5. Post-cycle-2 target graph (coordinator verification contract)

After cycle 2 the graph should be: main still on 24fe5bb plus at most one new commit whose
diff is confined to a single named cluster (typically src/estate/__init__.py,
src/estate/__main__.py, src/estate/config.py, src/estate/state.py, src/estate/io.py,
tests/test_estate.py); tests/smoke_test.sh byte-identical to HEAD, mode still 100755, still
printing SMOKE_OK, since it is the only proof that survives `git reset --hard pre-cluster` and
must stay runnable before any python package exists; and `python -m estate smoke` must emit
the identical SMOKE_OK/exit 0 signal so the two gates cannot diverge. CHRONOS_* env stays
unset, so every code path resolves through defaults, with the CLI-flag tier the only way to
override repo_root or run_id. Nothing under .estate/ may ever appear in `git ls-files` or
`git status --porcelain`; it must show only as `!! .estate/` under --ignored. A winning
cluster is verifiable by: clean tree, one new commit, `bash tests/smoke_test.sh` -> SMOKE_OK,
`python -m estate smoke` -> SMOKE_OK if the package was introduced, one append to
state.json.actions[] with cycle/cluster/changed/proof_cmd/proof_pe/head/utc, and
`git reset --hard pre-cluster && git clean -fd` restoring the scaffold while leaving the
control plane intact. Lock order stays repo.lock then hub.lock, and tag pre-cluster remains
the sole anchor: no new tags, no rewritten history, no force-push, no tracked-file churn
outside the winner.
[CHR|40469387b7|e5b8cab5|CARTOGRAPHER|20261016T030439Z-27f514|2|CARTO|L00006] {"event":"carto_done","ok":true,"writes":1,"artifact":"outbox/CARTO_MAP_C2.md","code_modified":false}
