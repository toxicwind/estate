name: repo-audit
description: >
  Audit GitHub repositories and recommend privacy settings based on naming patterns,
  descriptions, and topics. Uses gh CLI to fetch repository data, then analyzes with
  pandas/pyarrow to output recommendations as CSV or Parquet.

## Concept

This skill helps identify repositories that might accidentally expose sensitive information
by analyzing repository names, descriptions, and topics for patterns indicating they
should be private (e.g., containing words like "secret", "token", "credential", etc.).

Outputs a analysis report showing which public repos should be made private and vice versa.

## Dynamic argv

```bash
python3 sovereign/skills/repo-audit/audit.py \
  --user toxicwind \
  --output repo-audit-analysis \
  --format both \
  --threshold 10 \
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

## Procedure

1. **Fetch**: Uses `gh api` to paginate through all repositories for the specified user/org
2. **Filter**: Optionally filters by star count and current visibility (public/private)
3. **Analyze**: For each repository:
   - Fetches topics via GitHub API
   - Checks name, description, and topics for private-indicating patterns
   - Determines if repo should be private based on patterns
4. **Output**: Results written as CSV and/or Parquet with columns:
   - owner, name, visibility (public/private), private (bool), should_be_private (bool)
   - reasons (why it should be private), stars, fork, description, topics, html_url

## Pattern Detection

The analysis looks for these case-insensitive patterns in repo names, descriptions, and topics:
- secret, token, key, credential, password, passwd
- private, internal, confidential, proprietary
- cert, certificate, ssh, gpg, pem, p12, pfx
- config, settings, env, .env, dotenv
- cred, auth, oauth, ssl, tls

If any pattern is found, the repo is flagged as "should be private".

## Output Examples

### CSV Output (first few rows):
```
owner,name,visibility,private,should_be_private,reasons,stars,fork,description,topics,html_url
toxicwind,pi-agent,public,false,true,name contains 'agent',154,false,Agentic AI coding agent,,https://github.com/toxicwind/pi-agent
toxicwind,tau,public,false,true,name contains 'tau',420,false,The Tau language and ecosystem,,https://github.com/toxicwind/tau
```

### Parquet Output:
Same data as CSV but in efficient columnar format with compression.

## Examples

```bash
# Basic audit of your repos
python3 sovereign/skills/repo-audit/audit.py --user toxicwind

# Audit with minimum 10 stars, output both formats
python3 sovereign/skills/repo-audit/audit.py --user toxicwind --threshold 10 --format both

# Only check public repos that might need to be private
python3 sovereign/skills/repo-audit/audit.py --user toxicwind --public-only

# Only check private repos that might be safe to make public
python3 sovereign/skills/repo-audit/audit.py --user toxicwind --private-only

# Specify custom output name
python3 sovereign/skills/repo-audit/audit.py --output my-repo-analysis --format parquet
```

## Dependencies

- `gh` CLI (GitHub CLI) - must be authenticated
- Python 3.7+
- `pandas` (optional, for DataFrame handling)
- `pyarrow` (optional, for Parquet output)

Install Python dependencies with:
```bash
pip install pandas pyarrow
```

The script will work without pandas/pyarrow but will only output CSV format.