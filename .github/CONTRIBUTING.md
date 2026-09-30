# Contributing to Sovereign

> **The Sovereign Framework is a self-hosted operating environment where a working agent fleet lives** — inference routing, HMAC-signed agent chat, and pitchfork-supervised service daemons.

---

## Standing Development Rules

Before committing or submitting changes:

1. **MAXIMAL, NOT SIMPLEST**:
   - Always choose the maximal, complete solution. Half-measures and stub implementations are rejected.
   - Every fix must cover edge cases, error handlers, and all callers.
2. **AUDIT = Production-Grade Repair**:
   - Audits must implement concrete, tested code repairs — never report-only.
3. **Port SSOT Rule**:
   - Never invent or hardcode port numbers in application code. All `25xxx` ports are assigned in `config/ports.env`.
4. **Tooling Standards**:
   - Use `fd` and `rg` for search (or `ffs find` / `ffs grep`). Never use legacy `find` or `grep`.
   - Run `syntax-guard <file>` before committing to guarantee 0 syntax errors.
5. **Git Protocol**:
   - Commit after every unit of work.
   - Pull-before-push with rebase; never force-push without backup branches.

---

## Local Verification Suite

Run these verification commands before creating a Pull Request:

```bash
# 1. Verify filesystem health and bin symlinks
bun helpers/estate-scanner.ts

# 2. Run Tau audit suite
tau audit

# 3. Pre-flight syntax validation
syntax-guard <modified_files>

# 4. Verify live 25xxx services
bun helpers/health-audit.ts --json
```
