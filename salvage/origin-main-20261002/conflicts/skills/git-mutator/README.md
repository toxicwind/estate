<div align="right">

[![license: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-1f6feb?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

# git-mutator

> Safe git operations with agentic completion auditing and secret boundary verification.

> **Why care?** Agents commit and push constantly — and one leaked token in a URL or one un-audited completion UUID can poison the repo. git-mutator wraps status/diff/commit/push with secret scanning and completion auditing, and `commit-push` blocks the push when it finds a leak.

- **Safe mutations** — `status`, `diff`, `commit`, `push`, `commit-push` with conventional-commit messages
- **Secret boundary** — `scan-secrets` catches credential patterns; pushes use credential helper/SSH, never token-in-URL
- **Agentic audit** — `agentic-audit` checks completion UUIDs, agent artifacts, and secret leaks
- **Repo hygiene** — `ensure-gitignore` adds security patterns; `diff-configs` diffs two config files

```mermaid
flowchart LR
    YOU[you / agent] --> CLI[git-mutator cli]
    CLI --> AUDIT[scan-secrets + agentic-audit]
    AUDIT -->|clean| COMMIT[commit]
    AUDIT -->|leak| BLOCK[blocked]
    COMMIT --> PUSH[push via credential helper / SSH]
```

## Quick start

```bash
bun helpers/git-mutator/cli.ts status
bun helpers/git-mutator/cli.ts scan-secrets
bun helpers/git-mutator/cli.ts commit-push "feat: safe change"
```

| Command | Description |
|---|---|
| `status` | Show git status (staged/unstaged/untracked) |
| `diff [--staged]` | Show diff (working tree or staged) |
| `commit <msg>` | Commit with conventional commit message |
| `push [remote] [branch]` | Push via credential helper/SSH |
| `commit-push <msg>` | Audit → commit → push (blocks on leaks) |
| `ensure-gitignore` | Add security patterns to .gitignore |
| `scan-secrets [files]` | Scan for credential patterns |
| `agentic-audit [files]` | Audit completion UUIDs, agent artifacts, secret leaks |
| `diff-configs <A> <B>` | Diff two config files |

## License & security

- **License:** [MIT](https://github.com/toxicwind/sovereign-projects#license)
- **Security:** this tool exists to enforce the secret boundary — `commit-push` refuses to push when `scan-secrets` finds a leak. Never bypass with a raw `git push` carrying a token in the URL; see `SKILL.md` for the full trigger list and conventions.
