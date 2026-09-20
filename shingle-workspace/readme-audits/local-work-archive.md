# README audit — toxicwind/local-work-archive @ 1c01466b6f4f6ba27bfa7ee741875096ae1cf73b — 2026-09-14

**Verdict:** NEEDS UPDATE

Private repo, 2.7 GB, 93 blobs, 3 commits (all 2026-09-14). README is 171 chars /
2 lines — nothing else in the tree is documented. Mechanical checks all PASS
except `readme-exists: WARN` (trivial length).

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| "Private archive of local-only git work from awrawr-pc" | Repo is private; manifests record source roots `/home/toxic/...` (e.g. `worktrees/club-3090-scratch/manifest.json`: `"repo": "/home/toxic/.gemini/antigravity-ide/scratch/club-3090"`) | VERIFIED |
| "worktree snapshots" | `worktrees/` holds 11 snapshots (club-3090-scratch, dedi-ops, librefang, nuvio-platform, pi-conv-audit, smithers, sovereign-herd, sovereign, toxicwind-repos, workspace, x-algorithm), each with `manifest.json` + `staged.patch` + `tracked.patch` (+ `untracked.tar.gz`); commits `0d987ccb` "preserve: awrawr-pc at-risk snapshots 2026-09-14 (worktrees + untracked tarballs…)" | VERIFIED |
| "untracked" content | `untracked/` holds 5 bundles (nvme0-recovery, projects-tau-diff, ralph-test, sovereign-untracked, tau-extensions) with `manifest.json` + tarballs + sha256/filelist metadata | VERIFIED |
| "stashes" | No stash objects, stash lists, or stash-named files anywhere in the 93-blob tree | UNVERIFIED |
| "unpushed branches" | No branch refs or branch snapshots beyond per-worktree patch diffs against recorded head SHAs | UNVERIFIED |
| "Created 2026-09-14 during local safety audit" | Initial commit `c30f17b6` + all commits dated 2026-09-14; repo description matches verbatim | VERIFIED |

Verdicts: VERIFIED / STALE (used to be true) / WRONG (never true) /
UNVERIFIED (can't confirm from tree).

## Missing from README

Real features, renames, removals, or config changes in recent commits with no
README coverage:

- **Layout is undocumented**: `worktrees/` vs `untracked/` top-level dirs,
  plus `worktrees/*/submodules/` (nuvio-platform, sovereign) — none mentioned.
- **No inventory**: 11 worktree snapshots + 5 untracked bundles are
  undiscoverable without listing the tree.
- **Chunking convention**: commits `0d987ccb` / `1c01466b` "split remaining
  >45MB tarballs to <=45MB chunks" — `.tar.gz.part-NN` naming exists in tree
  (e.g. `untracked/sovereign-untracked/*.part-00..02`) but no reassembly
  instructions (`cat *.part-* > x.tar.gz`).
- **Manifest provenance**: `manifest.json` fields (source repo path, head SHA,
  branch, date, sha256, `excluded_secrets`) are undocumented.
- **No restore instructions**: how to apply `staged.patch`/`tracked.patch`
  (`git apply`) or extract the tarballs.
- **Secrets hygiene note missing**: manifests show secret exclusions were
  attempted on some entries (`"excluded_secrets"`,
  `"excluded_secret_content"`), but exclusion lists are sparse and an API key
  exposure through this repo was flagged to the owner on 2026-09-14. README
  should warn that snapshots may contain secrets.

## Quickstart check

- N/A — README has no quickstart, commands, or entrypoints to verify.

## Action taken

- None — report only (per task scope; no edits/commits/pushes).
