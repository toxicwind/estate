# Git Inventory Audit — awrawr-pc (2026-09-14)

Read-only sweep via the awrawr-mcp exec bridge. ~440 git repos scanned across
`/home/toxic` (sovereign, projects, repos, github, workspace, priority dirs),
`/opt`, `/srv`. Noise pruned: node_modules, .cache, vendor, .venv, __pycache__,
.cargo, gist-archive, dotfiles_pull, archive/backups. Known-good bridge files
(awrawr_mcp.py, audit exporter, JSONL/parquet, systemd units) untouched.
No services restarted. No writes made on awrawr-pc.

## 0. Headline findings

- **DELETED/RENAMED REMOTE FLAGS: NONE.** Zero local repos have remotes pointing
  at `toxicwind/tau`, `toxicwind/oh-my-pi` (deleted today) or
  `toxicwind/sovereign-pi` (renamed today). No local checkout is orphaned from
  a deleted remote.
- **Biggest unpushed divergence: `/home/toxic/sovereign`** — main is **+165
  commits ahead of origin/main** (toxicwind/sovereign-projects), plus 1 stash,
  7 modified + 20 untracked paths. The untracked paths include `tau/`,
  `projects/tau/`, `herd/`, `mesh/`, `sovereign-scripts/`, `sovereign-skills/`.
- **`/home/toxic/sovereign/tau/` vs `projects/tau/` (RESOLVED by side chat):**
  neither is its own git repo — both are untracked working dirs inside the
  sovereign-projects checkout. `tau/` (35,736 source files, 20,817 touched
  since Sep 10, has `.agent/` runtime state) is the **LIVE working tree**.
  `projects/tau/` (21,922 files, 61 touched since Sep 10) is stale but
  **ARCHIVE-WORTHY — DO NOT DELETE**: it holds 6,143 files absent from `tau/`
  (root `bun.lock`, `engine/crates/pi-natives/tools/*`). Because both are
  untracked/ignored inside the checkout, **plain `git push` will NOT capture
  them** — preservation needs a tarball-into-archive mechanism, not a push.
- **`/home/toxic/sovereign/tau/engine/.git` is an EMPTY stub** (only `info/`);
  an early scan artifact attributed the parent repo's status to it — corrected.
- **SECURITY: `/home/toxic/projects/moonbox-live/.git_repos/*.git`** (7 bare
  mirrors) have **GitHub PATs embedded in plaintext in their remote URLs**
  (2 distinct tokens). Recommend rotating and re-cloning without embedded creds.
- **`/home/toxic/sovereign-history`** is a repo whose only remote is
  `file:///home/toxic/.git.bak-20260913` (a 2026-09-13 backup of the sovereign
  workspace git dir: branch main @ 1baf0f5f7, remote toxicwind/sovereign,
  extra branch fix/inkling-maximal fully merged, no stash).

## 1. Remote-URL flags (deleted/renamed repos)

No matches for `toxicwind/(tau|oh-my-pi|sovereign-pi)` in any remote URL across
all ~440 repos. **Nothing is orphaned from today's deletions/rename.**

## 2. Watched-for-consolidation (blocks the 5-repo archive pass)

| Repo | Local clones | State |
|---|---|---|
| omp-extensions | `/home/toxic/sovereign/tau/extensions/omp-extensions___omp-kafka___0.1.0` and `/home/toxic/sovereign/projects/tau/extensions/omp-extensions___omp-kafka___0.1.0` | **RISK (both):** on branch `fix/add-kafkajs-dep` @ c3c4d27; 3 modified READMEs; local `main` **+1 ahead of upstream/RekunDzmitry** (`04efbb2 fix: add missing kafkajs dependency and tests`). Clones identical except `.git/index` |
| sovereign-scripts | 4 identical plain dirs (NOT repos): `sovereign/{,packages/,projects/,projects/packages/}sovereign-scripts` | untracked inside sovereign checkout; 16 files each |
| sovereign-skills | 4 identical plain dirs (NOT repos): same 4 locations | untracked; 5 files each |
| sovereign-swap | 1 plain dir: `/home/toxic/sovereign/sovereign-swap` (contains only `build/`) | untracked |
| sovereign-zed | **no local clone found anywhere** | — |

## 3. Git auth on awrawr-pc

- `gh auth status`: **WORKS** — logged in as `toxicwind` (token in
  `/home/toxic/.config/gh/hosts.yml`, scopes: gist, read:org, repo, workflow),
  HTTPS protocol.
- `git config --global/--system credential.helper`: **not set** (empty).
- `ssh -T git@github.com`: **FAILS** — `Permission denied (publickey)`,
  exit 255. No SSH-key auth to GitHub on this machine. Pushes must go over
  HTTPS via gh.

## 4. Consolidated at-risk table

Legend: S=stash, A=ahead-of-upstream (commits), D=dirty worktree, U=untracked,
DET=detached HEAD, NR=no remote.

### 4a. Stashes (1 repo, 1 entry)
- `/home/toxic/sovereign`: `stash@{0}: WIP on main: dd19e6848 chore: remove
  stale engine/ groq files, add OPENROUTER_PARAMS`

### 4b. Ahead of upstream (unpushed commits)
- `/home/toxic/sovereign`: main **+165** vs origin/main (sovereign-projects)
- `/home/toxic/projects/morphe-patcher`: main **+43** vs origin/main
  (MorpheApp/morphe-patcher)
- `/home/toxic/projects/super-ralph`: main **+3** vs origin/main
  (8682388, 15281f3, ff2e255 — NIM proxy fixes)
- `/home/toxic/projects/agents/openfang`: main **+2** vs origin/main
  (0dcc98b, e361d98)
- `/home/toxic/projects/herd`: main **+1** vs origin/main (ea54484)
- `/home/toxic/projects/antigravity-gateway-master`: main **+1** vs origin/main
- `/home/toxic/projects/arxiv-mcp-server`: main **+1** vs upstream/main
  (blazickjp)
- `/home/toxic/projects/ast-grep`: main **+1** vs upstream/main
- `/home/toxic/projects/crypto-workspace`: main **+1** vs origin/main
  (toxicwind/mist-factory)
- sovereign ×2 `omp-extensions___omp-kafka___0.1.0` clones: local main **+1**
  vs upstream/main (RekunDzmitry/omp-extensions)

### 4c. Dirty worktrees of note (modified/staged)
- `/home/toxic/sovereign`: M .gitattributes, .recursive-verified, package.json;
  D 9router, audit/bun.lockb; M submodule pointers tools/nuvio-{platform,webos}
- `/home/toxic/sovereign/herd`: M LICENSE.md, M README.md
- `/home/toxic/sovereign/projects/shell/ii` + `/home/toxic/sovereign/shell/ii`
  (two checkouts, same repo): D 5 quickshell icon files
- `/home/toxic/sovereign/tools/nuvio-platform`: 11 staged submodule adds, **no remote**
- `/home/toxic/sovereign/tools/nuvio-webos`: M 9 files
- `/home/toxic/projects/dedi-ops`: M 13 (incl. `.env`!), R 8 renames to
  legacy/dayz-discord/
- `/home/toxic/projects/pi-conversation-aware-audit`: **M 1096 files**
  (kimi-code fork, origin toxicwind/kimi-code-sovereign)
- `/home/toxic/projects/toxicwind-repos`: **D/M 990 files** on branch
  dev/security-audit-2026 (mass deletion)
- `/home/toxic/projects/organized-lattice-v3/xai-grok-stack/x-algorithm`:
  D 216 files of 226 changed (checkout looks gutted)
- `/home/toxic/projects/organized-lattice-v3/media-vaults/WiiBox`: M 29,
  **no remote**
- `/home/toxic/projects/itvx_morphe_vault`: M 9, **no remote**
- `/home/toxic/projects/hyprradial`: hyprbars→hyprradial rename, 17 changed
- `/home/toxic/projects/agents/openfang`: M 3 rust kernel files
- `/home/toxic/projects/final_bruteforce_1779691527/gayxxx-sovereign`:
  D 19 .cs3 build files
- `/home/toxic/projects/master_cs3_20260525_012533/template`: A 144 jadx outputs
- `/home/toxic/projects/agent-dashboard`: M/A 7 (next.js fork, canary)
- `/home/toxic/projects/CodeWhale`: M 3 package.json
- `/home/toxic/projects/cachyos-kernel`: M PKGBUILD (+3 untracked patch/config)
- `/home/toxic/projects/super-ralph`: M bun.lock, package.json
- `/home/toxic/projects/websites/effusion-labs`: M 4 css/config files
- `/home/toxic/projects/moonbox-live`: M llama-swap binary
- `/home/toxic/projects/free-claude-code`: M api/models/anthropic.py
- `/home/toxic/projects/kyle-pi-model-discovery`: M 3 src files
- `/home/toxic/projects/mist-factory`: A dashboard/index.html, **no remote**
- `/home/toxic/projects/nvme0-recovery`: DETACHED, **no remote**,
  ?? carved/, crypto-findings/
- `/home/toxic/projects/ralph-test`: DETACHED, **no remote**, ?? 6 agent dirs
- `/home/toxic/github/harness-local`: DETACHED, **no remote**, clean
- `/home/toxic/workspace`: **no remote**, ?? MONOREPO_MIGRATION_NOTES.md,
  not_owned_by_toxic.txt
- `/home/toxic/repos/wii-auto-store`: **no remote**, M README.md,
  ?? INSTRUCTIONS.md, osc_v4_contents.json
- `/home/toxic/smithers`: upstream-only (no origin), M package.json
- `/home/toxic/.gemini/antigravity-ide/scratch/club-3090`: D 12 files
  (gemma/qwen vllm cache + patch files), origin noonghunna/club-3090
- `/home/toxic/.librefang`: A 674 files staged (initial config), **no remote**

### 4d. Detached HEADs (all clean trees unless noted)
arc-agi-ops, end4-mac-launcher (×2), forge-test-1786623471, kataware-doki,
nvme0-recovery (+untracked, no remote), test-1787449974, tool-mesh (+??
AGENTS.md), universal-search-fuzzer, unwatermarked, wii-homebrew-maximal,
wii-stream-pack, sovereign-history (remote=file:// backup), ralph-test
(+untracked, no remote), github/harness-local (no remote),
archive/backups/backup_openclaw_openfang_1779150995/openclaw_backup/workspace
(8 staged adds — backup noise).

### 4e. Bare mirror repos (moonbox-live/.git_repos/*.git)
7 bare mirrors: agents-md-project, effusion-labs, envd-project,
repo_kimi_team_recon, toxicwind-repos (has backup-local-*/backup-remote-*
branches), triangle-access. **All have GitHub PATs embedded in plaintext
remote URLs** — rotate these tokens.

## 5. Clean-repo summary

~330 repos are clean (no stash, not ahead, clean tree, on a branch). The bulk
are: vendored upstream checkouts under projects/ (antigravity-*, grok-*,
hyprland dotfiles pulls — excluded from risk as vendored noise), Chris's
toxicwind/* project mirrors, and sovereign sub-checkouts (skills/*,
projects/packages/*, extensions). No remote-URL flags among them. Full
per-repo list available from the sweep logs on request.

## 6. Caveats

- Read-only throughout: only `git status/log/remote/stash/for-each-ref/rev-parse`,
  `find`, `ls`, `diff -rq`, `du`. No writes, no service restarts. The side chat
  confirmed `.git/index` touches from the sweep are benign.
- `git status` counts for the whole-home backup git dir
  (`/home/toxic/.git.bak-20260913` vs worktree /home/toxic) reflect its
  2026-09-13 index state (466k staged-add entries), not live intent — treat as
  archival reference only.
- Detached-HEAD clean checkouts have no uncommitted work; their commits remain
  reachable via reflog/branches.
- Per task scope, `~/awrawr_mcp_audit_export.py`, `~/.awrawr_mcp_audit.jsonl`,
  `~/.awrawr_mcp_audit.parquet` were not read or touched.
