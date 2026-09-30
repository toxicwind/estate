# README rollout — crew completion audit (2026-09-30)

**Scope:** the 7-crew README maximalization rollout Chris ordered 2026-09-29
("max commit and merge to toxicwind live, every readme.md uses the readme skill").
53 repositories, crews Rusty / Tarnish / Volt / Pip / Bramble / Wren / Slate.

**Method:** remote HEAD verification via GitHub API per repo — commit SHA, committer
date, message subject. Report prose was treated as a claim, not evidence.
Agent `completed` status was treated as "process ended", not "outcome succeeded".

**Verdict:** 50 of 53 landed via the crews. 2 gaps remediated same night.
1 repo blocked (archived, read-only). **52/53 skill-conformant on main as of this doc.**

## Per-crew results

| Crew | Repos | Landed | Notes |
|---|---|---|---|
| Rusty `4a399f6f` | 7 | 7/7 | ranch `7cbcce9a`, flock `3e9e1ba3`, herd `c6a07ba9`, fleetd `759d113e`, squawk `054aea21`, mcpproxy-go `36055d90`, secretsmith `b78e2454` |
| Tarnish `4953ef2b` | 7 | 5/7 crew + 2 remediated | guidellm `483838e3`, super-ralph `4e5cd2b7`, tau `c446f284`, tau-extensions `1c898e3d`, sovereign `07ff1847` landed. ralph-dashboard had no README commit (HEAD was 2026-09-21) — remediated `b2df3ecb`. sovereign-projects had no README commit — root README was already a 456-line maximal doc, only the badge block needed the skill's right-aligned for-the-badge treatment — remediated `20dad721` |
| Volt `8fcad960` | 7 | 7/7 | nvidia-alive `e81c8ff5`, nvidia-kernel-guard `1dbf2c06`, nvidia-nim-model-probe `b95a5903`, nvidia-swarm-lens `0cd562ec`, nim-inkling-api-research `822e5431` (master), entropy-gpu `f166073b`, k3-capacity-hack `bfa4740c` |
| Pip `5cbfc612` | 7 | 7/7 | codeflux `f6b9f106`, codeflux-moulti `ac2aeaf2` (master), codeflux-patchling `3b02f321`, codeflux-python-patch `3683d5f4` (master), codeflux-watchfiles `61c0a09f`, ast-grep `4daad14e`, agent-dashboard `00bde8db` (default branch `canary`, not main) |
| Bramble `7c09cd26` | 7 | 6/7 | sovereign-dispersal `2fc2ca2f`, sovereign-scripts `abf8ac7b`, sovereign-swap `d6f44834`, identity-router `67732d51`, repo-first-class `09d1f211`, safety-review-gate `f9f02237` landed. **sovereign-skills: repo is ARCHIVED (read-only) — push 403s. Bramble wrote the README (it exists) but could not land it. Needs unarchive to complete.** |
| Wren `0d47ddc4` | 9 | 9/9 | effusion-labs `f7da96c6`, boundless `1306de14`, ontological-atlas `39a12e97`, qed `e04c6c9d`, codex-desktop-linux `b9251667`, caddy-sovereign-auth `db89c5bd`, web3-sec-workspace `d9224e44`, musepool `0a687360`, modelbeats `35587c11` |
| Slate `9ceb7fd0` | 9 | 9/9 | pj-fast `5333d10f`, outlier-toolkit `b242ba2e`, refusal-hunt `39e0d468`, rig `d2db564b`, session-bus-refresh `05a7c68f` (master), vaultfs `31c2e790`, zedra-sovereign `be3320d2`, playwright-mcp `ea967318`, neo-osint `6bb33ebf` |

All SHAs verified against `git ls-remote` / the GitHub API on 2026-09-30.

## Gaps found and remediated

1. **ralph-dashboard** — Tarnish's batch had no commit here. Wrote a maximal README
   per the skill (fork notice + yote durability changes preserved, right-aligned
   for-the-badge badges, hero, features, screenshots, quickstart, mermaid
   architecture, config table, dev, license+security). One correction during
   writing: the old README claimed MIT, but neither upstream
   (Endogen/ralph-dashboard) nor the fork declares a license — documented honestly
   as undeclared. Landed `b2df3ecb`, remote ref verified.
2. **sovereign-projects** — root README was already maximal (456 lines,
   oracle-framed hero untouched); only the badge block was converted to the
   skill's right-aligned for-the-badge convention. Landed `20dad721`, ref verified.
3. **sovereign-skills** — **blocked, not fixable from here.** GitHub has the repo
   archived; pushes 403 (`This repository was archived so it is read-only`).
   The README content exists and is lint-clean; it lands the moment the repo is
   unarchived. Chris's call.

## The "completed but not running" question

All seven crew agents reached `completed` during the night — that is why the UI
stopped showing them as running. `completed` means the agent process ended, **not**
that its outcome succeeded: Bramble's agent is `completed` while reporting 6/7
landed. The task UI conflates "process ended" with "task succeeded". If local code
controls that aggregation, it should split the two states.

## The "home toxic" branch hunt

Chris: "why is home toxic even a branch" — six sweeps found **no such branch
anywhere**:

- GitHub branches across ~80 toxicwind repos (grep `home`) — only
  `toxicwind/effusion-labs` `codex/*homepage*` branches, unrelated.
- All local branches across 60 git repos on yote — nothing.
- `git ls-remote` refs on 16 rollout repos — clean.
- Repo names containing "home" — `wii-homebrew-maximal`, `wii-homebrew-toolkit`,
  `wii-homebrew-pack`, `kimi-k3-homelab`; all branch-clean.
- `/home/toxic/.git` does not exist — the home dir itself is not a repo.
- Cell-side crew clones (`~/workspace/readme-rollout/*`) — no non-main branches.

**Not proven from the UI/task-record schema yet:** whether the card renders
branch=`main` and cwd=`/home/toxic` as separate fields or mangles them into one
branch-like label. If Chris saw it in a specific screen, the screenshot would
settle it — nothing on the git side explains it.

## Push path note (for the next rollout)

`git-push-ref.py` (cell, git-database API) now 403s on blob creation:
`Resource not accessible by personal access token`. The remediations above were
pushed from **yote via `gh`** (clone → commit → push → `git ls-remote` verify),
which works. Cell→yote file transfer: base64 in ≤1500-char `printf %s` chunks,
sha256-verified both sides (watch the final partial chunk — a `while read` loop
drops the last line if it lacks a trailing newline; append one first).

## Related

- Skill: `workspace/skills/readme/SKILL.md` (canonical readme-maximal aesthetic)
- Linter: `~/workspace/bin/readme-lint.ts` (cell-side; both remediated READMEs pass)
- GPU policy broadcast 2026-09-30 (fleet + OpenFang lane): no NVIDIA-only lock;
  external/non-local GPU avoided unless directly herd-related.
