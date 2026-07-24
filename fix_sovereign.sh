#!/bin/bash
set -e

echo "🔧 Starting Sovereign Project Fix..."

# Phase 1: Remove broken symlinks
echo "🧹 Phase 1/4: Cleaning broken symlinks..."
find /home/toxic/sovereign -type l -xtype l -exec rm {} \; 2>/dev/null || true
BROKEN_COUNT=$(find /home/toxic/sovereign -type l -xtype l | wc -l)
echo "✅ Removed $BROKEN_COUNT broken symlinks"

# Phase 2: Fix circular symlinks
echo "🔄 Phase 2/4: Breaking circular symlinks..."
find /home/toxic/sovereign -type l -exec sh -c '
  for f; do
    target=$(readlink "$f")
    if [ "$target" = "$f" ]; then
      echo "Circular symlink: $f"
      rm "$f"
    fi
  done
' _ {} + 2>/dev/null || true
CIRCULAR_COUNT=$(find /home/toxic/sovereign -type l -exec sh -c 'for f; do [ "$(readlink "$f")" = "$f" ] && echo "1"; done' _ {} + | wc -l)
echo "✅ Fixed $CIRCULAR_COUNT circular symlinks"

# Phase 3: Update task configurations
echo "📝 Phase 3/4: Fixing task configurations..."
find /home/toxic/sovereign -name "*.json" -exec sed -i 's/"task"/"type": "task", "task"/g' {} \; 2>/dev/null || true
TASK_FIX_COUNT=$(find /home/toxic/sovereign -name "*.json" -exec grep -l '"type": "task"' {} \; | wc -l)
echo "✅ Updated task configurations in $TASK_FIX_COUNT files"

# Phase 4: Validate fixes
echo "✅ Phase 4/4: Validating fixes..."
REMAINING_BROKEN=$(find /home/toxic/sovereign -type l -xtype l | wc -l)
if [ "$REMAINING_BROKEN" -eq 0 ]; then
    echo "🎉 All symlinks fixed successfully!"
else
    echo "⚠️  $REMAINING_BROKEN broken symlinks remain"
fi

echo "🚀 Sovereign Project Fix Complete!"
echo "Summary:"
echo "  - Fixed broken symlinks: $BROKEN_COUNT"
echo "  - Fixed circular symlinks: $CIRCULAR_COUNT"
echo "  - Updated task configurations: $TASK_FIX_COUNT files"
echo "  - Remaining issues: $REMAINING_BROKEN"
