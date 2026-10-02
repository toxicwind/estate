# CI/CD Push Building & Engine Migration

When setting up push-building or auditing engine fork migrations in sovereign projects:
1. Use `push-build.sh` to queue versioned builds into `brand` (port 25148) upon commit.
2. Analyze engine vs vendor diffs using pandas DataFrames over `engine-vendor-diff.csv` to ensure all custom features (OAuth refresh, storage contracts, API key logins) are preserved.
3. Keep README.md updated with sovereign fork enhancements and CI/CD status.