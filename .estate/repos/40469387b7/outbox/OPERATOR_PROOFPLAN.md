# OPERATOR_PROOFPLAN.md

repo_root=/home/toxic/development/estate | repo_hash=40469387b7 | run_id=20261016T030439Z-27f514 | agent_id=e5b8cab5 | cycle=1

[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|1|BOOTSTRAP|L000001] {"event":"transport_verified","mode":"ssh_pc_ts","user":"root"}
[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|1|SNAPSHOT|L000002] {"event":"runtime_snapshot","pe":"pe_ce21ca2b8454b434","repo":"empty"}
[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|1|OPERATE|L000003] {"event":"proof_plan_authored","artifact":"OPERATOR_PROOFPLAN.md"}
[CHR|40469387b7|e5b8cab5|OPERATOR|20261016T030439Z-27f514|1|PROOF|L000004] {"event":"proof_plan_written","lines":121}

## 1. Runtime snapshot (remote awrawr-pc via ssh pc-ts)

Evidence: ⟦PE:pe_ce21ca2b8454b434⟧ (probe transcript, not reproduced here).

| Item | Value | Expected | Verdict |
|---|---|---|---|
| git | 2.55.0 | present | OK |
| python3 | 3.14.7 | present | OK |
| bash | 5.3.15(1)-release x86_64-pc-linux-gnu | present | OK |
| tmux | server NOT running (no /tmp/tmux-0/default) | none | OK |
| estate processes | none (`ps aux \| grep -i estate` empty) | none | OK |
| estate listeners | none | none | OK |
| env estate/proxy | none set | none | OK |
| /home disk | 170G avail of 928G (82% used) | >10G free | OK |
| repo state | NOT a git repo; only `.estate/` skeleton | empty | OK |

Non-estate listeners (pre-existing host services, informational only): sshd 0.0.0.0:22 (transport),
tailscaled 100.72.199.93:443/5252 and 100.108.135.48:54646, dnsmasq 10.0.0.218:53,
systemd-resolve 0.0.0.0:5355, syncthing 127.0.0.1:18384, dockerd 127.0.0.1:20130,
next-server 127.0.0.1:20128, java 100.72.199.93:39557 / 172.19.0.1:32907 / 10.0.0.218:37269,
code-insiders 127.0.0.1:52118, codebase-memory 127.0.0.1:25195, uvicorn 127.0.0.1:25194,
flock 127.0.0.1:25193, python 127.0.0.1:25198/25199, openfang 127.0.0.1:25196.

Hazards for the scaffold cluster:
- No global git identity (`user.name` / `user.email` unset) and `init.defaultBranch` unset.
  The scaffold MUST set these or every commit will fail.
- `hub/registry.json` advertises `active_coord_tmux: estate_40469387b7_coord`, but that tmux
  session does not exist (tmux server down). Coordinator must create it.
- `state.json` records `dirty: NOT_A_GIT_REPO`, `head: ""`, `cycle: 0` — matches observation.

## 2. Minimal repro for the CURRENT empty state

Run from repo_root; proves the baseline (nothing built yet).

```
cd /home/toxic/development/estate && git status         # exit 128: fatal: not a git repository
cd /home/toxic/development/estate && ls -A              # exactly ".estate"
cd /home/toxic/development/estate && git rev-parse HEAD # exit 128: fatal: not a git repository
```

## 3. Fast checks after a scaffold cluster

All must pass, in order, from repo_root:

1. `git status -sb` -> `## No commits yet on <branch>` plus untracked source files.
   Must NOT report the `fatal:` not-a-repo error.
2. `git rev-parse HEAD` -> a 40-hex SHA (non-empty). Baseline was exit 128.
3. `git ls-files` -> lists scaffold files (e.g. `README.md`, source); MUST NOT list any
   path under `.estate/`. Fail if `.estate` appears.
4. `bash tests/smoke_test.sh` -> exit 0 (only if the cluster created the script; if absent,
   treat as NOT-YET-APPLICABLE, do not auto-fail).
5. `git stash list` -> empty (clean tree, nothing stashed) for the baseline scaffold.

## 4. Test hooks — coordinator proof command per cluster candidate

Canonical proof command (run this one):

```
cd /home/toxic/development/estate && git status -sb
```

Alternative (when the candidate claims a commit exists):

```
cd /home/toxic/development/estate && git rev-parse HEAD
```

PASS excerpt (first ~5 lines) for the canonical command:

```
## No commits yet on main
?? README.md
?? src/
?? tests/smoke_test.sh
```

Interpretation: line 1 proves a git repo with an unborn branch; `??` lines are untracked
scaffold files. If any line begins `## <branch>...ahead`, or `.estate` is tracked, reject.
A candidate still printing `fatal: not a git repository` FAILS.

## 5. Rollback verification (git-based only)

Pre-git state restore (cluster must not have committed anything):

```
cd /home/toxic/development/estate && git stash list && git stash
cd /home/toxic/development/estate && git reset --hard HEAD
cd /home/toxic/development/estate && rm -rf .git && git status
```
Expected after `rm -rf .git`: exit 128 `fatal: not a git repository` — baseline restored.

Post-first-commit restore (keep the repo, drop working-tree changes):

```
cd /home/toxic/development/estate && git stash list
cd /home/toxic/development/estate && git reset --hard HEAD
cd /home/toxic/development/estate && git clean -nd
```

Rollback rules: never touch `.estate/`; never `rm -rf` outside the repo root; confirm
`git ls-files | grep .estate` is empty both before and after.

## 6. Bottom line

Recommended proof command for every cluster candidate:

```
cd /home/toxic/development/estate && git status -sb
```

One line. Exit 0, first line `## No commits yet on <branch>` (or `## <branch>` post-commit),
and no `.estate` entry anywhere in the output.
