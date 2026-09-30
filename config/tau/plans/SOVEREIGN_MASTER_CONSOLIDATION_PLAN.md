# Sovereign Master Consolidation & First-Class Tooling Plan

## Context
The workstation (CachyOS / BTRFS on NVMe, 820GB used across /home/toxic) contains overlapping git worktrees (163GB sovereign, 177GB projects), uncompressed historical cell backups (~25GB), legacy git snapshots (17GB), and scattered temporary scripts. The goal is to establish `/home/toxic/sovereign` as the single authoritative master repository, safely consolidate and prune redundant worktrees, leverage native BTRFS block-level extent deduplication (`jdupes -B` / `duperemove` via `FIDEDUPERANGE`) without reinventing the wheel, and expose a first-class unified Bun MCP server (`sovereign-mcp-server.ts`) for all agent tooling.

---

## Approach

### Phase 1: Shell & Search Tooling Hardening (Immediate Verification)
1. **Ensure First-Class Search Execution**:
   - Verify `~/.bashrc.env` disables conflicting bash loadables (`enable -n fd rg 2>/dev/null || true`).
   - Verify `PATH` deduplication produces exactly 20 unique, ordered directories without duplication.
   - Verify `find` and `grep` wrappers in `~/.bashrc.env` dispatch to `ffs find` / `ffs grep` with fallback to native `/usr/bin/fd` and `/usr/bin/rg`.
2. **Execution Test**:
   - Run `bash -lc "true"` and verify exit code 0.
   - Run `fd --version` (10.5.0) and `rg --version` (15.2.0) across subshells.

### Phase 2: Sovereign Master Worktree & Repo Consolidation
1. **Worktree Audit & Inventory**:
   - Query all registered git worktrees using `git -C /home/toxic/sovereign worktree list`.
   - For each worktree (`sovereign-503`, `sovereign-clean`, `sovereign-sweep-main`, `dash-main`, `herd-healer`, `sovereign-wt-*`):
     - Check `git status --porcelain` for uncommitted changes.
     - Check `git log -1` against `origin/main` and `forge/gate-retire-final`.
2. **Safe Merge & Prune Protocol**:
     - Stash or commit any unique branch state to sovereign backup branches (`backup/wt-*`).
     - Remove stale worktrees cleanly with `git -C /home/toxic/sovereign worktree remove --force <path>` followed by `git worktree prune`.
     - Retain `/home/toxic/sovereign` as the single active working tree.

### Phase 3: BTRFS Block-Level Extent Deduplication (No Reinventing the Wheel)
1. **BTRFS Reflink Deduplication**:
   - Install/verify `jdupes` / `duperemove` via pacman (`sudo pacman -S --needed --noconfirm jdupes duperemove`).
   - Run block-level deduplication across heavy duplicate directories (`/home/toxic/projects`, `/home/toxic/sovereign`, `/home/toxic/cell-backup-*`) using BTRFS `FIDEDUPERANGE` ioctl:
     ```bash
     jdupes -r -B /home/toxic/projects /home/toxic/sovereign
     ```
   - This clones duplicate data blocks on disk without modifying or breaking any file paths or symlinks.
2. **Archive Isolation**:
   - Move stale gist dumps (`/home/toxic/gist-archive/`) and cell backups into a single compressed cold-storage volume (`/home/toxic/cold-storage/`) to prevent search tools from indexing 300+ identical micro-repos.

### Phase 4: First-Class Unified Sovereign Bun MCP Server
1. **Implement `sovereign/helpers/sovereign-mcp-server.ts`**:
   - Create a stdio JSON-RPC MCP server in TypeScript running under Bun.
   - Expose the core sovereign operational tools:
     - `estate_scan`: Runs `estate-scanner.ts` across estate paths (anomalies, broken symlinks, path health).
     - `estate_health_audit`: Runs `health-audit.ts` probing ports 25xxx.
     - `estate_mesh_probe`: Runs `mesh-probe.ts` against `shep` (`:25127`).
     - `estate_git_mutator`: Runs `git-mutator.ts` status / scan-secrets.
     - `estate_safe_rg`: Token-budgeted regex/AST code search.
     - `estate_paper_search`: Queries `race_papers.py` on arXiv / alphaXiv.
2. **Register in `shep` Gateway (`mcp_config.json`)**:
   - Add `sovereign-tools` upstream to `/home/toxic/sovereign/mesh/gateway/mcp_config.json`:
     ```json
     {
       "name": "sovereign-tools",
       "protocol": "stdio",
       "command": "bun",
       "args": ["/home/toxic/sovereign/helpers/sovereign-mcp-server.ts"],
       "enabled": true
     }
     ```
   - Restart `shep` via pitchfork: `cd /home/toxic/sovereign && pitchfork restart shep`.

### Phase 5: End-to-End Estate Verification
1. **Verify Services in Pitchfork & Mise**:
   - `mise -C /home/toxic/sovereign run health-hindsight` $\to$ Healthy (`:25117`).
   - `mise -C /home/toxic/sovereign run health-tau` $\to$ Healthy (`:25111`).
   - `sovereign/awrawr-ws-exec` $\to$ Healthy (`:25204`).
2. **Verify Tooling**:
   - `tau audit` $\to$ 13 PASS, 0 FAIL.
   - `/home/toxic/sovereign/bin/estate-scan` $\to$ PASS (0 broken bin symlinks).
   - `/home/toxic/sovereign/projects/mesh/bin/openfang-mesh-probe.sh` $\to$ `PROBE-PASS`.

---

## Critical Files & Anchors
- `/home/toxic/.bashrc.env`: Idempotent PATH + first-class `ffs`/`fd`/`rg` tool routing.
- `/home/toxic/sovereign/pitchfork.toml`: Service SSOT for all 25xxx daemons.
- `/home/toxic/sovereign/mesh/gateway/mcp_config.json`: Shep upstream configuration.
- `/home/toxic/sovereign/helpers/sovereign-mcp-server.ts`: Unified Bun MCP server.
- `/home/toxic/sovereign/helpers/estate-scanner.ts`: High-speed filesystem & path validator.

---

## Verification
1. **Search Tool Integrity**:
   - `find hindsight.sh` $\to$ executes `ffs find` in <100ms.
   - `grep "HINDSIGHT_API_PORT" sovereign/stack/services/hindsight.sh` $\to$ executes `ffs grep` cleanly.
2. **MCP Mesh Verification**:
   - `shep upstream list` shows `sovereign-tools` as `Connected`.
   - `shep call tool-read --tool-name=sovereign-tools:estate_scan` returns structured JSON estate report.
3. **Estate Health & Audit**:
   - `tau audit` exits 0 with all checks green.
   - `openfang-mesh-probe.sh` exits 0 with `PROBE-PASS`.
