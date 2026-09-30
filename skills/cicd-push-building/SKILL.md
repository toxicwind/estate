---
name: cicd-push-building
description: Automated CI/CD push building via brand and git hooks with semantic versioning
---

# CI/CD Push Building with Brand

- Push build dispatch script: `/home/toxic/sovereign/helpers/push-build.sh`
- Automatically extracts the version from `packages/coding-agent/package.json` or root `package.json` (e.g. `v18.3.0`).
- Automatically detects toolchain (`bun`, `rust`, `go`, `python`) and submits a JSON payload to `/home/toxic/brand/queue/`.
- Git `post-commit` hook triggers this automatically on commit.
