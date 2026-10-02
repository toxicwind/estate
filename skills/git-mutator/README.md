![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/git-mutator?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/git-mutator?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/git-mutator?style=for-the-badge)

# git-mutator
Safe git operations with agentic completion auditing

## What it does
Provides safe git operations with agentic completion auditing and secret boundary verification. Manages staged/unstaged/untracked files, commits with secret boundary verification, and pushes via credential helper/SSH (no token-in-URL).

## Why it matters
Prevents accidental credential leaks and ensures audit trails for agent-mediated git operations by combining conventional git workflows with automated secret scanning and completion UUID detection.

## Who it's for
AI agents and developers performing automated git operations who need protection against credential leaks and verification that operations completed as intended.

## Features
- **Secret Boundary Verification** - Blocks commits if token patterns detected in tracked files
- **Credential Safety** - Uses git credential helper or SSH only (never token-in-URL)
- **Agentic Audit** - Scans for completion UUIDs, .claude/.codex/.cursor artifacts, and secret leaks
- **SSOT Respect** - Excludes `/home/toxic/sovereign/config/ports.env` from secret scanning
- **Dry-run Mode** - `--dry-run` previews operations without executing
- **Conventional Commits** - Enforces conventional commit format (feat:, fix:, chore:, etc.)
- **Automatic .gitignore** - Adds `.bak.` files to .gitignore automatically

## Quick Start
```bash
# Show git status
bun helpers/git-mutator/cli.ts status

# Scan for secrets
bun helpers/git-mutator/cli.ts scan-secrets

# Agentic completion audit
bun helpers/git-mutator/cli.ts agentic-audit

# Commit with conventional message
bun helpers/git-mutator/cli.ts commit "feat: add new feature"

# Audit → commit → push (blocks on leaks)
bun helpers/git-mutator/cli.ts commit-push "feat: add thing"

# Diff two config files
bun helpers/git-mutator/cli.ts diff-configs config/herd.yaml config/llama-swap.yaml
```

## Configuration
- **Location**: `/home/toxic/sovereign/helpers/git-mutator/` (modular Bun/TS helper - 6 files)
- **Port SSOT**: `/home/toxic/sovereign/config/ports.env` (excluded from secret scanning)
- **Git Ignore**: `/home/toxic/sovereign/.gitinnie` (security boundaries)

## Development
Modify the TypeScript source in `/home/toxic/sovereign/helpers/git-mutator/`:
- `cli.ts` - Command-line interface
- `git.ts` - Core git operations
- `api.ts` - API definitions
- `errors.ts` - Error handling
- `types.ts` - Type definitions
- `index.ts` - Entry point

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Secret Scanning**: Detects tokens, keys, credentials, passwords, SSH/GPG materials, config files, and auth materials
- **SSOT Protection**: Explicitly excludes ports.env from secret scanning
- **Credential Handling**: Never uses token-in-URL, relies on credential helper or SSH
- **Agent Artifact Detection**: Scans for .claude/, .codex/, .cursor directories