# Bornite Maximal Merge Plan

## Context
Integrate upstream `estate-swap` and latest `bornite` features into `projects/bornite` to create a unified, robust AI router backend that supports advanced MCP, tailcat peering, sqlite activity storage, capability compatibility checks, and concurrency limits without breaking existing bornite configurations.

## Approach
1. **Dependency & Struct Alignment**:
   - Ensure `Config` and related structs in `projects/bornite/internal/config/` include all fields required by newly merged packages (`GlobalConcurrencyLimit`, `Security`, `Tailcat`, etc.).
   - Verify `go.mod` and `go.sum` contain all required dependencies without version conflicts.
2. **Compilation & Build**:
   - Run `go build -o bornite .` inside `/home/toxic/pens/estate/ranch/bornite`.
   - Fix any missing fields, package reference mismatches, or syntax errors.
3. **Service Integration**:
   - Update `/home/toxic/projects/bornite` symlink if needed to point to the unified `projects/bornite` directory.
   - Restart the `estate/bornite` daemon via Pitchfork and verify successful health check and chat completion proxying.

## Verification
- **Build Verification**: `go build -o bornite .` completes with zero errors/warnings.
- **Health Check**: `curl -s http://127.0.0.1:25100/health` returns `{"status":"ok"}` or equivalent healthy JSON.
- **Inference Verification**: A test API completion request to `http://127.0.0.1:25100/v1/chat/completions` successfully proxies and returns a valid response.

## Assumptions & Contingencies
- If compilation fails due to an undefined field in a newly merged package, stub or implement the required field in `internal/config` using safe defaults.
