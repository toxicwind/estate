---
name: git-mutator
description: >
  Safe git operations with agentic completion auditing. Manages staged/unstaged/untracked files,
  commits with secret boundary verification, pushes via credential helper/SSH (no token-in-URL).
  Triggers on: "commit", "push", "git status", "scan secrets", "agentic audit", "git diff",
  "commit-push", "ensure gitignore", "diff configs", "git-mutator", "git mutations".
---

# Git Mutator

## Usage

Run `bun helpers/git-mutator/cli.ts <command>` to perform safe git operations with
agentic completion auditing and secret boundary verification.

## Commands

| Command                  | Description                                           |
| ------------------------ | ----------------------------------------------------- |
| `status`                 | Show git status (staged/unstaged/untracked)           |
| `diff [--staged]`        | Show diff (working tree or staged)                    |
| `commit <msg>`           | Commit with conventional commit message               |
| `push [remote] [branch]` | Push to remote via credential helper/SSH              |
| `commit-push <msg>`      | Audit → commit → push (blocks on leaks)               |
| `ensure-gitignore`       | Add security patterns to .gitignore                   |
| `scan-secrets [files]`   | Scan for credential patterns                          |
| `agentic-audit [files]`  | Audit completion UUIDs, agent artifacts, secret leaks |
| `diff-configs <A> <B>`   | Diff two config files                                 |
| `help`                   | Show usage                                            |

## Tool calls

```bash
bun /home/toxic/sovereign/helpers/git-mutator/cli.ts status
bun /home/toxic/sovereign/helpers/git-mutator/cli.ts agentic-audit
bun /home/toxic/sovereign/helpers/git-mutator/cli.ts commit-push "feat: add thing"
bun /home/toxic/sovereign/helpers/git-mutator/cli.ts diff-configs config/herd.yaml config/llama-swap.yaml
bun /home/toxic/sovereign/helpers/git-mutator/cli.ts scan-secrets
```

## Behavior

- **Secret boundary**: blocks commits if token patterns detected in tracked files
- **Credential safety**: uses git credential helper or SSH only (never token-in-URL)
- **Agentic audit**: scans for completion UUIDs, .claude/.codex/.cursor artifacts, secret leaks
- **SSOT respect**: excludes `/home/toxic/sovereign/config/ports.env` from secret scanning
- **Dry-run mode**: `--dry-run` previews without executing

## Constraints

- Commit messages must follow conventional commit format (`feat:`, `fix:`, `chore:`, etc.)
- `.bak.` files are added to `.gitignore` automatically
- `commit-push` audits first and blocks on any secret leak
- The SOVEREIGN_PORT_SSOT (`/home/toxic/sovereign/config/ports.env`) is excluded from secret scanning

## Files

- `/home/toxic/sovereign/helpers/git-mutator/` — modular Bun/TS helper (6 files)
- `/home/toxic/sovereign/config/ports.env` — port SSOT
- `/home/toxic/sovereign/.gitignore` — security boundaries
