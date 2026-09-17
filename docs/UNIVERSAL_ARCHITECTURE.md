# Universal Architecture — Polyglot Sovereign Stack (August 2026)

**Status**: Living document. Applies to all code under `/home/toxic/sovereign/`, `/home/toxic/projects/pi-agent/`, `/home/toxic/.pi/agent/`.

---

## 1. Language Roles & Boundaries

| Language | Runtime | Domain | Interop Mechanism |
|----------|---------|--------|-------------------|
| **TypeScript (Bun)** | Bun v1.3+ | API layer, orchestration, tooling, MCP servers, agent logic | Native `bun:ffi`, `child_process`, HTTP/Unix sockets |
| **Go** | Go 1.23+ | High-throughput proxies, rate limiters, egress managers, data plane | gRPC, HTTP/2, Unix sockets, shared memory |
| **Rust** | Rust nightly | SIMD/GPU kernels, crypto, parsers, WASM modules, hot paths | `bun:ffi` (C ABI), `wasm32-wasip1`, CLI binaries |

**Rule**: No language crosses its domain boundary without explicit interface contract (protobuf/JSON Schema/Zod).

---

## 2. Polyglot Integration Patterns (August 2026)

### 2.1 Bun ↔ Go (Primary Data Plane)

```typescript
// TypeScript: spawn Go binary with structured JSON over stdin/stdout
// Use for: llama-swap, astmatrix, sovereign-router
import { $ } from "bun";

const result = await $`/home/toxic/bin/llama-swap --json`.json();
```

```go
// Go: read JSON from stdin, write JSON to stdout
// No HTTP overhead for local data plane
func main() {
    dec := json.NewDecoder(os.Stdin)
    enc := json.NewEncoder(os.Stdout)
    for {
        var req Request
        if err := dec.Decode(&req); err != nil { return }
        resp := process(req)
        enc.Encode(resp)
    }
}
```

**Transport**: `bun:ffi` for hot paths (sub-ms), stdio JSON for control plane.

### 2.2 Bun ↔ Rust (Hot Path / SIMD)

```typescript
// TypeScript: load Rust WASM or native dylib via bun:ffi
import { dlopen, FFIType, suffix } from "bun:ffi";

const lib = dlopen(`libtokenizer.${suffix}`, {
  encode: { args: [FFIType.ptr, FFIType.i32], returns: FFIType.ptr },
  decode: { args: [FFIType.ptr], returns: FFIType.ptr },
});
```

```rust
// Rust: #[no_mangle] extern "C" functions
#[no_mangle]
pub extern "C" fn encode(ptr: *const u8, len: i32) -> *mut u8 { ... }
```

**Compile**: `cargo build --release --target x86_64-unknown-linux-gnu` (or `-musl` for static).

### 2.3 Shared Memory / Zero-Copy (High-Throughput)

- **Ring buffers**: `mmap` shared memory between Go/Rust/Bun
- **Cap'n Proto / FlatBuffers**: zero-copy serialization
- **io_uring**: Go/Rust async I/O, Bun via `bun:ffi` binding

---

## 3. Project Structure (Monorepo)

```
/home/toxic/sovereign/
├── config/                 # TOML configs (ports.env, mise.toml, pitchfork.toml)
├── src/
│   ├── go/                 # Go services (llama-swap, astmatrix, router)
│   │   ├── cmd/            # Main packages
│   │   ├── internal/       # Private packages
│   │   └── go.mod
│   ├── rust/               # Rust crates (tokenizers, crypto, SIMD)
│   │   ├── crates/
│   │   └── Cargo.toml
│   ├── ts/                 # TypeScript packages (Bun workspace)
│   │   ├── packages/
│   │   │   ├── ai/         # @earendil-works/pi-ai
│   │   │   ├── agent/      # @earendil-works/pi-agent
│   │   │   ├── coding-agent/
│   │   │   └── ...
│   │   ├── package.json    # Bun workspace root
│   │   └── bun.lock
│   └── polyglot/           # Cross-language interfaces
│       ├── proto/          # Protobuf definitions
│       ├── schemas/        # JSON Schemas / Zod
│       └── ffi/            # C headers for FFI
├── bin/                    # Built binaries (go build, cargo build, bun build)
├── scripts/                # Build/orchestration scripts (Bun)
└── tests/                  # Integration tests (multi-language)
```

---

## 4. Build System (Mise + Bun)

```toml
# mise.toml
[tools]
bun = "1.3.14"
go = "1.23.1"
rust = "nightly"

[tasks]
# Polyglot build
"build:all" = "mise run build:go && mise run build:rust && mise run build:ts"
"build:go" = "cd src/go && go build -o ../../bin ./cmd/..."
"build:rust" = "cd src/rust && cargo build --release --workspace"
"build:ts" = "cd src/ts && bun run build"

# Dev loop
"dev:go" = "cd src/go && air -c .air.toml"
"dev:rust" = "cd src/rust && cargo watch -x 'build --workspace'"
"dev:ts" = "cd src/ts && bun --hot run dev"

# Test
"test:integration" = "bun test:integration"
```

```json
// src/ts/package.json (Bun workspace)
{
  "name": "@sovereign/ts",
  "private": true,
  "workspaces": ["packages/*"],
  "scripts": {
    "build": "bun run build:packages",
    "build:packages": "for p in packages/*; do (cd $p && bun run build); done",
    "typecheck": "tsgo --noEmit"
  }
}
```

---

## 5. Configuration: Single Source of Truth

| File | Purpose |
|------|---------|
| `config/ports.env` | **All ports (25xxx)** — never hardcode |
| `config/mise.toml` | Tool versions, tasks, env |
| `config/pitchfork.toml` | Daemon definitions |
| `src/go/config/*.yaml` | Go service configs (loaded at startup) |
| `src/rust/config/*.toml` | Rust crate configs |
| `src/ts/packages/*/package.json` | TS package configs |

**Loading order** (all languages):
1. `config/ports.env` → env vars
2. Language-specific config files
3. CLI flags (override)

---

## 6. Observability Contract

Every service (Go/Rust/TS) exposes:

```yaml
# Standard endpoints
/health          # Liveness (returns 200 OK)
/ready           # Readiness (checks deps)
/metrics         # Prometheus metrics
/debug/pprof     # pprof (Go/Rust only)
```

**Metrics naming**: `sovereign_<service>_<operation>_<unit>`
- `sovereign_llama_swap_requests_total`
- `sovereign_astmatrix_latency_seconds`
- `sovereign_mcp_tool_calls_total`

---

## 7. Error Handling: Fail Loud

| Language | Pattern |
|----------|---------|
| **TypeScript** | `throw new SovereignError(code, message, cause)` — never catch silently |
| **Go** | `return fmt.Errorf("context: %w", err)` — wrap, don't discard |
| **Rust** | `anyhow::Result<T>` with `context()` — propagate with context |

**Rule**: No `2>/dev/null`, no `|| true`, no empty catch blocks.

---

## 8. Testing Strategy

| Level | Tool | Scope |
|-------|------|-------|
| **Unit (TS)** | `bun test` / `vitest` | Single package, mocked deps |
| **Unit (Go)** | `go test ./...` | Single package |
| **Unit (Rust)** | `cargo test` | Single crate |
| **Integration** | `bun test:integration` | Cross-language, real services |
| **Contract** | `pact` / custom | Protobuf/JSON Schema compliance |
| **E2E** | `./test.sh` | Full stack, real providers |

**Integration test pattern**:
```typescript
// Spawn real Go/Rust binaries, test via stdio/HTTP
const proc = await $`../../bin/llama-swap --stdio`.quiet();
const result = await proc.stdin.write(JSON.stringify({model: "free", messages: [...]}));
// Verify JSON response
```

---

## 9. Dependency Management

| Language | Lockfile | Update Policy |
|----------|----------|---------------|
| **TypeScript** | `bun.lock` | `bun update` (explicit), `npm install --ignore-scripts` |
| **Go** | `go.sum` | `go get -u` (explicit), vendoring for releases |
| **Rust** | `Cargo.lock` | `cargo update` (explicit), `cargo deny check` |

**Security**: `cargo deny check`, `npm audit`, `govulncheck` in CI.

---

## 10. Release & Deployment

| Artifact | Build | Deploy |
|----------|-------|--------|
| **Go binaries** | `go build -ldflags="-s -w"` | `bin/` → systemd/pitchfork |
| **Rust binaries** | `cargo build --release --target x86_64-unknown-linux-musl` | `bin/` |
| **TypeScript** | `bun build --compile --target=bun-linux-x64` | `bin/` or `npm pack` |
| **WASM modules** | `cargo build --target wasm32-wasip1` | `src/ts/packages/*/wasm/` |

**Versioning**: Single version across all languages (lockstep). Tag: `vX.Y.Z`.

---

## 11. AGENTS.md Compliance Checklist

| Rule | Implementation |
|------|----------------|
| **Verify live** | `/health` + `curl` in all tasks |
| **Fail loud** | No silent errors, structured error types |
| **Multi-strategy** | 3+ impls for non-trivial (e.g., router: Go/TS/Rust) |
| **TDD/BDD** | Failing test first, `tsgo --noEmit`, `go test`, `cargo test` |
| **Emergence tools** | GHAS → ast-grep → Tombi |
| **call_tool_destructive** | Write/edit = destructive, read = inspection |
| **CUDA-aware** | `nvidia-smi` validation in Go/Rust services |
| **No head truncation** | Full file reads, streaming for large outputs |
| **Port SSOT** | `config/ports.env` only source |

---

## 12. Quick Reference: Adding a New Polyglot Service

1. **Define contract** in `src/polyglot/proto/<service>.proto` + JSON Schema
2. **Implement Go** in `src/go/cmd/<service>/main.go` (data plane)
3. **Implement Rust** in `src/rust/crates/<service>-core/` (hot paths)
4. **Implement TS** in `src/ts/packages/<service>/` (orchestration)
5. **Add build tasks** to `mise.toml`
6. **Add health/metrics** endpoints
7. **Write integration test** in `tests/integration/<service>.test.ts`
8. **Update CHANGELOG** in each language's package

---

**Last Updated**: 2026-08-08  
**Maintainer**: toxic (`toxicwind@gmail.com`)