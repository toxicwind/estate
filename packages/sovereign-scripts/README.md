# sovereign-scripts (packages mirror)

<div align="right">
![sovereign](https://img.shields.io/badge/sovereign--projects-blue?style=for-the-badge) ![python](https://img.shields.io/badge/python-toolkit-3776AB?style=for-the-badge) ![kind](https://img.shields.io/badge/kind-workspace_mirror-green?style=for-the-badge)
</div>

*Workspace mirror of the `sovereign-scripts` Python automation toolkit — GitHub API ops, repo audits, archiving, sandboxing, and health checks. Same scripts, same conventions as the top-level `sovereign-scripts/` directory (contents verified identical); the full story lives in [the canonical README](../../sovereign-scripts/README.md).*

## Scripts

| Script | What it does |
|---|---|
| `sovereign_helper.py` | Master hook for GitHub API ops — async, parallel, rate-limited |
| `health_check.py` | Port/socket health checks for the sovereign environment |
| `git-push-one.py` | Push one file to a GitHub repo with per-repo identity |
| `commit_extractor.py` | Bulk GitHub commit extraction with resumable state |
| `archivefs_v3.py` | Mount-like binary archive with 90MB chunking |
| `arfs-cat.py` | cat/ls files inside an ArchiveFS archive without extracting |
| `auto-hook-loader.py` | Load all auto-hooks from the agent hooks dir |
| `namespace_probe.py` | Linux namespace & capability audit |
| `cache_timing.py` | Cache side-channel timing probe (educational) |
| `unshare-root.py` | Run commands in an unshared user namespace as root |
| `mitm-proxy/` | MITM proxy helpers (`playwright_mitm.py`, `race_aware_loader.sh`) |
| `patches/` | Patch scripts (`browser_guard.py`) |

See `AGENTS.md` in this directory for repo conventions.

## Mirror relationship

```mermaid
flowchart LR
    ROOT["sovereign-scripts/<br/>toolkit (top level)"] --> MIRROR["packages/sovereign-scripts/<br/>workspace mirror"]
    MIRROR --> SAME["same scripts<br/>same AGENTS.md<br/>same conventions"]
```

This directory mirrors the top-level toolkit so workspace consumers get the scripts where they expect them. Changes belong in one place and get carried to the other — don't let the two drift.

## Quick Start

```bash
python3 packages/sovereign-scripts/health_check.py
python3 packages/sovereign-scripts/git-push-one.py --help
python3 packages/sovereign-scripts/commit_extractor.py --owner toxicwind --output ./commits
```

## Configuration

Per-script flags (`--help` is the contract); GitHub-API scripts read credentials from the environment. `archivefs_v3.py` chunks at 90MB; `arfs-cat.py` reads archives without extracting.

## Dev & contributing

Follow `AGENTS.md`: verify live before claiming, fail loud (never silence errors), prefer `fd`/`rg` over `find`/`grep`. Keep the mirror in sync with the top-level directory.

## License & Security

Internal estate tooling — part of the sovereign projects, not published for external use. GitHub tokens stay in the environment, never in the repo. `mitm-proxy/` and `cache_timing.py` are dual-use (proxy tooling, timing probes) — built for auditing our own estate only.
