# repo-audit — Maximal Repository Auditor

Local-first repository visibility auditor. Scans all local git repos, builds a pandas DataFrame with tree hierarchy, identifies duplicates/symlinks/orphans, and recommends privacy settings.

## Concept

**Local-first**: All data comes from local disk. No GitHub API calls needed. Uses `git log` to read commit metadata, pandas for analysis, pyarrow for parquet export.

Two scripts:
- `local_audit.py` — Local-first auditor (no gh CLI needed)
- `repo_audit.py` — GitHub API auditor (for upstream analysis)

## Architecture

```
Local Disk (.git scan) → pandas DataFrame → Tree Hierarchy → Recommendations
                                    ↓
                          Parquet + CSV + JSON Export
                                    ↓
                          Duplicate/Symlink/Orphan Detection
```

## Local-First Audit

```bash
# Scan all local repos (projects + sovereign)
python local_audit.py --all

# Scan specific path
python local_audit.py --path /home/toxic/projects

# With parquet export
python local_audit.py --all --parquet out.parquet

# Show duplicates and stale repos
python local_audit.py --all --duplicates --orphans
```

### CLI Flags

| Flag | Description |
|------|-------------|
| `--path <dir>` | Path to scan (default: /home/toxic/projects) |
| `--all` | Scan both projects and sovereign |
| `--duplicates` | Show repos with duplicate names |
| `--orphans` | Show repos with no activity (>90d) |
| `--format {table,csv,json,parquet}` | Output format |
| `--parquet <path>` | Parquet export path |
| `--csv <path>` | CSV export path |
| `--json <path>` | JSON export path |

### DataFrame Schema

| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Repo name |
| `path` | str | Absolute path on disk |
| `area` | str | `projects`, `sovereign`, or `other` |
| `last_commit` | str | ISO date of last commit |
| `message` | str | Commit message |
| `commit` | str | Short commit hash (8 chars) |
| `author` | str | Commit author |

## GitHub API Audit

```bash
# Full GitHub audit with privacy recommendations
python repo_audit.py --user toxicwind --format parquet --parquet audit.parquet

# Multi-user audit
python repo_audit.py --users toxicwind,sovereign --bun

# Specific repos
python repo_audit.py --repos toxicwind/pi,toxicwind/tau --bun --json
```

### repo_audit.py Features

- **Naming pattern scoring**: weighted private/public indicators
- **Topic-based anomaly detection**: sensitive topic heatmap
- **Bun version detection**: via gh API
- **Agentic prompts**: auto-generated gh commands
- **Parquet/CSV/JSON export**: via pyarrow/pandas

## Tree Hierarchy

The local audit produces a tree view by area:

```
🌿 PROJECTS (291 repos)
────────────────────────────────────────────────────────────────
  📁 sovereign-projects  2026-09-10 22:24:45  trigger CI after making repo
  📁 pi-vault-mind       2026-09-09 05:45:28  maximal: full config keys
  📁 codeshift           2026-09-07 13:40:06  feat(config): maximal herd
  ...

🌿 SOVEREIGN (control plane)
────────────────────────────────────────────────────────────────
  📁 maximal-sovereign-agentic-audit  ...
  📁 repo-visibility-audit            ...
  ...
```

## Symlink Map

First-class symlinks in the monorepo:

| Symlink | Target | Purpose |
|---------|--------|---------|
| `.shared` | `/home/toxic/.sovereign-shared` | Shared resources |
| `.shared-helpers` | `/home/toxic/sovereign/helpers` | Operational helpers |

Duplicate symlinks removed: `tau`, `tau-extensions`, `pi-agent`, `qed`, `effusion-labs`, `arlockworks-*`

## Env Map

`projects.env` contains 327 project mappings:

```
PROJECT_NAME=PATH:AREA:LAST_LOCAL_PUSH:GH_PRIVATE:GH_PRIVATE_SCORE:GH_RECOMMENDATION
```

Example:
```
sovereign-scripts=/home/toxic/projects/sovereign-projects/sovereign-scripts:projects:2026-08-24 06:08:00:False:21.0:PRIVATE
infra-recon=/home/toxic/projects/infra-recon:projects:2026-08-24 06:08:00:False:14.0:PRIVATE
```

## Dependencies

- Python 3.12+
- `pandas` (≥3.0.0)
- `pyarrow` (≥25.0.0)
- `gh` CLI (optional, for GitHub API audit)

## Examples

```bash
# Local-first audit (no network needed)
python local_audit.py --all --parquet local-repos.parquet

# GitHub privacy audit
python repo_audit.py --user toxicwind --format parquet

# Full audit: local tree + GitHub privacy analysis
python local_audit.py --all && python repo_audit.py --user toxicwind
```
