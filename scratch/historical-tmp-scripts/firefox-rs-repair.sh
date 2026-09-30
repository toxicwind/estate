#!/usr/bin/env bash
# firefox-rs-repair.sh — Audit and repair Firefox Remote Settings dummy URL override
#
# The Mozilla test fixture URL `data:,#remote-settings-dummy/v1` in
# `services.settings.server` breaks ALL Remote Settings syncs (Nimbus, etc.)
# with broad `get-exception` errors. This script finds and removes it.
#
# Idempotent: safe to run multiple times. Creates timestamped backups.
# Must run as the user who owns the Firefox profile (not root).
#
# Usage: firefox-rs-repair.sh [--audit-only]

set -euo pipefail

AUDIT_ONLY=false
[[ "${1:-}" == "--audit-only" ]] && AUDIT_ONLY=true

DUMMY_URL="remote-settings-dummy"
BACKUP_DIR="/tmp/firefox-prefs-backup"
FOUND=0
FIXED=0

echo "=== Firefox Remote Settings Dummy URL Audit ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Find all Firefox profiles
for prefs in "$HOME"/.mozilla/firefox/*.default*/prefs.js; do
    [[ -f "$prefs" ]] || continue
    profile=$(dirname "$prefs" | xargs basename)
    echo "Checking profile: $profile"

    if grep -q "$DUMMY_URL" "$prefs" 2>/dev/null; then
        echo "  ⚠️  FOUND dummy URL in $prefs"
        FOUND=$((FOUND + 1))

        if [[ "$AUDIT_ONLY" == false ]]; then
            # Check if Firefox is running with this profile
            if pgrep -f "firefox.*$profile" >/dev/null 2>&1; then
                echo "  ⚠️  Firefox is running with this profile — cannot safely edit prefs.js"
                echo "  Close Firefox first, then re-run."
                continue
            fi

            # Backup
            mkdir -p "$BACKUP_DIR"
            backup="$BACKUP_DIR/prefs.js.bak-$(date +%Y%m%d-%H%M%S)"
            cp "$prefs" "$backup"
            echo "  Backed up to: $backup"

            # Remove the dummy URL line and blank normandy URL
            grep -v "$DUMMY_URL" "$prefs" | grep -v 'app.normandy.api_url", ""' > "$prefs.tmp"
            mv "$prefs.tmp" "$prefs"
            echo "  ✅ Removed dummy URL override"
            FIXED=$((FIXED + 1))
        fi
    else
        echo "  ✅ Clean (no dummy URL)"
    fi
done

echo ""
echo "=== Enterprise Policy Check ==="
POLICY_FILE="/etc/firefox/policies/policies.json"
if [[ -f "$POLICY_FILE" ]]; then
    echo "Policy file exists: $POLICY_FILE"
    # Validate JSON
    if python3 -c "import json; json.load(open('$POLICY_FILE'))" 2>/dev/null; then
        echo "  ✅ Valid JSON"
    else
        echo "  ❌ Invalid JSON!"
    fi
    # Check for known-invalid preference policies
    if grep -q "app.normandy.api_url\|app.shield.optoutstudies.enabled\|services.settings.server" "$POLICY_FILE" 2>/dev/null; then
        echo "  ⚠️  WARNING: Policy contains preferences rejected by Firefox for stability reasons."
        echo "  These must be removed — use Preferences policy only for allowed prefs,"
        echo "  or manage via prefs.js/user.js instead."
    else
        echo "  ✅ No invalid preference policies"
    fi
else
    echo "No policy file at $POLICY_FILE (this is fine)"
fi

echo ""
echo "=== Summary ==="
echo "Profiles with dummy URL: $FOUND"
[[ "$AUDIT_ONLY" == false ]] && echo "Profiles fixed: $FIXED"
echo ""
if [[ $FOUND -eq 0 ]]; then
    echo "✅ All clear — no dummy Remote Settings URLs found."
else
    if [[ "$AUDIT_ONLY" == true ]]; then
        echo "Run without --audit-only to fix (Firefox must be closed)."
    fi
fi
