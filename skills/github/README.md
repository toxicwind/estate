![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/github?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/github?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/github?style=for-the-badge)

# github
Use Github when the user asks for Github or this provider's API

## What it does
Provides access to GitHub's REST API using the user-connected `custom.github` personal access token (PAT) credential, with dedicated CLI wrappers for common operations and secure credential handling.

## Why it matters
Enables safe, authenticated interactions with GitHub's API for repository management, issue handling, pull request operations, and other GitHub functionalities without exposing credentials or requiring manual token handling.

## Who it's for
Developers and AI agents who need to programmatically interact with GitHub's REST API for automation, integration, or workflow purposes while maintaining credential security.

## Features
- **PAT Authentication** - Uses user-connected `custom.github` credential (securely stored, never exposed)
- **Dedicated CLI Wrappers** - 
  - `gh.py` - Main GitHub CLI wrapper for standard operations
  - `git-push-ref.py` - Workaround for HTTPS push failures (blobs→tree→commit→ref via git-database API)
  - `mkref.py` - Create branch ref at known SHA via git-database API
- **Secure Auth Handling** - 
  - Credential already stored; nothing collects one
  - Never asks user to paste raw key, set env var, pass secret flag, or write auth file
  - 401/403 = question about request before credential validation
  - Verifies credential attachment; reconnects via `credentials.request_api_access` on rejection
- **API Restriction** - Limits authenticated requests to: api.github.com only
- **No Credential Logging** - Never prints, logs, or persists raw credentials
- **Surrogate Query Safety** - Python CLIs must use dynamic_credentials helpers for authenticated requests
- **JSON Response Handling** - Uses `read_json_response()` helper instead of direct `resp.read()` for urllib

## Quick Start
```bash
# Standard GitHub operations (issues, PRs, repos, etc.)
~/workspace/skills/github/bin/gh.py <standard-gh-command>

# Workaround for HTTPS push failures
~/workspace/skills/github/bin/git-push-ref.py <file-path> <branch> <commit-message>

# Create branch ref at known SHA
~/workspace/skills/github/bin/mkref.py <branch-name> <known-sha>
```

## Configuration
- **CLI Location**: `~/workspace/skills/github/bin/` (Python CLIs)
- **Auth Credential**: Stored as `custom.github` (PAT - Personal Access Token)
- **Required Imports** (for Python CLIs):
  - `/opt/hatch/skills/skill-creator/bin/dynamic_credentials.py`
  - Must call one of:
    - `add_surrogate_to_request(...)`
    - `url_with_surrogate_query_param(...)`
    - `url_with_surrogate_path_segment(...)`
  - If using urllib: must use `read_json_response(resp)` from same helper
  - Must send only `hsurr:*` values to api.github.com
- **Security Rules**:
  - Never print, log, or persist raw credentials
  - Restrict authenticated requests to api.github.com only
  - On 401/403: first verify credential was attached (request without helpers = wrong/under-scoped token)
  - Only after verifying credential-attached request is still rejected: call `credentials.request_api_access` with `reconnect`

## Development
Modify the Python CLI wrappers in `/home/toxic/estate/skills/github/bin/`:
- `gh.py` - Main GitHub CLI wrapper (standard operations)
- `git-push-ref.py` - HTTPS push workaround (git-database API)
- `mkref.py` - Branch ref creation at known SHA (git-database API)

All Python CLIs must properly import and use the dynamic credentials helpers for authenticated requests to api.github.com.

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Credential Protection** - Never exposes raw PAT; uses surrogate authentication flow
- **API Scope Limitation** - Restricts to api.github.com only prevents accidental data leakage
- **No Persistent Storage** - Doesn't log, print, or persist credentials in any form
- **Request Verification** - Checks for proper credential attachment before treating as credential issue
- **Safe Reconnection** - Uses established credential request flow for token renewal/recovery
- **Input Sanitization** - Requires specific helper usage for authenticated requests prevents bypass