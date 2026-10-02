# cicd-push-building

[![for-the-badge](https://img.shields.io/badge/Bun-000000?style=for-the-badge)](https://bun.sh) [![for-the-badge](https://img.shields.io/badge/Semantic_Version-EDD327?style=for-the-badge)](https://semver.org) [![for-the-badge](https://img.shields.io/badge/Git_Post-Commit-FFD700?style=for-the-badge)](https://git-scm.com)

## cicd-push-building

Automated CI/CD push building via brand and git hooks with semantic versioning. Push build dispatch script automates versioned builds into the brand queue.

### Features

- **Push build dispatch script**: `/home/toxic/sovereign/helpers/push-build.sh` — dispatches versioned builds to brand
- **Automatic version extraction**: Extracts version from `packages/coding-agent/package.json` or root `package.json` (e.g. `v18.3.0`)
- **Toolchain detection**: Automatically detects toolchain (`bun`, `rust`, `go`, `python`) and submits JSON payload to `/home/toxic/brand/queue/`
- **Git post-commit hook**: Triggers build automatically on commit

### Quick start (3 commands max)

```bash
# Ensure the post-commit hook is active (installed via git template)
# On commit, the hook automatically runs:
/home/toxic/sovereign/helpers/push-build.sh

# Or manually trigger a build:
/home/toxic/sovereign/helpers/push-build.sh

# Check the brand queue status
curl http://127.0.0.1:25148/queue
```

### Architecture

The git `post-commit` hook is configured at clone time and runs `/home/toxic/sovereign/helpers/push-build.sh` on every commit. The script:
1. Extracts the version from package.json (or root package.json)
2. Detects the toolchain in use
3. Submits a JSON payload to the brand queue at port 25148
4. The payload includes: version, toolchain, git commit SHA, and timestamp

Brand then processes the queue and dispatches builds to the appropriate build agents.

### Config / optional services

- `/home/toxic/sovereign/helpers/push-build.sh` — dispatch script (required)
- Brand queue at port 25148 — receives JSON payloads
- `packages/coding-agent/package.json` or root `package.json` — version source
- Toolchain auto-detection for: bun, rust, go, python

### Dev / contributing

- Ensure the git post-commit hook is installed (cloned via estate template)
- Verify `push-build.sh` is executable and paths are correct
- Add new toolchain detection by extending the script's toolchain logic
- Ensure package.json versions follow semantic versioning (major.minor.patch)
- Brand queue must be running on port 25148 for automatic dispatch

### License

Open Claw — see `skill.toml` for details.

### Security

- Version is extracted from package.json — do not commit snapshot versions that diverge from reality
- Brand queue endpoint should be kept internal; exposure could trigger unintended builds