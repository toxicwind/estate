# Sovereign tree

```
sovereign/
├── AGENTS.md                 # project rules (inherits ~/.grok)
├── README.md                 # this file
├── TREE.md                   # this file
├── mise.toml + mise/tasks/   # lifecycle (up/down/health/test-llm)
├── process-compose.yaml      # GENERATED from stack/modules
├── package.json / bun.lock   # Bun runtime
├── .env.local                # ports, paths, flags
├── .gitignore
├── Caddyfile                 # optional edge (not in pc profile)
├── prometheus.yml
│
├── stack/
│   ├── modules/*.yaml        # process-compose process defs
│   │   ├── llama-swap.yaml
│   │   ├── null-g-proxy.yaml
│   │   ├── openfang.yaml
│   │   ├── prometheus.yaml
│   │   ├── rust-web.yaml
│   │   ├── yote.yaml
│   │   └── hf-downloader.yaml
│   ├── services/*.sh         # entry shims
│   ├── base.yaml             # version + strict settings
│   ├── build-compose.sh      # modules → process-compose.yaml
│   ├── profiles.sh           # core / sovereign / full
│   ├── lib.sh                # shared helpers
│   ├── up.sh / down.sh / health.sh
│   └── ports.env
│
├── src/                      # ALL app TypeScript (Bun — primary)
│   ├── mcp/llama_swap.ts     # MCP server + CLI e2e
│   ├── deploy/               # Insiders / IDEs / OpenFang providers
│   └── services/             # hf-downloader, openfang, null-g-proxy
│
├── rust_algo_web/            # Rust hot-path web + watchdog
│   ├── src/main.rs
│   ├── src/watchdog.rs
│   ├── Cargo.toml
│   └── static/
│
├── tools/llama-swap/         # config.yaml only (binary in bin/)
│
├── bin/                      # binary artifacts only
│   ├── llama-swap            # ELF (Go)
│   ├── sovereign_web         # ELF (Rust)
│   ├── llama-gguf-hash       # utility wrapper
│   └── llama-gguf-hash-run   # utility wrapper
│
├── tests/
├── skills/
├── projects/                 # experimental sub-projects
├── models -> ~/models        # GGUF runtime (not in git)
└── backup/                   # moved junk — NEVER stage
```
