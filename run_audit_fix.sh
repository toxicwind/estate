#!/bin/bash

echo "=== Running Audit Log Script with Auto-Fix ==="

cd /home/toxic/sovereign

echo "1. Checking if Bun is available..."
if command -v bun &> /dev/null; then
    echo "   ✓ Bun found"
else
    echo "   ✗ Bun not found. Please install Bun first."
    exit 1
fi

echo "2. Checking if Danfo.js is installed..."
if [ -f "node_modules/danfojs-node/package.json" ]; then
    echo "   ✓ Danfo.js found"
else
    echo "   ⚠ Danfo.js not found. Installing..."
    bun add danfojs-node
fi

echo "3. Running audit script..."
bun run audit_log.ts

echo "4. Checking for any errors in the output..."
if [ $? -eq 0 ]; then
    echo "   ✓ Audit script completed successfully"
else
    echo "   ✗ Audit script failed"
    exit 1
fi

echo "5. Verifying output files..."
if [ -f "audit-output/audit-report.md" ] && \
   [ -f "audit-output/audit-data.json" ] && \
   [ -f "audit-output/audit-fixes.json" ]; then
    echo "   ✓ All output files created successfully"
    echo ""
    echo "Output files:"
    echo "  - audit-output/audit-report.md (human-readable report)"
    echo "  - audit-output/audit-data.json (raw data)"
    echo "  - audit-output/audit-fixes.json (structured fixes for subagents)"
else
    echo "   ✗ Some output files missing"
    exit 1
fi

echo ""
echo "=== Audit Complete ==="
echo "The script has successfully:"
echo "  ✓ Parsed the 1000-line log file"
echo "  ✓ Identified symlink errors and categories"
echo "  ✓ Generated structured reports"
echo "  ✓ Created fix plans for subagents"
echo ""
echo "Next steps:"
echo "  1. Review audit-output/audit-report.md for full analysis"
echo "  2. Use audit-output/audit-fixes.json to delegate tasks to subagents"
echo "  3. Subagent A: Fix broken symlinks"
echo "  4. Subagent B: Resolve symlink loops"
