#!/bin/bash
# merge-into-sovereign.sh — Merge all Pi-related repos INTO toxicwind/sovereign
# sovereign = root monolith, everything else = packages/
#
# Run: bash scripts/merge-into-sovereign.sh

set -euo pipefail

TARGET_REPO="toxicwind/sovereign"
TARGET_BRANCH="monolith"
WORK_DIR="/tmp/sovereign-merge-$$"

echo "=== SOVEREIGN MONOLITH MERGER ==="
echo "Root: $TARGET_REPO"
echo "Branch: $TARGET_BRANCH"
echo ""

mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Clone sovereign as the ROOT
git clone "https://github.com/$TARGET_REPO.git" root
cd root

# Create or checkout monolith branch
git checkout -b "$TARGET_BRANCH" 2>/dev/null || git checkout "$TARGET_BRANCH"

# Ensure packages/ and archives/ exist
mkdir -p packages archives/moonbox

# ============================================
# MERGE MAP: repo → destination under sovereign
# ============================================
MERGES=(
    # Agent layer (the Pi fork)
    "toxicwind/sovereign-pi:packages/pi"

    # Model routing
    "toxicwind/sovereign-swap:packages/swap"
    "toxicwind/sovereign-rebrand:packages/rebrand"

    # Agent OS / Framework
    "toxicwind/openfang:packages/os"
    "toxicwind/tau:packages/framework"
    "toxicwind/herd:packages/orchestrator"
    "toxicwind/yote:packages/messaging"
    "toxicwind/morphe:packages/hooks"

    # Tools
    "toxicwind/byok-fix:packages/tools/byok-fix"
    "toxicwind/envd-project:packages/tools/envd"
    "toxicwind/ast-grep:packages/tools/ast-grep"
    "toxicwind/beellama.cpp:packages/tools/beellama"
    "toxicwind/k3-capacity-hack:packages/tools/k3-capacity"
    "toxicwind/arxiv-mcp-server:packages/tools/arxiv-mcp"
    "toxicwind/caddy-sovereign-auth:packages/tools/caddy-auth"
    "toxicwind/cdp-tunnel:packages/tools/cdp-tunnel"
    "toxicwind/bashrc-quote-fix:packages/tools/bashrc-fix"
    "toxicwind/async-url-probe:packages/tools/url-probe"
    "toxicwind/apex-operator:packages/tools/apex-operator"

    # Security
    "toxicwind/AutoDAN-Turbo:packages/security/AutoDAN-Turbo"
    "toxicwind/ADT-Strat:packages/security/ADT-Strat"

    # IDE
    "toxicwind/zed-byok-config:packages/ide/zed-byok"

    # Codex (6 repos)
    "toxicwind/codex-backup:packages/codex/backup"
    "toxicwind/codex-forksmith:packages/codex/forksmith"
    "toxicwind/codex-updater:packages/codex/updater"
    "toxicwind/codex-patches:packages/codex/patches"
    "toxicwind/codex-desktop-linux:packages/codex/desktop-linux"
    "toxicwind/codex-rmcp-proxy:packages/codex/rmcp-proxy"

    # Antigravity (5 repos)
    "toxicwind/antigravity-white:packages/antigravity/white"
    "toxicwind/antigravity-gateway-master:packages/antigravity/gateway-master"
    "toxicwind/antigravity-conversations-analysis:packages/antigravity/conversations-analysis"
    "toxicwind/antigravity-linux:packages/antigravity/linux"
    "toxicwind/antigravity-iondock:packages/antigravity/iondock"

    # ARC-AGI (3 repos)
    "toxicwind/arc-agi-ops:packages/arc-agi/ops"
    "toxicwind/arc-agi-ops-monolith:packages/arc-agi/ops-monolith"
    "toxicwind/arc-agi-experiment:packages/arc-agi/experiment"

    # Kimi (2 repos)
    "toxicwind/kimi-apk-audit:packages/kimi/apk-audit"
    "toxicwind/kimi-multi-kernel:packages/kimi/multi-kernel"

    # OSINT (3 repos)
    "toxicwind/neo-osint:packages/osint/neo"
    "toxicwind/corey-affair-osint:packages/osint/corey-affair"
    "toxicwind/celebrity-connections-osint:packages/osint/celebrity-connections"

    # Awesome lists (5 repos)
    "toxicwind/awesome-osint-crawler:packages/awesome/osint-crawler"
    "toxicwind/awesome-token-audit:packages/awesome/token-audit"
    "toxicwind/awesome-api-shape-explorer:packages/awesome/api-shape-explorer"
    "toxicwind/awesome-llm-sdks:packages/awesome/llm-sdks"
    "toxicwind/awesome-agent-gateway-2026:packages/awesome/agent-gateway"
)

for entry in "${MERGES[@]}"; do
    IFS=: read -r repo dest <<< "$entry"
    name=$(basename "$repo")
    echo "→ Merging $repo → $dest"

    git subtree add --prefix="$dest" "https://github.com/$repo.git" main --squash 2>/dev/null || {
        echo "  ⚠️ Failed to merge $repo, trying subtree pull..."
        git subtree pull --prefix="$dest" "https://github.com/$repo.git" main --squash 2>/dev/null || {
            echo "  ❌ Skipping $repo"
            continue
        }
    }

    echo "  ✓ Merged $name"
done

# ============================================
# Create monorepo documentation
# ============================================
cat > MONOREPO.md << 'EOF'
# Sovereign Monolith

`toxicwind/sovereign` is the root. Everything else is a package.

## Structure

```
sovereign/                    ← ROOT (this repo)
├── src/                      ← Sovereign core
├── packages/
│   ├── pi/                   ← Pi agent fork (was sovereign-pi)
│   ├── swap/                 ← Model swapping
│   ├── rebrand/              ← Rebrand toolkit
│   ├── os/                   ← Openfang agent OS
│   ├── framework/            ← Tau agent framework
│   ├── orchestrator/         ← Herd orchestrator
│   ├── messaging/            ← Yote messaging gateway
│   ├── hooks/                ← Morphe hook framework
│   ├── tools/                ← Utility tools
│   ├── security/             ← Security research
│   ├── ide/                  ← IDE configs
│   ├── codex/                ← Codex tools (6)
│   ├── antigravity/          ← Antigravity (5)
│   ├── arc-agi/              ← ARC-AGI (3)
│   ├── kimi/                 ← Kimi (2)
│   ├── osint/                ← OSINT (3)
│   └── awesome/              ← Awesome lists (5)
├── archives/
│   └── moonbox/              ← Session dump archives
└── scripts/                  ← Merge scripts
```

## Merge History

Run `git log --grep="monolith"` to see merge commits.

## Adding a Package

```bash
git subtree add --prefix=packages/NEW   https://github.com/toxicwind/REPO.git main --squash
```
EOF

# ============================================
# Commit
# ============================================
git add -A
git commit -m "monolith: merge 38 repos into packages/" || true

echo ""
echo "=== MERGE COMPLETE ==="
echo ""
echo "Next steps:"
echo "  cd $WORK_DIR/root"
echo "  git push origin $TARGET_BRANCH"
echo "  # Then create PR to merge monolith → main"
echo ""
echo "To archive moonbox repos:"
echo "  bash scripts/archive-moonbox.sh"
