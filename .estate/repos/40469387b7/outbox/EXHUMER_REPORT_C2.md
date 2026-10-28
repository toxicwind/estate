# EXHUMER REPORT - cycle 2 (entropy / hotspots / brittleness)

repo_hash=40469387b7 run_id=20261016T030439Z-27f514 cycle=2 agent=e5b8cab5
snapshot=⟦PE:pe_78b1e680b4774e5a⟧ cycle1_synthesis=⟦PE:pe_ce21ca2b8454b434⟧ cycle1_proof=⟦PE:pe_db0898a9fa7c9266⟧
scope: read-only probes via ssh pc-ts. No repo or .estate writes.

## Event stream
[CHR|40469387b7|e5b8cab5|EXHUMER|20261016T030439Z-27f514|2|EXHUME|L000001] {"phase":"PROBE_PERMS","targets":["/home/toxic","development","estate","README.md","tests/smoke_test.sh"],"root_owned":6,"world_writable":0}
[CHR|40469387b7|e5b8cab5|EXHUMER|20261016T030439Z-27f514|2|EXHUME|L000002] {"phase":"PROBE_IDENT","user":"toxic","uid":1000,"sudo_nopasswd_all":true,"home_mode":"700"}
[CHR|40469387b7|e5b8cab5|EXHUMER|20261016T030439Z-27f514|2|EXHUME|L000003] {"phase":"EXEC_AS_TOXIC","cmd":"bash tests/smoke_test.sh","result":"SMOKE_OK","rc":0}
[CHR|40469387b7|e5b8cab5|EXHUMER|20261016T030439Z-27f514|2|EXHUME|L000004] {"phase":"EXEC_AS_TOXIC","cmd":"git status","error":"detected dubious ownership","rc":128}
[CHR|40469387b7|e5b8cab5|EXHUMER|20261016T030439Z-27f514|2|EXHUME|L000005] {"phase":"PROBE_GIT","remotes":0,"branches":1,"tags":1,"commits":2,"fsck":"clean","status":"clean"}
[CHR|40469387b7|e5b8cab5|EXHUMER|20261016T030439Z-27f514|2|EXHUME|L000006] {"phase":"PROBE_TOOLING","bash_n":"SYNTAX_OK","py_files":0,"git_version":"2.55.0","ignored_paths":[".estate/"]}
[CHR|40469387b7|e5b8cab5|EXHUMER|20261016T030439Z-27f514|2|EXHUME|L000007] {"phase":"DRY_RUN","cmd":"git clean -ndx","would_remove":[".estate/"],"verdict":"CATASTROPHIC"}
[CHR|40469387b7|e5b8cab5|EXHUMER|20261016T030439Z-27f514|2|EXHUME|L000008] {"phase":"RANK","top_risk":"R1_state_annihilation_via_git_clean_x","surgeon_targets":3}

## 1. Permission / ownership brittleness

| path | mode | owner | toxic read | toxic write | toxic exec |
|---|---|---|---|---|---|
| /home/toxic | 700 | toxic:toxic | yes (owner) | yes | yes |
| /home/toxic/development | 755 | root:root | yes | no | traverse |
| estate/ | 755 | root:root | yes | no | traverse |
| README.md | 644 | root:root | yes | no | - |
| tests/ | 755 | root:root | yes | no | traverse |
| tests/smoke_test.sh | 755 | root:root | yes | no | yes |
| .git/ (+config, objects) | 755/644 | root:root | yes | no | traverse |
| .estate/ (all subtrees) | 755 | root:root | yes | no | traverse |

Verified empirically:
- Smoke test as toxic: `SMOKE_OK`, rc=0. Runnable. The 700 home dir does NOT block toxic, because toxic OWNS it and is the process owner. Path traversal succeeds end-to-end.
- Every git command as toxic: `fatal: detected dubious ownership in repository`, rc=128. Repo + .git are root-owned, so git 2.55.0 safe.directory protection refuses. Git is effectively root-only.

Risk quantification: 6 of 6 tracked/metadata paths are root:root; 0 are writable by toxic; only 1 of 6 is executable-by-others. Read/exec is fine; WRITE is 0% available to toxic without sudo.

CRITICAL AMPLIFIER: toxic holds `(ALL) NOPASSWD: ALL` (plus 3 more NOPASSWD:ALL entries and `SETENV: NOPASSWD: ALL`). The 700 home directory is therefore security theater - zero isolation. Any "fix" that relies on unix permissions alone (chmod 700, chown toxic) provides no security boundary, only a confusing failure mode. Conversely it means an ownership fix can be applied at any time without an outage window.

## 2. Git brittleness

- Remote: none configured. No push target, no redundancy, no off-box recovery path. Disk loss = total loss of both the scaffold and .estate (which lives only on this filesystem).
- Branching: single branch `main`, no other refs. No `dev`/topic isolation; every mutation lands directly on the anchor's descendant.
- Tag hygiene: `refs/tags/pre-cluster` -> 2d9b5cb directly. It is a LIGHTWEIGHT tag (points at a commit object, no tag object) - no tagger, no timestamp, no signature. It can be silently moved or deleted with no audit trail. The commit itself IS genuinely empty and IS a valid rollback anchor (diff vs HEAD = only the 3 added files, 12 insertions).
- Identity: no `/root/.gitconfig`, no `/etc/gitconfig`, no local user.name/user.email. Every commit depends on ad-hoc `-c user.name=... -c user.email=...` injection. A bare `git commit` fails with "Author identity unknown".
- state.json hygiene bug: `dirty` field holds `"## main"`. That is the branch-status header emitted by `git status -sb` (the cycle-1 proof_cmd), not a dirtiness value. Branch name and cleanliness have been conflated; a clean tree is recorded as dirty-looking. Consumers keying on `dirty` will misclassify every cycle.

DANGEROUS COMMANDS (exact, do-not-run):
- `git clean -fdx`  <-- PRIMARY. `-x` defeats .gitignore, so `.estate/` is deleted. Confirmed by dry run: `Would remove .estate/`. This annihilates hub/registry.json, hub.lock, repo.lock, state.json, manifest.json, all outbox/ artifacts, and every artifact PE snapshot + proof. Irreversible: no remote.
- `git clean -dffdx`, `git clean -fdx .` (same effect, easier to typo into)
- `git clean -X` / `-XX` (removes ONLY ignored files - i.e. exactly .estate/, the worst subset)
- `git reset --hard pre-cluster && git clean -fdx` - the cycle-1 AGGREGATE rollback recipe correctly uses `-fd` (safe, .estate survives because it is ignored, not untracked). Any future "hardening" of that recipe to `-fdx` inverts it into state destruction. Treat that recipe line as a booby trap.
- `git tag -d pre-cluster` or `git update-ref -d refs/tags/pre-cluster` - destroys the only rollback anchor
- `git reflog expire --expire=now --all && git gc --prune=now` - makes the empty baseline unreachable
- `git checkout --orphan`, `git filter-branch`, `git filter-repo`, `git push --force` (no remote, so last is a no-op error)
- `rm -rf .estate` - trivial, and because it is gitignored, git will not even warn that it vanished

## 3. Tooling warnings / errors

- `git fsck --full --strict`: clean, zero output. No dangling, missing, or corrupt objects.
- `git status --porcelain=v1`: clean tree. No modified, staged, or untracked entries.
- `git status --ignored`: exactly one ignored path, `.estate/`. No stray __pycache__ or *.pyc (the .gitignore entries for them are speculative - no Python exists in the repo yet).
- `bash -n tests/smoke_test.sh`: SYNTAX_OK.
- Python compile checks: N/A - zero `.py` files under the repo (outside .git).
- The ONLY error raised by any probe: `fatal: detected dubious ownership in repository` (rc=128) when git runs as toxic.
- HEAD 24fe5bb matches state.json `head` - consistent.

## 4. Top-5 risks, ranked

R1 (CRITICAL) - State annihilation via `git clean -fdx`. `.estate/` is ignored, so `-x` deletes it; dry run confirms. No remote, no backup. One keystroke destroys all cycle state and every PE proof. Likelihood: moderate (rollback recipes are actively being iterated). Impact: total.
R2 (HIGH) - Root-only git + zero-writable-to-toxic repo. Smoke test runs as toxic but git does not; any coordinator step that is not root silently fails with rc=128. The failure is loud (good) but it will be misread as corruption, not ownership.
R3 (HIGH) - Lightweight `pre-cluster` tag with no remote. The single rollback anchor is unsigned, undated, movable, and exists on exactly one disk.
R4 (MEDIUM) - `(ALL) NOPASSWD: ALL` for toxic. Renders the 700 home dir and all unix permissions meaningless as a security boundary; ownership "fixes" will be mistaken for hardening.
R5 (MEDIUM) - state.json `dirty` field stores the `git status -sb` header `"## main"`. Semantic corruption of cycle bookkeeping; propagates to every future cycle's proof gate.

## 5. Three targets for SURGEON this cycle

T1 - Guardrail against state annihilation (highest value, smallest diff). Make `.estate/` un-deletable-by-git-accident. Preferred: stop relying on `.gitignore` as the protection and add an explicit tracked tripwire plus a pre-clean guard. Concretely, add a `tests/smoke_test.sh` assertion that fails if `.estate/` is absent, so `git clean -fdx` damage is detected on the very next smoke run instead of silently corrupting cycle N+1. Alternative/complement: a repo-local `pre-clean` hook is NOT possible (git has no pre-clean hook) - so the tripwire must be in the smoke test or a wrapper script. Do NOT add a `clean` alias that shadows the builtin.
T2 - Ownership + identity normalization. Give the repo a persisted git identity (local user.name/user.email) so commits stop depending on ad-hoc `-c` injection, and document the root-only git constraint. Recommend `chown -R toxic:toxic` on the repo OR a documented `safe.directory` exception - but pick ONE and record it, because the current split (toxic can run tests, cannot run git) is the actual source of confusion. Note explicitly that chmod/chown is NOT a security control here, given R4.
T3 - Tag and state-hygiene hardening. Convert `pre-cluster` to an annotated, signed tag (`git tag -a -s`) so the anchor gains tagger/date/signature and cannot be silently moved, and fix the `dirty` field so it stores a real cleanliness value (clean/dirty) rather than the `git status -sb` header. Both are cheap, reversible, and remove the two quietest failure modes.

## Non-goals / explicit abstentions
- No sibling `*_C2.md` artifacts were read; only cycle-1 published AGGREGATE.md was consulted, as permitted.
- No code, config, or .estate state was modified. This report is the sole write.
- Ranked likelihood figures are judgments from probe evidence, not measurements; no multi-cycle sample exists yet (n=2 commits, n=1 prior cycle).
