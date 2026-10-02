![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/repo-audit?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/repo-audit?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/repo-audit?style=for-the-badge)

# repo-audit
Audit GitHub repositories and local project structure

## What it does
Comprehensive repository auditing with two approaches: 1) Remote analysis using GitHub CLI for privacy risk assessment, 2) Local analysis scanning filesystem for git repos and building hierarchical structure DataFrame.

## Why it matters
Enables proactive identification of privacy risks (public repos containing sensitive data) and provides visibility into local git repository organization, duplicates, symlinks, and structural issues.

## Who it's for
DevOps engineers, security analysts, and developers who need to audit repository visibility, detect accidental public exposure of sensitive code, and understand local git repository landscapes.

## Features
- **Remote Analysis** (`repo_audit.py`) - Uses `gh` CLI to fetch and analyze GitHub repositories for privacy risks via naming/description/topic patterns
- **Local Analysis** (`local_audit.py`) - Scans local filesystem for git repos, builds hierarchical DataFrame with tree structure
- **Multiple Output Formats** - CSV, Parquet, or both formats supported
- **Privacy Pattern Detection** - Flags repos containing secret/token/credential/config/auth-related terms that should be private
- **Tree Structure Output** - Hierarchical path visualization showing repo locations in filesystem
- **Cross-Referencing** - Maps remote repos to local paths using projects.env
- **Duplicate Detection** - Identifies orphaned repos, symlink chains, circular references, submodules, and subtrees

## Quick Start
```bash
# Local-first audit (recommended for performance & privacy)
python3 sovereign/skills/repo-audit/local_audit.py \
  --scan /home/toxic/projects \
  --output local-projects \
  --format both \
  --tree

# Remote GitHub privacy audit
python3 sovereign/skills/repo-audit/repo_audit.py \
  --user toxicwind \
  --output repo-audit-analysis \
  --format both

# Local audit with tree view and depth limit
python3 sovereign/skills/repo-audit/local_audit.py \
  --scan /home/toxic \
  --tree \
  --depth 2 \
  --output overview

# Cross-reference local and remote
python3 sovereign/skills/repo-audit/repo_audit.py \
  --user toxicwind \
  --load-env-map \
  --format json
```

## Configuration
- **Dependencies**:
  - `gh` CLI (GitHub CLI) - required for `repo_audit.py` only
  - Python 3.7+
  - `pandas` (required for both scripts)
  - `pyarrow` (optional, for Parquet output)

- **local_audit.py Parameters**:
  - `--scan`: Directory to scan for git repos (default: `/home/toxic/projects`)
  - `--output`: Output file basename (default: `local-projects`)
  - `--format`: Output format - csv, parquet, or both (default: `both`)
  - `--tree`: Show tree structure in output (default: `false`)
  - `--depth`: Max tree depth (-1 for unlimited, default: `-1`)
  - `--min-stars`: Minimum stars for GitHub sync (default: `0`)
  - `--exclude-archived`: Exclude archived repos (default: `true`)
  - `--follow-symlinks`: Follow symlinks when scanning (default: `false`)
  - `--include-bare`: Include bare repositories (default: `false`)

- **repo_audit.py Parameters**:
  - `--user`, `-u`: GitHub username/org (default: `toxicwind` or `$GH_USER`)
  - `--output`, `-o`: Output file basename (default: `repo-audit`)
  - `--format`, `-f`: Output format - csv, parquet, or both (default: `both`)
  - `--threshold`, `-t`: Minimum stars for analysis (default: `0`)
  - `--private-only`: Analyze only private repos (default: `false`)
  - `--public-only`: Analyze only public repos (default: `false`)
  - `--load-env-map`: Load projects.env for cross-referencing (default: `true`)

## Development
Modify the Python scripts in `/home/toxic/estate/skills/repo-audit/`:
- `repo_audit.py` - Remote GitHub analysis
- `local_audit.py` - Local filesystem scanning
- Supporting files: `audit.py`, `local_audit.py`, `projects.env`

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Privacy-First**: Local analysis preferred to avoid exposing repo structure to external APIs
- **Pattern-Based Detection**: Identifies potentially private repos through name/description/topic analysis
- **No Raw Credentials**: Uses `gh` CLI authentication rather than storing tokens
- **Environment Mapping**: Optional cross-referencing via projects.env without exposing sensitive data