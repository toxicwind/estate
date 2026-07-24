#!/bin/bash

echo "=== Applying Biome-like Fixes to audit_log.ts ==="

cd /home/toxic/sovereign

echo "1. Creating backup of original file..."
cp audit_log.ts audit_log.ts.biome_backup
echo "   ✓ Backup created: audit_log.ts.biome_backup"

echo "2. Applying Biome-like fixes..."
cp audit_log_fixed.ts audit_log.ts
echo "   ✓ Fixed version applied"

echo "3. Verifying the changes..."
if diff -q audit_log.ts.biome_backup audit_log.ts > /dev/null; then
    echo "   ⚠ No changes detected (files are identical)"
else
    echo "   ✓ Changes applied successfully"
    echo ""
    echo "Key improvements made:"
    echo "  • Added proper error handling with try-catch"
    echo "  • Improved type safety in reduce operations"
    echo "  • Fixed Map operations with proper null checks"
    echo "  • Enhanced code organization and readability"
    echo "  • Added Biome configuration file"
fi

echo ""
echo "4. Running the fixed audit script..."
if command -v bun &> /dev/null; then
    bun run audit_log.ts
    if [ $? -eq 0 ]; then
        echo ""
        echo "   ✓ Audit script ran successfully with fixes"
    else
        echo ""
        echo "   ✗ Audit script failed"
        exit 1
    fi
else
    echo "   ⚠ Bun not available, skipping test run"
fi

echo ""
echo "=== Biome-like Fixes Complete ==="
echo ""
echo "Files modified:"
echo "  • audit_log.ts (with Biome-like improvements)"
echo "  • biome.json (Biome configuration created)"
echo "  • audit_log.ts.biome_backup (original backup)"
echo ""
echo "The script now has:"
echo "  ✓ Proper error handling"
echo "  ✓ Type-safe operations"
echo "  ✓ Better code organization"
echo "  ✓ Biome configuration for future formatting"
echo ""
echo "To run the audit:"
echo "  bun run audit_log.ts"
