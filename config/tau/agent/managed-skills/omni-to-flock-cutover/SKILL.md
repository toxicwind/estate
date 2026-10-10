---
name: omni-to-flock-cutover
description: Procedure for cutting over tau agent configuration from obsolete OmniRoute to VansRouter/flock gateway system
---

# Omni→Flock Cutover Procedure

This procedure cuts over the tau agent configuration from the obsolete OmniRoute system (:20130) to the new VansRouter/flock gateway system (:20128).

## Prerequisites
- Verify flock gateway (:20128) is healthy and responding
- Have sudo/container management permissions (docker/podman)
- Backup current configuration if desired

## Steps

### 1. Verify Flock Gateway Health
```bash
# Test that :20128 is working (should get valid response, not auth error)
curl -s -m 5 http://127.0.0.1:20128/v1/models
```

### 2. Update Tau Agent Configuration
Edit `~/.tau/agent/config.yml`:
- Change `providers.omni.baseUrl` from `http://127.0.0.1:20130/v1` to `http://127.0.0.1:20128/v1`
- Change `extensions` list from `[pi-omniroute-sync, gwern]` to `[tau-flocksync, gwern]`

### 3. Remove Old Omniroute Extension Dependency
Edit `~/.tau/plugins/package.json`:
- Remove the line: `"pi-omniroute-sync": "^1.2.1"`

### 4. Quarantine Old Artifacts
```bash
# Create quarantine directory with timestamp
QUARANTINE_DIR="/home/toxic/archive/quarantine-omniroute-$(date +%Y%m%d)"
mkdir -p "$QUARANTINE_DIR"

# Move omniroute artifacts to quarantine
mv ~/.omniroute "$QUARANTINE_DIR/" 2>/dev/null || true
mv ~/.tau/agent/extensions/pi-omniroute-sync "$QUARANTINE_DIR/" 2>/dev/null || true
mv ~/.tau/plugins/node_modules/pi-omniroute-sync "$QUARANTINE_DIR/" 2>/dev/null || true
```

### 5. Stop Omniroute Container
```bash
# Stop the omniroute container (docker or podman)
docker stop omniroute-gateway 2>/dev/null || podman stop omniroute-gateway 2>/dev/null || true
```

### 6. Verify Cutover
```bash
# Check that config was updated correctly
grep -A2 "omni:" ~/.tau/agent/config.yml | grep baseUrl
# Should show: baseUrl: http://127.0.0.1:20128/v1

# Check extensions list
grep -A2 "extensions:" ~/.tau/agent/config.yml
# Should show: extensions: [tau-flocksync, gwern]

# Verify package.json fix
grep -c "pi-omniroute-sync" ~/.tau/plugins/package.json
# Should show: 0

# Test that flock gateway works with tau agent
# (This will happen automatically on next tau start)
```

## Verification Points
- ✅ omni provider baseUrl points to :20128 (flock gateway)
- ✅ extensions list contains tau-flocksync, not pi-omniroute-sync
- ✅ pi-omniroute-sync removed from package.json dependencies
- ✅ omniroute container stopped
- ✅ Artifacts quarantined for potential recovery
- ✅ Tau agent should now work without omniroute authentication errors

## Notes
- The flock gateway on :20128 does not require authentication for basic model listing/chat
- First tau start after cutover may trigger initial model sync via tau-flocksync
- Monitor ~/.tau/agent/models.json for updated model list from :20128/v1/models
- If needed, quarantined artifacts can be restored from the archive directory
