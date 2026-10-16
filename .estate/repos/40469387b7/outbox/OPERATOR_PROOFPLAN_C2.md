# OPERATOR_PROOFPLAN_C2.md
repo_root=/home/toxic/development/estate | repo_hash=40469387b7 | run_id=20261016T030439Z-27f514 | agent_id=e5b8cab5 | cycle=2
snapshot: PE pe_78b1e680b4774e5a | transport: ssh pc-ts (root, key-based) | host: awrawr-pc | mode: READ-ONLY
[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|2|OPERATE|L000001] {"event":"transport_verified","mode":"ssh_pc_ts","user":"root","host":"awrawr-pc"}
[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|2|OPERATE|L000002] {"event":"runtime_snapshot","pe":"pe_78b1e680b4774e5a","repo":"git_main_clean"}
[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|2|OPERATE|L000003] {"event":"probes_executed","git_status_sb":"PASS","smoke_test":"PASS","fsck":"PASS","check_ignore":"PASS"}
[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|2|OPERATE|L000004] {"event":"proof_plan_authored","artifact":"OPERATOR_PROOFPLAN_C2.md"}

## 1. Executed probes (repo_root, read-only, zero mutation)
```
git status -sb                          -> ## main                                 exit 0, clean tree
git log --oneline --decorate -3         -> 24fe5bb (HEAD -> main) cluster-a minimal scaffold
                                           2d9b5cb (tag: pre-cluster) baseline-cycle1
git tag -l                              -> pre-cluster                            exactly one tag
git stash list                          -> (empty)                                nothing stashed
bash tests/smoke_test.sh                -> SMOKE_OK                               exit 0
bash -n tests/smoke_test.sh             -> (no output)                            exit 0, syntax OK
git fsck / git fsck --strict            -> (no output)                            exit 0, no errors/dangling
git check-ignore -v .estate/state.json -> .gitignore:1:.estate/ .estate/state.json   exit 0
git ls-files -s                         -> 100644 .gitignore, 100644 README.md, 100755 tests/smoke_test.sh
tmux ls                                 -> error connecting to /tmp/tmux-0/default (No such file or directory)
ss -ltnp                                -> 124 LISTEN rows, none estate/forge-related
ps (estate/forge scan)                 -> no estate repo process; host agent infra only
```
Verdict: CLEAN. `git status -sb` emits exactly one line `## main` - no staged, modified, or
untracked entries, and nothing under `.estate/` is tracked or reported.

## 2. Runtime snapshot table (remote awrawr-pc)
| Item | Value | Expected | Verdict |
|---|---|---|---|
| git | 2.55.0 | 2.55.0 | OK |
| python3 | 3.14.7 | 3.14.7 | OK |
| bash | 5.3.15(1)-release x86_64-pc-linux-gnu | 5.3.15 | OK |
| HEAD | 24fe5bbfb4f1200ad282b4ecee5d9079256f4450 on main | 24fe5bb | OK |
| tag pre-cluster | present on 2d9b5cb (empty baseline) | present | OK |
| git fsck / --strict | clean, exit 0, no dangling | clean | OK |
| tracked files | .gitignore, README.md, tests/smoke_test.sh (0755) | unchanged | OK |
| .estate ignore | .gitignore:1:.estate/ | ignored | OK |
| tmux | server NOT running | none | OK |
| estate process / listener | none / none of 124 sockets | none | OK |
| host agent infra | pitchfork log-sink x3 (estate/forge, forge-agent, bidder-forge) + bidder.py | informational | INFO |
| host | up 3d 7:19, load avg 3.03 | n/a | INFO |
Non-estate listeners (pre-existing, informational): dockerd 0.0.0.0:43000 and 127.0.0.1:8000,
flicker-agent *:3000. NOTHING new listening or running since cycle 1.

## 3. Canonical single proof command for cycle-2 candidates
Pick exactly one, based on what the candidate cluster does. Both run from repo_root.

(A) FILE-ADD CLUSTER (new files or directories):
```
cd /home/toxic/development/estate && git status -sb
```
PASS excerpt (first ~5 lines, as observed on current HEAD):
```
## main
```
PASS: exit 0; line 1 is `## main`; every other line is a `??` untracked entry, or there are no
other lines at all (clean tree post-commit). FAIL if any line contains `.estate` (ignore rule
broke), if a non-`??` status code appears (M/A/D/R/C) on a file the cluster did not declare, or
if `fatal:` is emitted.

(B) SMOKE-TEST / GUARDRAIL CLUSTER (touches tests/smoke_test.sh or guard logic):
```
cd /home/toxic/development/estate && bash tests/smoke_test.sh
```
PASS excerpt (stdout, as observed on current HEAD):
```
SMOKE_OK
```
PASS: exit 0 and stdout is exactly `SMOKE_OK`. FAIL on extra output, non-zero exit, or a missing
`SMOKE_OK`. Pair with `bash -n tests/smoke_test.sh` (exit 0, silent) as a syntax gate and assert
the file stays mode 0755.

## 4. Rollback verification (git only)
```
cd /home/toxic/development/estate && git reset --hard pre-cluster
cd /home/toxic/development/estate && git clean -fd
```
- `git reset --hard pre-cluster` moves HEAD to 2d9b5cb; `git log --oneline -1` must then print
  `2d9b5cb (HEAD -> main) baseline-cycle1`.
- `git clean -fd` removes untracked entries only. NEVER pass `-x` - it would delete the ignored
  `.estate/` outbox and all cycle state.
- After rollback: `git status -sb` -> `## main` (clean, empty tree); `git fsck` exit 0; `git tag -l`
  still `pre-cluster`; `bash tests/smoke_test.sh` -> non-zero because the script is gone, which is
  the correct empty-baseline signal, not a defect.
```
git stash list                             # empty before AND after
git tag -l                                 # pre-cluster must survive
git check-ignore -v .estate/state.json    # must still match
```
Rules: never `rm -rf` outside repo_root; never touch `.estate/`; `git ls-files | grep .estate`
must be empty both before and after rollback.

## 5. Recommendation - which single proof command
SMOKE-TEST-GUARDRAIL cluster (SURGEON mutates tests/smoke_test.sh, exit codes, or set -euo pipefail
semantics): use `bash tests/smoke_test.sh`. It is the only command that exercises the guardrail;
`git status -sb` is blind to a guardrail regression.
FILE-ADD cluster (new source files, directories, scripts): use `git status -sb`. Cheapest complete
proof that exactly the intended files appeared, nothing pre-existing changed, and `.estate/` stays
untracked.
Tie-breaker: a cluster that both adds files and guards the smoke test still takes
`bash tests/smoke_test.sh` as primary - guardrail correctness dominates layout.

## 6. Bottom line
```
cd /home/toxic/development/estate && git status -sb
```
Default: one line, exit 0, first line `## main`, zero non-`??` entries, zero `.estate` entries.
Swap to `bash tests/smoke_test.sh` iff the candidate is a smoke-test/guardrail cluster.
[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|2|OPERATE|L000005] {"event":"proof_plan_written","recommended_proof_cmd":"git status -sb","alt_guardrail_cmd":"bash tests/smoke_test.sh"}
