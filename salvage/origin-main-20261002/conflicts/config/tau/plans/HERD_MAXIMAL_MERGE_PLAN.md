# Herd Maximal Merge Plan

## Context
Integrate upstream `sovereign-swap` and latest `llama-swap` features into `projects/herd` to create a unified, robust AI router backend that supports advanced MCP, tailcat peering, sqlite activity storage, capability compatibility checks, and concurrency limits without breaking existing herd configurations.

## Approach
1. **Dependency & Struct Alignment**:
   - Ensure `Config` and related structs in `projects/herd/internal/config/` include all fields required by newly merged packages (`GlobalConcurrencyLimit`, `Security`, `Tailcat`, etc.).
   - Verify `go.mod` and `go.sum` contain all required dependencies without version conflicts.
2. **Compilation & Build**:
   - Run `go build -o llama-swap .` inside `/home/toxic/estate/projects/herd`.
   - Fix any missing fields, package reference mismatches, or syntax errors.
3. **Service Integration**:
   - Update `/home/toxic/projects/llama-swap` symlink if needed to point to the unified `projects/herd` directory.
   - Restart the `sovereign/herd` daemon via Pitchfork and verify successful health check and chat completion proxying.

## Verification
- **Build Verification**: `go build -o llama-swap .` completes with zero errors/warnings.
- **Health Check**: `curl -s http://127.0.0.1:25100/health` returns `{"status":"ok"}` or equivalent healthy JSON.
- **Inference Verification**: A test API completion request to `http://127.0.0.1:25100/v1/chat/completions` successfully proxies and returns a valid response.

## Assumptions & Contingencies
- If compilation fails due to an undefined field in a newly merged package, stub or implement the required field in `internal/config` using safe defaults.
