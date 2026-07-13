# Sovereign tree (production surface)

```
sovereign/
├── AGENTS.md                 # project rules (inherits ~/.grok)
├── TREE.md                   # this file
├── README.md
├── package.json / bun.lock   # Bun runtime
├── mise.toml + mise/tasks/   # lifecycle (up/down/health/test-llm)
├── process-compose.yaml      # GENERATED from stack/modules
├── Caddyfile / prometheus.yml
├── config/ports.env
├── bin/                      # thin operational scripts only
├── stack/
│   ├── modules/*.yaml        # process-compose process defs
│   └── services/*.sh         # entry shims → bun where possible
├── src/                      # ALL app TypeScript (Bun)
│   ├── mcp/llama_swap.ts     # MCP + CLI e2e
│   ├── deploy/               # Insiders / IDEs / OpenFang providers
│   ├── services/             # hf-downloader, openfang, …
│   └── landing/
├── tools/llama-swap/         # config.yaml + docs (binary ignored)
├── tests/
├── skills/
├── models -> ~/models        # GGUF runtime (not in git)
└── backup/                   # moved junk/history — NEVER stage
```

## Not in the live tree

Moved under `backup/clean_2026-07-11_prod/`:

| Was | Why |
|-----|-----|
| `rust_algo_web/`, `yote/`, `scratch/` | heavy / non-core |
| `tools/ollama-proxy-rs`, `tools/legacy` | legacy |
| most of `bin/llama-*` symlinks + ctx experiments | belong in builds, not repo |
| `.agents/teamwork_*`, config snaps | ephemeral |

## Commands

| Task | Does |
|------|------|
| `mise run up-core` | llama-swap + openfang + prometheus + rust-web + watchdog |
| `mise run up` | core + optional |
| `mise run health` | CORE vs OPT (exit 1 if core red) |
| `mise run test-llm` / `bun run test:llm` | e2e choices≥1 |
| `bun run deploy:ides` | wire IDEs → :25100 |

## LLM front door

Always `http://127.0.0.1:25100` (llama-swap). **Never vLLM.**

## Runtime split (optimized, no thrash)

| Layer | Runtime | Why |
|-------|---------|-----|
| Inference router | llama-swap (Go) | Already production; leave alone |
| Dashboard / watchdog | Rust `sovereign_web` | Hot long-lived process |
| MCP + IDE deploy + e2e | Bun `src/` | Fast glue; MCP SDK; not on token path |
| Lifecycle | bash `mise/tasks` | Thin; shebang `#!/usr/bin/env bash` |

## Agent shell note

`~/.zshrc` agent early-`return 0` only exits the **sourced** zshrc (minimal PATH). It does **not** complete your work script. False “complete” is almost always the harness **timeout → background**, not zsh. Prefer `bash --noprofile --norc` or scripts with bash shebangs for long git/mise work.
