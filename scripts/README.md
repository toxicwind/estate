# @estate/scripts

Consolidated repository of operational, CI/CD, release, benchmark, and auditing scripts for the estate-scripts Estate.

## Highlights
- **`pattern-borrow.ts`**: GitHub-wide pattern retrieval and borrower with automatic token fallback (`hosts.yml` / `GH_TOKEN`).
- **`ci-*.ts`**: Comprehensive release build, checksum, publish, and test scripts.
- **`test`**: Executed with Bun parallel test runner (`bun test --coverage`).

## Usage
```bash
bun test --coverage
bun pattern-borrow.ts "query"
```
