name: repo-audit
description: >
  Audit GitHub repositories and local project structure. Provides two approaches:
  1. repo_audit.py - Uses gh CLI to fetch remote repository data for privacy analysis
  2. local_audit.py - Scans local filesystem for git repos, builds tree structure DataFrame

## Concept

This skill provides comprehensive repository auditing capabilities:
- **Remote analysis** (repo_audit.py): Analyze GitHub repositories for privacy risks using naming patterns and topics
- **Local analysis** (local_audit.py): Scan local project structure, build hierarchical DataFrame, identify duplicates/symlinks
- Both outputs can be exported as CSV, Parquet, or JSON
- Local-first approach preferred for performance and privacy

## Dynamic argv (local_audit.py)

```bash
python3 sovereign/skills/repo-audit/local_audit.py \
  --scan /home/toxic/projects \
  --output local-projects \
  --format both \
  --tree
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scan` | `/home/toxic/projects` | Directory to scan for git repositories |
| `--output`, `-o` | `local-projects` | Output file basename (without extension) |
| `--format`, `-f` | `both` | Output format: csv, parquet, or both |
| `--tree` | `false` | Show tree structure in output |
| `--depth` | `-1` | Maximum tree depth to display (-1 for unlimited) |
| `--min-stars` | `0` | Minimum stars for GitHub sync (if applicable) |
| `--exclude-archived` | `true` | Exclude archived repositories from analysis |
| `--follow-symlinks` | `false` | Follow symlinks when scanning |
| `--include-bare` | `false` | Include bare repositories |

## Dynamic argv (repo_audit.py)

```bash
python3 sovereign/skills/repo-audit/repo_audit.py \
  --user toxicwind \
  --output repo-audit-analysis \
  --format both \
  --threshold 0 \
  --public-only
```

| Flag | Default | Description |
|------|---------|-------------|
| `--user`, `-u` | `toxicwind` (or `$GH_USER`) | GitHub username or organization to audit |
| `--output`, `-o` | `repo-audit` | Output file basename (without extension) |
| `--format`, `-f` | `both` | Output format: csv, parquet, or both |
| `--threshold`, `-t` | `0` | Minimum stars to consider for analysis |
| `--private-only` | `false` | Only analyze currently private repositories |
| `--public-only` | `false` | Only analyze currently public repositories |
| `--load-env-map` | `true` | Load projects.env for cross-referencing |

## Procedure (local_audit.py)

1. **Scan**: Walk the specified directory recursively to find `.git` directories
2. **Extract**: For each git repo:
   - Read git config (remote.origin.url)
   - Get latest commit hash, date, and message
   - List local branches
   - Check for uncommitted changes
   - Determine if repo is bare
   - Calculate size and file counts
3. **Build Tree**: Construct hierarchical tree based on directory structure
4. **Analyze**: Identify:
   - Duplicate remotes (same URL appearing multiple times)
   - Orphaned repos (no remote or inaccessible)
   - Symlink chains and circular references
   - Submodules and subtrees
5. **Output**: Results written as CSV and/or Parquet with columns:
   - path, name, remote_url, latest_commit, commit_date, branch_count
   - has_changes, is_bare, size_mb, file_count, depth, parent_path
   - tree_path (hierarchical path)

## Procedure (repo_audit.py)

1. **Fetch**: Uses `gh api` to paginate through all repositories for the specified user/org
2. **Filter**: Optionally filters by star count and current visibility (public/private)
3. **Analyze**: For each repository:
   - Fetches topics via GitHub API
   - Checks name, description, and topics for private-indicating patterns
   - Determines if repo should be private based on patterns
4. **Cross-reference**: Optionally loads projects.env to map repos to local paths
5. **Output**: Results written as CSV and/or Parquet with columns:
   - owner, name, visibility, private, should_be_private, reasons
   - stars, fork, description, topics, html_url
   - local_path (if env map loaded and match found)
   - dup_count (number of local copies found)

## Pattern Detection (repo_audit.py)

The analysis looks for these case-insensitive patterns in repo names, descriptions, and topics:
- secret, token, key, credential, password, passwd
- private, internal, confidential, proprietary
- cert, certificate, ssh, gpg, pem, p12, pfx
- config, settings, env, .env, dotenv
- cred, auth, oauth, ssl, tls

If any pattern is found, the repo is flagged as "should be private".

## Tree Structure Output (local_audit.py)

When `--tree` is enabled, the output includes a `tree_path` column showing the hierarchical location:
```
/home/toxic/projects/
├── sovereign-projects/
│   ├── tau/
│   ├── llama-swap/
│   └── qed/
├── .archive/
│   └── ComfyUI-*/ (archived)
├── websites/
│   └── effusion-labs/
└── sovereign/
    ├── helpers/
    └── src/
```

## Examples

```bash
# Local-first audit (recommended)
python3 sovereign/skills/repo-audit/local_audit.py --scan /home/toxic/projects --format both --tree

# Remote GitHub privacy audit
python3 sovereign/skills/repo-audit/repo_audit.py --user toxicwind --format both

# Local audit with tree view and depth limit
python3 sovereign/skills/repo-audit/local_audit.py --scan /home/toxic --tree --depth 2 --output overview

# Cross-reference local and remote
python3 sovereign/skills/repo-audit/repo_audit.py --user toxicwind --load-env-map --format json
```

## Dependencies

- `gh` CLI (GitHub CLI) - for repo_audit.py only
- Python 3.7+
- `pandas` (required for both scripts)
- `pyarrow` (optional, for Parquet output)

Install Python dependencies with:
```bash
pip install pandas pyarrow
```

The scripts will work without pyarrow but will only output CSV format.