# Sovereign Ecosystem — Deep Fork & Repository Audit

## Executive Summary
This document provides a comprehensive structural audit of all 14 custom forks across `/home/toxic/projects/` and `/home/toxic/sovereign`. Each fork's upstream origin, custom architectural additions, build toolchains, and inter-dependencies are documented to prevent configuration drift and regression.

---

## Fork Matrix & Roles

| Fork ID | Path | Upstream Origin | Build Toolchain | Key Custom Additions |
|---|---|---|---|---|
| **`pi-agent`** | `/home/toxic/projects/pi-agent` | `toxicwind/pi` | Bun / TS + Rust | 1M context routing, CWD-aware launchers, unified RPC builder, full native/MCP tool integration, local SQLite state. |
| **`llama-swap`** | `/home/toxic/projects/llama-swap` | `mostlygeek/llama-swap` | Go (1.24+) | Go AST Matrix router (`internal/astmatrix/`), LIFO macro resolution, `normalize_sse` streaming adapter, `fuser -k` stale port cleanup, IPv4 defaults. |
| **`mcpproxy-go`** | `/home/toxic/projects/mcpproxy-go` | `smart-mcp-proxy` | Go | 231 tools federated across 18 MCP servers, Bleve search index, offline TPA scanner, zero-quarantine auto-approval. |
| **`ghas`** | `/home/toxic/projects/github-advanced-search-mcp` | `toxicwind/github-advanced-search-mcp` | Bun / TS | Dual-engine search (Blackbird web index + classic REST), Firefox profile session auth, high-recall intent router (`apps/api`, `apps/mcp`, `apps/frontend`). |
| **`beellama`** | `/home/toxic/projects/beellama.cpp` | `ggerganov/llama.cpp` | C++ (CMake/CUDA) | DFlash speculative decoding (3.5-4.4x speedup on RTX 3090), MTP head support, `--kv-unified`. |
| **`ik_llama`** | `/home/toxic/projects/ik_llama.cpp-main` | `ikawrakow/ik_llama.cpp` | C++ (CMake/CUDA) | Extreme quantization kernels (IQ4_XS, Q5_K_XL), Heretic 27B long-context offload. |
| **`turboquant`** | `/home/toxic/projects/llama-cpp-turboquant` | `llama.cpp` | C++ (CMake/CUDA) | TurboQuant 3-bit / 4-bit KV Cache compression (`turbo2`, `turbo3`), fused dequantization flash attention. |
| **`kimi-code`** | `/home/toxic/projects/kimi-code-sovereign` | `MoonshotAI/kimi-code` | Bun / TS / Vue | Multi-kernel agent runtime, tree-sitter bash service, structured OAuth usage, modern Web UI. |
| **`antigravity-gw`** | `/home/toxic/projects/antigravity-gateway-master` | `toxicwind/antigravity-gateway` | Next.js / TS | Single-port Next.js + API + WebSocket gateway on `:25128`, active server discovery. |
| **`zedra`** | `/home/toxic/projects/zedra-tanlethanh` | `tanlethanh/zedra` | Rust (Cargo) | Mobile & remote Zed agent host (`zedra-host` on `:25130`), GPUI bindings. |
| **`sovereign`** | `/home/toxic/sovereign` | `toxicwind/sovereign` | Bun / TS | Master control plane: ports SSOT (`config/ports.env`), `pitchfork.toml` / `mise.toml` generation, stack orchestration (`core`, `main`, `agents`, `search`, `mcp`, `monitoring`, `all`). |
| **`caddy-auth`** | `/home/toxic/projects/caddy-sovereign-auth` | `caddyserver/caddy` | Go | Tailscale identity extraction and API key auth middleware. |
| **`greprip`** | `/home/toxic/projects/greprip` | `toxicwind/greprip` | Python / Rust | Fast ERE/BRE pattern translation with SIGPIPE suppression. |
| **`process-compose`** | `/home/toxic/projects/process-compose` | `F1bonacc1/process-compose` | Go | TUI supervisor with MCP SSE security origin filtering and cross-namespace dependency pruning. |

---

## Inter-Dependency & Data Flow

```
                                [Sovereign Control Plane]
                                (/home/toxic/sovereign)
                                           │
          ┌────────────────────────────────┼────────────────────────────────┐
          ▼                                ▼                                ▼
  [Model Inference]                [Tool Federation]               [Search & Memory]
  llama-swap (:25100)              mcpproxy-go (:25127)             ghas-api (:25112)
    ├── beellama.cpp (DFlash)        ├── desktop-commander (stdio)  ghas-mcp (:25113)
    ├── ik_llama.cpp (Heretic)       ├── smarter-ast-mcp (stdio)    qdrant (:25133)
    └── turboquant (3-bit KV)        ├── codebase-memory (stdio)    redis (:25199)
                                     └── arxiv-mcp (stdio)
                                           │
                                           ▼
                                [Agent Client Runtimes]
                                  ├── pi-agent (CLI/TUI)
                                  ├── kimi-code (:25126)
                                  └── antigravity-gw (:25128)
```

---

## Stash & Worktree Status

1. **`github-advanced-search-mcp`**: Stash merged and committed (`feat(ghas): merge stash updates`). Conflict resolution verified with 20/20 test passes.
2. **`llama-swap`**: Macro hardening committed (`fix(config): harden Env slice macro validation`). All `internal/config/` and `internal/astmatrix/` tests pass.
3. **`pi-agent`**: Verified 1M context models, unlocked advisor tool permissions, dynamic launcher in `/home/toxic/.local/bin/pi`.
