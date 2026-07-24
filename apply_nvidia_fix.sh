#!/bin/bash
set -e

echo "=== Applying NVIDIA Fix to Zed Settings ==="

# Create backup
SETTINGS_FILE="/home/toxic/.config/zed/settings.json"
BACKUP_FILE="${SETTINGS_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "1. Creating backup: $BACKUP_FILE"
cp "$SETTINGS_FILE" "$BACKUP_FILE"

# Use jq to add NVIDIA provider
echo "2. Adding NVIDIA provider configuration"

# Read the patch
PATCH_FILE="/home/toxic/sovereign/nvidia_patch.json"

# Use jq to merge the patch into the language_models section
jq '.language_models += input' "$SETTINGS_FILE" "$PATCH_FILE" > "${SETTINGS_FILE}.tmp" && \
  mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"

echo "3. Verifying the changes"

# Check if NVIDIA was added
if jq -e '.language_models.nvidia' "$SETTINGS_FILE" > /dev/null; then
    echo "✓ NVIDIA provider successfully added"

    # Show what was added
    echo "✓ NVIDIA configuration:"
    jq '.language_models.nvidia' "$SETTINGS_FILE" | head -20
else
    echo "✗ Failed to add NVIDIA provider"
    exit 1
fi

echo ""
echo "=== Fix Applied Successfully ==="
echo "Backup created at: $BACKUP_FILE"
echo "Settings updated at: $SETTINGS_FILE"
echo ""
echo "Next steps:"
echo "1. Rebuild Zed: cd /home/toxic/projects/zed && cargo build --release"
echo "2. Restart Zed to use the new binary with NVIDIA support"
echo "3. Verify NVIDIA models appear in Zed's model selection"
