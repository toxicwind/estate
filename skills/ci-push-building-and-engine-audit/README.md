# ci-push-building-and-engine-audit

[![for-the-badge](https://img.shields.io/badge/CI-CD-2F80ED?style=for-the-badge)](https://ci-cd.example.com) [![for-the-badge](https/img.shields.io/badge/Engine_Audit-ED8533?style=for-the-badge)](https://engine-audit.example.com) [![for-the-badge](https://img.shields.io/badge/Version_Semantic-EDD327?style=for-the-badge)](https://semver.org)

## ci-push-building-and-engine-audit

Automated CI/CD push building via brand and engine migration auditing. Ensures sovereign fork enhancements and CI/CD status are always documented and preserved.

### When setting up push-building or auditing engine fork migrations in sovereign projects:

1. **Use `push-build.sh` to queue versioned builds into `brand` (port 25148) upon commit**
2. **Analyze engine vs vendor diffs using pandas DataFrames over `engine-vendor-diff.csv`** to ensure all custom features (OAuth refresh, storage contracts, API key logins) are preserved
3. **Keep README.md updated with sovereign fork enhancements and CI/CD status**

### Features

- **Push build dispatch**: `push-build.sh` queues versioned builds into `brand` (port 25148) upon commit
- **Engine migration auditing**: Analyze engine vs vendor diffs using pandas DataFrames over `engine-vendor-diff.csv`
- **Custom feature preservation**: Ensures OAuth refresh, storage contracts, API key logins are preserved across engine migrations
- **README integration**: Keeps README.md updated with sovereign fork enhancements and CI/CD status

### Quick start (3 commands max)

```bash
# Trigger a push build on commit (via git post-commit hook)
# The hook runs push-build.sh which submits to brand queue at port 25148

# Analyze engine vs vendor diffs
python3 -c "
import pandas as pd
diff = pd.read_csv('engine-vendor-diff.csv')
# Check for preserved custom features
features = ['OAuth refresh', 'storage contracts', 'API key logins']
for f in features:
    if f in diff['feature'].values:
        print(f'Preserved: {f}')
    else:
        print(f'MISSING: {f}')
"

# Verify CI/CD status
curl http://127.0.0.1:25148/status
```

### Architecture

The ci-push-building-and-engine-audit skill combines two concerns:

1. **Push building** (from `cicd-push-building`): git post-commit hook → `push-build.sh` → brand queue (port 25148) → dispatched builds
2. **Engine auditing**: pandas DataFrame analysis of `engine-vendor-diff.csv` to diff custom features between sovereign engine and vendor baseline

The engine-vendor-diff.csv contains rows of features with columns for: feature name, status (preserved/missing/altered), and migration notes. The pandas DataFrame analysis reports which custom features survived the engine fork migration.

### Config / optional services

- `/home/toxic/estate/helpers/push-build.sh` — push build dispatch script
- Brand queue at port 25148 — receives and processes queue entries
- `engine-vendor-diff.csv` — engine vs vendor feature diff dataset
- pandas — for DataFrame-based diff analysis (may need `pip install pandas`)
- Toolchain detection (bun, rust, go, python) from `cicd-push-building`

### Dev / contributing

- Ensure `engine-vendor-diff.csv` is kept up to date with each engine migration
- Add new feature tracking columns to the diff CSV as new custom features are added
- Verify brand queue is running before expecting auto-dispatch on commits
- Keep README.md synchronized with new sovereign fork enhancements
- pandas must be available for the diff analysis script

### License

Open Claw — see `skill.toml` for details.

### Security

- `engine-vendor-diff.csv` contains sensitive feature mapping — restrict access
- OAuth refresh, storage contracts, API key logins must not be lost during engine migration
- Brand queue should be internal-facing; exposure could trigger unintended builds