<<<<<<< HEAD
# Security Policy — Sovereign Estate

## Supported Versions

| Version / Subsystem | Status | Supported |
|---|---|---|
| Sovereign Master (`main`) | Active Development | :white_check_mark: Yes |
| Tau Agent Engine (`18.2.x`) | Production | :white_check_mark: Yes |
| Mesh Gateway / Shep | Active | :white_check_mark: Yes |
| Legacy Grok-Build Stack | Archived | :x: No |

---

## Reporting a Vulnerability

> [!CAUTION]
> **Zero Credential Leakage Invariant**:
> Never post live API tokens, credentials, or private keys to GitHub Issues, Pull Requests, or public discussions.

If you discover a security vulnerability, prompt-injection vector, or privilege-escalation bug within the Sovereign mesh, please report it responsibly:

1. **Private Disclosure**: Email the core maintainer or open a private [GitHub Security Advisory](../../security/advisories/new).
2. **Include Technical Context**:
   - Subsystem affected (e.g., `shep`, `sovereign-router`, `bridge`, `tau`).
   - Minimal reproduction script or vector.
   - Any observed log traces (with secrets redacted).

### Secret Boundary Commitments
- Real credentials live **exclusively** in `~/.secrets` (mode `0600`) and `.env.local`.
- Any git commit containing token patterns (`*.pat`, `*.key`, `*secret*`, `*token*`) is rejected at pre-commit.
=======
# Security Policy

## Supported Versions

Only the latest release is supported with security updates.

## Reporting a Vulnerability

To report a security issue, either:

- Email can1357 directly, or
- Open a [private security advisory](https://github.com/can1357/oh-my-pi/security/advisories/new) on GitHub

Include steps to reproduce and any relevant details. Do not open a public issue for security vulnerabilities.

## Response

Reports are handled on a best-effort basis. You can expect an initial acknowledgment within a few days.
>>>>>>> v18.3.0
