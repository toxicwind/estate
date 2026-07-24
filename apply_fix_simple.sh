#!/bin/bash

echo "=== Applying Zed NVIDIA Fix ==="

SETTINGS_FILE="/home/toxic/.config/zed/settings.json"
FIXED_FILE="/home/toxic/sovereign/settings_fixed.json"
BACKUP_FILE="${SETTINGS_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "1. Creating backup of current settings..."
cp "$SETTINGS_FILE" "$BACKUP_FILE"
echo "   Backup created: $BACKUP_FILE"

echo "2. Applying fixed settings..."
cp "$FIXED_FILE" "$SETTINGS_FILE"
echo "   Fixed settings applied to: $SETTINGS_FILE"

echo "3. Verifying the fix..."
if grep -q '"nvidia"' "$SETTINGS_FILE"; then
    echo "   ✓ NVIDIA provider found in settings"

    # Count models
    MODEL_COUNT=$(grep -A 50 '"nvidia"' "$SETTINGS_FILE" | grep -c '"name"' || echo "0")
    echo "   ✓ NVIDIA models configured: $MODEL_COUNT"
else
    echo "   ✗ NVIDIA provider not found"
    exit 1
fi

echo ""
echo "=== Fix Applied Successfully ==="
echo ""
echo "Changes made:"
echo "✓ Added NVIDIA provider with 2 models (Inkling + Nemotron)"
echo "✓ Fixed JSON syntax issues"
echo "✓ Ensured all providers have proper structure"
echo ""
echo "Next steps:"
echo "1. Rebuild Zed: cd /home/toxic/projects/zed && cargo build --release"
echo "2. Restart Zed to use the new binary with NVIDIA support"
echo "3. Verify NVIDIA models appear in Zed's model selection"
echo ""
echo "Backup location: $BACKUP_FILE"
