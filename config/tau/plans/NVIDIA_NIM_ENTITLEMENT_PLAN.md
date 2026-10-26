# NVIDIA NIM Entitlement, Secretsmith Fix, and MCP Browser Configuration Plan

## Context
User needs to fix three things:
1. NVIDIA NIM entitlement issue causing 404 errors
2. Secretsmith CLI tool not working
3. MCP browser for headed operation

## Approach
Three steps:
1. Fix secretsmith setup
2. Verify NVIDIA forum post
3. Configure MCP browser for headed mode

### Step 1: Fix secretsmith
Create default collection.
Test store/retrieve.
Verify functionality.

### Step 2: Verify NVIDIA forum
Check post #379205.
User already checked via Firefox.
No action needed if handled.

### Step 3: Configure MCP browser
Check current config.
Set up persistent Chromium profile.
Test navigation and screenshots.

## Critical files & anchors
- /home/toxic/.local/bin/secretsmith
- /home/toxic/.tau/rhodochrosite.key
- /home/toxic/.tau/agent/config.yml
- xd://mcp__browserless_*

## Verification
After execution:
1. Secretsmith: collections show default
2. Secretsmith: store/retrieve test secret works
3. MCP browser: persistent status shows Chromium alive
4. NVIDIA: forum post verified

## Assumptions & contingencies
- If secretsmith fails: try --bus $DBUS_SESSION_BUS_ADDRESS
- If MCP browser persistent fails: use ephemeral sessions
- If forum shows no solution: wait for NVIDIA admin or use OpenRouter NVIDIA models