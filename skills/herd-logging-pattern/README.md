# herd-logging-pattern

[![for-the-badge](https://img.shields.io/badge/Go-slog-00ADD8?style=for-the-badge)](https://go.dev/libslog) [![for-the-badge](https://img.shields.io/badge/Rust-tracing-02346E?style=for-the-badge)](https://docs.rs/tracing) [![for-the-badge](https://img.shields.io/badge/JSON-Output-EDBC2F?style=for-the-badge)](https://json.org)

## herd-logging-pattern

Gold-standard logging pattern from herd (`toxicwind/herd`). Use this when any service needs "awesome logs" — structured, searchable, per-source isolated, live-streamable.

### The Three Layers

#### 1. Structured Application Logs

**Go** (`log/slog`):
```go
slog.Info("model loaded", "model", name, "size", sizeBytes, "duration_ms", elapsed)
slog.Error("failed to load config", "config", path, "error", err)
```

**Rust** (`tracing`):
```rust
tracing::info!(agent = %name, id = %agent_id, "Spawning agent");
```

**Rules:**
- Key-value pairs, NEVER format strings for structured data
- Include correlation IDs (`request_id`, `agent_id`) on every log in a request/agent context
- Use `%` (Display) not `?` (Debug) for human-readable field values

#### 2. Per-Source Log Monitors

Don't mix all logs into one stream. Isolate by source:

- **Herd**: proxy logs | upstream logs | combined (mux) logs
- **OpenFang**: per-agent logs | API logs | system logs

Each monitor gets:
- Circular buffer history (O(1) writes, bounded memory)
- Independent log level
- Event subscribers for live tailing

**Go implementation**: `internal/logmon/` — `Monitor` with `NewWriter()`, `SetLogLevel()`, `GetHistory()`

#### 3. HTTP Log Endpoints

Expose logs programmatically:

```
GET /logs                    — historical logs (all sources or filtered)
GET /logs/stream             — SSE live tail (combined)
GET /logs/stream/{source}    — SSE live tail (per-source)
```

**Query params**: `?level=debug&since=2026-09-30T00:00:00Z&source=proxy`

### JSON Output (Machine-Parseable)

Human-readable is the default. JSON is opt-in via env var:

**Rust**:
```rust
if std::env::var("APP_LOG_JSON").map(|v| v == "1").unwrap_or(false) {
    tracing_subscriber::fmt().json()...
} else {
    tracing_subscriber::fmt()...
}
```

**Go**:
```go
if os.Getenv("APP_LOG_JSON") == "1" {
    slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stderr, nil)))
} else {
    slog.SetDefault(slog.New(slog.TextHandler(os.Stderr, nil)))
}
```

**With JSON, filtering becomes**:
```bash
# All logs for one agent
logs | jq 'select(.fields.agent == "coyote")'

# Errors in the last hour
logs | jq 'select(.level == "ERROR" and .timestamp > "2026-09-30T00:00:00Z")'

# Correlate by request
logs | jq 'select(.fields.request_id == "abc-123")'
```

### Config-Driven Levels

```yaml
# config.yaml
logLevel: info        # debug | info | warn | error
logToStdout: both     # none | proxy | upstream | both (herd-specific)
logTimeFormat: rfc3339
```

**Rust**: `RUST_LOG=debug,openfang_kernel=trace`

### Checklist for "Awesome Logs"

- [ ] Structured key-value (not format strings)
- [ ] Correlation IDs on every contextual log
- [ ] JSON output option (env var, default off for compat)
- [ ] Per-source isolation (not one mixed stream)
- [ ] HTTP endpoints for history + live tail
- [ ] Configurable levels without restart (or with fast restart)
- [ ] Circular buffer (bounded memory, no log rotation hell)

### Anti-Patterns

- ❌ `log.Printf("agent %s did %s", name, action)` — use fields
- ❌ Single log file for everything — isolate by source
- ❌ No correlation IDs — can't trace a request across services
- ❌ JSON always on — breaks human tailing; make it opt-in
- ❌ Unbounded log buffers — use circular buffers

### Quick start

```bash
# Start the log service with structured logging
# Go example
go run ./...

# Or with JSON output enabled
APP_LOG_JSON=1 go run ./...

# Query the HTTP endpoints
curl http://127.0.0.1:25100/logs?level=error
curl http://127.0.0.1:25100/logs/stream
curl http://127.0.0.1:25100/logs/stream/proxy
```

### License

Open Claw — see `skill.toml` for details.

### Security

- JSON output is opt-in via env var, default off for human compatibility
- Per-source isolation prevents credential leakage across service boundaries
- Correlation IDs enable end-to-end request tracing without inspecting payload values