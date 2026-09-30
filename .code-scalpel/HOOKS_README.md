# Code Scalpel hooks

Governance enforcement on every file operation — Claude Code hooks *and* git hooks, wired to the Code Scalpel policy engine.

<div align="right">

[![license: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-main-6e56cf?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

## Why this exists

Agents change code fast. Policies in `policy.yaml` are just words unless something **runs them** — this directory is that something. Two enforcement layers, one audit trail:

- **Claude Code hooks** intercept tool calls *before* they run — a policy violation never reaches the filesystem.
- **Git hooks** enforce at commit time — nothing sneaks into history uncovered.

## What it enforces

- **PreToolUse** — validates every Edit, Write, Bash, and MultiEdit call against governance policies.
- **PostToolUse** — logs every operation to the audit trail.
- **pre-commit** — verifies audit coverage for all staged changes.
- **commit-msg** — logs commits to the audit trail.
- Three enforcement modes, per rule: `audit-only` → `warn` → `block`.

```mermaid
flowchart LR
    OP[file operation] --> PRE{PreToolUse hook}
    PRE -->|policy allows| RUN[tool executes]
    PRE -->|policy denies<br/>(block mode)| DENY[blocked, logged]
    RUN --> POST[PostToolUse → audit.log]
    C[git commit] --> PC[pre-commit: audit coverage check]
    PC -->|covered| CM[commit-msg → audit trail]
    PC -->|not covered| FAIL[commit refused]
```

## Quick start

```bash
code-scalpel install-hooks        # Claude Code hooks → .claude/settings.json
code-scalpel install-git-hooks    # git pre-commit + commit-msg hooks
code-scalpel install-hooks --user # user-level Claude Code settings
```

## Architecture

| Layer | Trigger | Enforcement point |
|---|---|---|
| Claude Code hooks | `PreToolUse` / `PostToolUse` events | `code-scalpel hook pre-tool-use` / `post-tool-use` |
| Git hooks | `pre-commit` / `commit-msg` | `code-scalpel verify-audit-coverage <file>` |

Manual invocation (used by the hooks internally — you can also run them by hand):

```bash
code-scalpel hook pre-tool-use   # governance validation
code-scalpel hook post-tool-use  # audit logging
code-scalpel uninstall-hooks     # remove
```

### Enforcement modes

| Mode | Behavior |
|---|---|
| `audit-only` | Log all operations without blocking |
| `warn` | Warn on violations, allow operations |
| `block` | Block operations that violate policy |

Mode is per-policy, configured in `.code-scalpel/policy.yaml`. Start in `audit-only`, graduate to `block` once the audit trail looks clean.

### Hook configuration

The Claude Code hook wiring lives in `.claude/settings.json` (installed by `install-hooks`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "name": "code-scalpel-governance",
        "match": { "tools": ["Edit", "Write", "Bash", "MultiEdit"] },
        "command": "code-scalpel hook pre-tool-use",
        "onFailure": "block"
      }
    ]
  }
}
```

## Config

All knobs live in `.code-scalpel/`:

| File | Role |
|---|---|
| `policy.yaml` | security rules + enforcement mode (the source of truth) |
| `budget.yaml` | change-budget limits — blast-radius control |
| `config.json` | governance and enforcement settings |
| `dev-governance.yaml` | dev-environment governance profile |
| `ide-extension.json` | IDE extension wiring |
| `response_config.json` / `.schema.json` | hook response shaping |
| `policy.manifest.json` | signed manifest for tamper detection (optional) |
| `audit.log` | audit trail of policy decisions (auto-generated, never hand-edit) |
| `autonomy_audit/` | autonomy engine audit logs (auto-generated) |

## Dev

Full documentation: [IDE enforcement & governance](https://github.com/3D-Tech-Solutions/code-scalpel/blob/main/docs/architecture/IDE_ENFORCEMENT_GOVERNANCE.md) (upstream).

## License & security

MIT where marked — [LICENSE](https://github.com/toxicwind/sovereign-projects#license). `audit.log` and `autonomy_audit/` are append-only trails: don't edit them by hand or you break the tamper story the trail exists to tell. License keys (`license/license.jwt`) are never committed — see [license/](license/).
