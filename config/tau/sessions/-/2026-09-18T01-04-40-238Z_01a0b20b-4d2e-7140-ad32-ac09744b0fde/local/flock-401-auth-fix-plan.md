# Flock 401 Authentication Fix Plan

## Context
The flock service is returning 401 Unauthorized errors. The issue appears to be related to key configuration or authentication. Need to investigate the key handling, API key configuration, and authentication logic in the flock codebase.

## Approach

### Step 1: Discover key configuration locations
- Search for API key, auth key, or credential configuration in the flock codebase
- Identify where keys are loaded, validated, and used for authentication
- Check for environment variables, config files, or hardcoded keys

### Step 2: Investigate the 401 error source
- Find where 401 errors are caught and handled
- Identify the authentication flow and where it fails
- Check for key validation logic and error messages

### Step 3: Fix the key configuration
- Update or correct the API key configuration
- Ensure the key is properly formatted and has the correct permissions
- Add proper error handling and logging for authentication failures

### Step 4: Verify the fix
- Test the flock service with the corrected key
- Confirm 401 errors are resolved
- Check for any related errors or warnings

## Critical Files & Anchors
- `/home/toxic/estate/projects/herd/internal/flock/` - main flock implementation
- `/home/toxic/estate/projects/herd/mesh/flock-pkg/sovereign_complete_pkg/flock-dist/lib/llm_client/llm_client.py` - LLM client with authentication
- `/home/toxic/estate/projects/herd/mesh/flock-pkg/sovereign_complete_pkg/flock-dist/lib/orchestrator/orchestrator.py` - orchestration logic
- `/home/toxic/estate/projects/herd/internal/flock/config.go` - configuration handling
- `/home/toxic/estate/projects/herd/internal/flock/providers.go` - provider authentication

## Verification
1. Run `ffs_find -pattern "key" -root /home/toxic/estate/projects/herd` to locate key configuration
2. Run `ffs_find -pattern "401" -root /home/toxic/estate/projects/herd` to find error handling
3. Read the identified configuration files to understand the current state
4. Apply the fix and test the flock service

## Assumptions & Contingencies
- The 401 error is caused by an incorrect or missing API key
- If the key is correct but authentication still fails, the issue may be in the authentication flow itself
- If no key configuration is found, the service may be using a default or hardcoded key that needs to be updated

If the key configuration is found but appears correct, investigate the authentication flow and error handling next.
If no key configuration is found, check for environment variables or external configuration sources.
