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
