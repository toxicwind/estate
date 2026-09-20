# awrawr-pc Git Safety Preservation — 2026-09-14

Source audit: `awrawr-git-inventory-2026-09-14.md`
Bridge: `~/workspace/skills/awrawr-mcp/` (`bin/exec.py`)
Backup remote (private): `https://github.com/toxicwind/local-work-archive.git`

**Result: every at-risk item from the inventory is now preserved on the private
`toxicwind/local-work-archive` remote** — 34 branches + tarball artifacts in `main`,
all verified via `git ls-remote`. No worktree was modified in the process
(before/after `git status --porcelain` hashes matched everywhere; zero
WORKTREE-CHANGED warnings across 110 receipts). No force-pushes, no branch
deletions, no `stash`/`checkout`/`reset`/`clean` on any user repo. The only
`reset --soft` was inside a disposable local scratch clone of the archive repo.

## HIGHEST-RISK item: tau-extensions — PRESERVED

`/home/toxic/sovereign/tau-extensions/` (101 files) is the intended
`toxicwind/tau-extensions` extensions monorepo (omp-kafka + omp-edit-committer
forks + omp-model-router). It was **unpushed, untracked, and no remote exists**
(github.com/toxicwind/tau-extensions → 404) — invisible to git, backed up nowhere.

- Both copies (`sovereign/tau-extensions/`, `sovereign/projects/tau-extensions/`)
  verified byte-identical via `diff -rq`.
- Secrets screen: 2 content hits, both FALSE POSITIVES (Kafka SASL `password:`
  plumbing in `packages/omp-kafka/src/consumer.ts:100`, type declaration in
  `types.ts:45`). No secret values. Nothing excluded.
- Packed as `untracked/tau-extensions/tau-extensions.tar.gz` (183 KB) + manifest
  (sha256 `d9574121…`, risk flag, file list) → committed to archive `main`, pushed.
- **Open question for Chris (recorded, NOT acted on):** publish it to GitHub as
  `toxicwind/tau-extensions` (README already links that URL)? Rebrand is
  incomplete: `marketplace.json` still says `omp-extensions`, owner RekunDzmitry.
  Do NOT create the repo without his call.

## Preserved branches on local-work-archive (verified `git ls-remote`)

**Stash + sovereign main**
- `archive/stash-sovereign-20260914-0` — sovereign `stash@{0}` (original still present locally)
- `backup/sovereign/main` — sovereign local main at `85f823d09297…`. Upstream push
  to `toxicwind/sovereign-projects` SKIPPED: not a clean fast-forward (remote main
  moved to `996931b2`, local is behind/ahead-diverged). Archive backup is the safety net.

**Unpushed branches** (`backup/<slug>/main`)
- morphe-patcher (43 commits, `97edf384…`; upstream is MorpheApp → archive only)
- super-ralph (3 commits; upstream evmts/super-ralph → archive only)
- openfang (2 commits; upstream RightNow-AI → archive only)
- herd (1 commit; upstream push not clean FF → skipped, archive only)
- antigravity-gateway-master (`5644645b…`; upstream toxicwind/… dry-run clean →
  **real fast-forward push succeeded `443dcba..5644645`**)
- arxiv-mcp-server (upstream blazickjp → archive only)
- ast-grep (upstream not user's → archive only)
- crypto-workspace (upstream toxicwind/mist-factory dry-run clean → **push succeeded**)
- omp-ext-a / omp-ext-b (RekunDzmitry omp-kafka extension clones → archive only;
  these are NOT the wave-2 `toxicwind/omp-extensions`)

**Dirty worktree snapshots** (`archive/worktree-<slug>-20260914`)
- shell-ii, shell-ii-projects, effusion-labs, wii-auto-store, wiibox, itvx-morphe-vault,
  gayxxx-sovereign, kyle-pi-model-discovery, mist-factory, super-ralph (M bun.lock,
  M package.json, ?? fix-nim-proxy.patch), omp-ext-a, omp-ext-b, openfang
- nuvio-webos, hyprradial, cs3-template — each needed `git fetch --unshallow origin`
  first (shallow-clone root cause: remote "did not receive expected object")
- cachyos-kernel, free-claude-code — inventory paths were wrong
  (`/home/toxic/projects/…`); actual repos at `/home/toxic/cachyos-kernel`,
  `/home/toxic/free-claude-code`; same shallow-clone fix applied
- CodeWhale, moonbox-live — same shallow-clone fix applied
- agent-dashboard — full-history branch push kept failing (655,772-object pack,
  repeated HTTP 500 / remote hangup); preserved as
  `archive/worktree-agent-dashboard-20260914-squashed`, an orphan commit with a
  **byte-identical tree** (36,099 objects), pushed ok. Full-history branch kept locally.

**Artifact snapshots in archive `main`** (`worktrees/<slug>/`, all files ≤45 MB)
- sovereign, sovereign-herd (kimi_tokens.json / tokens.go / token_cmd.go etc. excluded),
  nuvio-platform, dedi-ops (.env, .env.*, compose/runbook secret hits excluded),
  pi-conv-audit, toxicwind-repos, x-algorithm (thunder/kafka_utils.rs excluded),
  smithers (node_modules `*token*` overmatches honored), club-3090-scratch, librefang,
  workspace
- The worker's 90 MB split threshold was wrong; all >45 MB tarballs were re-split
  with `split -b 45M` in a fresh pass, manifests updated with part lists + reassembly
  notes, squashed into one commit and pushed (`c30f17b..0d987cc`, then `..1c01466`).

**Untracked tarballs in archive `main`** (`untracked/<name>/`, all ≤45 MB chunks)
- `sovereign-untracked/` — 18 sovereign `??` entries, 127.7 MB in 3 parts
- `projects-tau-diff/` — 6,058 files (of 6,143) absent from `tau/`, 55.3 MB in 2 parts;
  85 `*token*`/`*credentials*`-named source files excluded by the secrets screen
  (list in manifest; many are likely false positives, e.g. tokenizer implementations)
- `nvme0-recovery/` — full repo incl. `.git` with 19,862 loose objects
  (1,372 parentless "Checkpoint" disk-carving commits, no refs/HEAD); 52.1 MB in 2 parts;
  `crypto-findings/signals.txt` excluded by secrets screen
- `ralph-test/` — 175 untracked agent-skill files (repo has no commits); 0.1 MB.
  Inventory path was wrong (`/home/toxic/projects/ralph-test`); actual `/home/toxic/ralph-test`
- `tau-extensions/` — see HIGHEST-RISK above

**Detached repos**
- nvme0-recovery → tarball (above); harness-local → see NOT-PRESERVED (empty)

**Wave-2 plain directories**
- sovereign-scripts (17 files) / sovereign-skills (4 files): all 4 copies each
  verified byte-identical (content md5 `53ccfa4d…` / `2674d8e1…`) → one copy each
  inside `sovereign-untracked/`; 3 redundant copies flagged as dedup opportunities.
- sovereign-swap `build/` → inside `sovereign-untracked/`. sovereign-zed → no local copy.

## NOT-PRESERVED (explicit)

1. **Secret-screen exclusions** (excluded from snapshots, listed in manifests —
   not claimed as preserved): sovereign herd `kimi_tokens.json` ×2, `tokens.go`,
   `token_cmd.go`, `token_cmd_test.go`, `token_store.go`, `generate*.go`, etc.;
   dedi-ops `.env`, `.env.chronos`, `.env.example/.template/.global` + compose/runbook
   content hits; x-algorithm `thunder/kafka_utils.rs`; smithers node_modules
   `*token*` paths; projects-tau-diff 85 `*token*`/`*credentials*` source files;
   nvme0 `crypto-findings/signals.txt`; ralph-test
   `.opencode/skills/security-review/SKILL.md` (content identical in 4 sibling copies).
2. **harness-local** (`/home/toxic/github/harness-local`): repo is EMPTY
   (0 git objects, no commits, no refs, empty worktree) — nothing at risk.
3. **sovereign-zed**: no local copy exists — nothing to preserve.
4. **Moonbox bare mirrors** (`/home/toxic/projects/moonbox-live/.git_repos/*.git`):
   untouched per instructions. **Two GitHub PATs are embedded in their remote URLs —
   recommend rotating both.**
5. **Upstream pushes skipped** (archive backup done instead): sovereign main
   (not fast-forward vs remote `996931b2`), herd main (not clean FF). All other
   upstreams were either not Chris's (archive only) or pushed successfully
   (antigravity-gateway-master, crypto-workspace→mist-factory).
6. **agent-dashboard full-history branch** exists only locally (655k-object pack
   would not push); the squashed orphan branch on the remote has an identical tree.

## Follow-ups for Chris

- Publish `tau-extensions` to GitHub as `toxicwind/tau-extensions`? (awaiting his call;
  rebrand incomplete — marketplace.json says `omp-extensions`, owner RekunDzmitry)
- Rotate the two GitHub PATs exposed in moonbox bare-mirror remote URLs.
- Sovereign upstream: local main vs remote `996931b2` needs a fetch/recheck before
  any upstream push is reconsidered.
- 85 `*token*`-named files excluded from the projects-tau-diff tarball are likely
  mostly false positives — repack without the name screen if he wants them.
- Optional dedup: 3 redundant copies each of sovereign-scripts/ and sovereign-skills/
  under `/home/toxic/sovereign/`.

Raw receipts: `/tmp/preserve/receipts.md` on awrawr-pc (110 lines; superseding
RETRY-OK receipts appended after each FAILED line they replace).
