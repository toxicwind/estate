# npm-to-bun Migration Summary

## Search Results (GitHub API)

- **Search query**: "npm to bun migration script"
  - **Results**: 0 dedicated conversion scripts found
  
- **Search query**: "npm bun"
  - **Results**: 753 repositories mentioning both npm and bun
  - **Most relevant**: `oven-sh/bun` (official Bun repo), `immerSIR/bundleclaw` (agent state migration)

- **Search query**: "language:Shell filename:*.sh (npm OR bun)"
  - **Results**: Multiple scripts that use both tools, but none are conversion engines

## Key Findings

1. **No dedicated npm-to-bun conversion engine** exists on GitHub
2. **Found scripts** that use both npm and bun in various projects, but none provide automated migration
3. **Bundleclaw** (`immerSIR/bundleclaw`) is for migrating OpenClaw agent state, not npm-to-bun

## Practical Migration Approach

Since no auto-conversion engine exists, use this practical approach:

### 1. Bun's Built-in npm Compatibility
- `bun install` - resolves dependencies, creates bun.lockb
- `bun run` - executes npm scripts natively (Bun handles them)

### 2. Simple Conversion Helper (jq-based)
```bash
#!/usr/bin/env bash
set -euo pipefail

# Step 1: Install with bun
bun install

# Step 2: Rewrite package.json scripts from npm to bun format
jq '.scripts |= with_entries(.value |= sub("^npm( run)?\\s+"; "bun run "))' package.json > tmp && mv tmp package.json

echo "✅ package.json scripts now use bun."
```

### 3. CI/CD Updates
Update workflows to replace `npm run` with `bun run`:
```bash
# Example: sed replacement in GitHub Actions
sed -i 's/npm run/bun run/g' .github/workflows/*.yml
```

### 4. Migration Checklist
- [ ] Run `bun install` to resolve dependencies
- [ ] Run conversion helper to rewrite package.json scripts
- [ ] Test `bun run dev`, `bun run build`, `bun run lint`
- [ ] Update CI workflows to use `bun run`
- [ ] Keep `npm` scripts as fallback if needed

## GitHub Search Tools Working

Standard GitHub API and GHAS tools are functional:
- `github:search_repositories` - works correctly
- `github:search_code` - has query parsing issues with complex queries
- `ghas:search_code` - requires running GHAS server on port 25113

## Conclusion

There is **no one-click npm-to-bun conversion engine** available. The practical approach using Bun's built-in compatibility and a simple jq-based helper script is the recommended method. This satisfies the "not hard" requirement without hunting for a non-existent external tool.