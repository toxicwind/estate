# Yote Consolidation — merge manifest

**Date:** 2026-09-20 · **Directive:** Chris — merge all Yote material on GitHub (private + public) into `sovereign-projects/projects/`, production-grade, stop using the gist.
**Coordinator:** subagent e57b7099 · **Plan:** `~/workspace/yote-consolidation/PLAN.md` (also in this repo's workspace copy)
**Iron rules honored:** no repo deleted; no newer file clobbered by an older one; every move recorded here.

## Inventory (phase 1)

- **473 repos** enumerated (`inventory/repos.md`); **635 code hits across 69 repos** (`inventory/code-hits.md`).
- Repos matching `*yote*` (name/description): `toxicwind/yote` (private, Rust gateway — the real one) + 1 false positive (ComfyUI fork via "Coyote-A").
- Full detail: `~/workspace/yote-consolidation/inventory/`.

## Merges (phase 3) — all into `toxicwind/sovereign-projects@main`

### 3a — Rust gateway: `toxicwind/yote` → `projects/yote/rust-gateway/`
- **Commit:** `c9383e4ae946643d29babba342ab18b5983ffada` (base `b6da5840`)
- 7 files, 179,886 bytes; every dest blob SHA == source blob SHA (7/7 verified).
- Files: `.gitignore`, `Cargo.toml`, `LICENSE`, `README.md`, `src/discord.rs` (65,068 B), `src/main.rs`, `src/telegram.rs` (100,338 B).
- Source repo untouched. Full table: `manifest/merge-a-rust.md`.

### 3b — Bridge client: `toxicwind/gear/awrawr-mcp/` → `projects/yote/bridge/`
- **Commit:** `b6da5840bc001a322e3b4135bde3323e6f0af72c`
- 13 files; every dest blob SHA == source blob SHA; exec-bit modes preserved.
- Key: `bin/exec.py` `d00f62f7` (50,539 B, fixed version), `bin/ws_daemon.py` `b3d47a6c` (15,433 B), `bin/wsframe.py`, `bin/xfer.py`, `bin/agent.py`, `bin/chat.py`, `bin/chatctx.py`, `SKILL.md`, `transport-health-checklist.md`, `poll-caps.md` (+3 more).
- Source repo untouched. Full table: `manifest/merge-b-bridge.md`.

### 3b-sync — Vendored `gear/awrawr-mcp/bin/ws_daemon.py` re-synced from gear
- **Commit:** `b3346c0206185f18603f6875df9e2a1cb911959e`
- `7a61fa46` (10,674 B, stale) → `b3d47a6c` (15,433 B, gear-canonical). Vendored `exec.py` already SHA-identical, untouched.

### 3c — Gist migration → `projects/yote/ops/`
- **Commit:** `653d653f5b6233ee2474c82f6bf7ed2ef3706803`
- `yote-doctor.sh` (6,138 B, v2, blob `03e44e32`) + `yote-fix.sh` (23,803 B, v3, blob `f2876976`), fetched HTTP 200 from gist raw.
- Gist's `exec.py`/`ws_daemon.py` deliberately NOT copied (gist exec.py is stale 49,463 B; gear's 50,539 B canonical version is in `bridge/`).
- Gist `e817e044162bb59c386615f89b1baeb0` left live, **deprecated** (description updated).
- Full table: `manifest/merge-b-ops.md`.

### 3d — Stale-mirror check: `toxicwind/sovereign` vs `sovereign-projects`
- Verdict: **pure stale mirror — nothing merged.** 2 shared yote paths: 1 identical, 1 diverged (`src/services/yote.ts`: sovereign 18,569 B Sep 11 vs SP 23,768 B Sep 17 — SP newer). 0 paths only-in-sovereign. Full report: `manifest/merge-c-diff.md`.

## Gist deprecation (phase 4)

- Contents migrated per 3c. New canonical raw URLs (public repo, no auth):
  - `https://raw.githubusercontent.com/toxicwind/sovereign-projects/main/projects/yote/ops/yote-doctor.sh`
  - `https://raw.githubusercontent.com/toxicwind/sovereign-projects/main/projects/yote/ops/yote-fix.sh`
- `yote-fix.sh`'s deploy source for `exec.py`/`ws_daemon.py` repointed from gist raw to `.../projects/yote/bridge/bin/...` (commit TBD in phase 4).
- References to update (parent's lane): `MEMORY.md` gist URLs, `~/workspace/docs/` run commands, yote-fix v1/v2 copies on the yote box.

## Deploy bundle (phase 5)

- Staged at `projects/yote/ops/deploy/` — `MANIFEST.txt` + `apply.sh` + `VERIFY.md`. **Staged only; the parent applies it to `/home/toxic/sovereign` via the exec bridge.**
- Bonus find during merge: `shingle-workspace/awrawr_ws_exec.py` (the box's WS server source) exists in SP — included in the bundle as review-only (parent diffs against the box's live copy before overwriting).

## Open decisions (not unilaterally resolved)

- **D1 — Rust vs TS gateway:** both preserved; unification is Chris's call.
- **D2 — `awrawr_ws_exec.py` freshness:** SP's copy vs the box's live copy — parent to diff on apply.
- Excluded as noise: moonbox-*/portal-audit/emergent-august mirrors, cdn-assets XMLs, "coyote time" game-dev hits, `toxicwind/rig/agents/coyote/` (parallel open-source config, left in rig).
