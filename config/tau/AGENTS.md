# AGENTS.md — .tau Sovereign Architecture Source of Truth
# Source: .local/bin/agent -> .local/bin/tau -> /home/toxic/estate/agent
#   (cli framework: projects/sovereign-projects/tau/packages/coding-agent/src/cli.ts)
#   invoked by: bash via /home/toxic/estate/agent (shebang: #!/usr/bin/env bash)
#   bun path: /home/toxic/.bun/bin/bun
#   config: PI_CONFIG_DIR=$HOME/.tau, PI_CODING_AGENT_DIR=$HOME/.tau/agent
#   single default profile, no toxic
# References: debate.md (449l; line refs 195/218/241/44/54/59/332/36/401/33/315); SYNTHESIS.md; verify_report.md (PASS); fill_confirm.md (PASS); computer-use.json (first-class); no-echo-ban.md (toxic-persona MANDATORY #2)
#
# SOVEREIGN REPO: /home/toxic/estate (first-class operational repo)
# - AGENTS.md: /home/toxic/.tau/AGENTS.md → /home/toxic/estate/AGENTS.md (symlink, full docs)
# - helpers/: Bun/TS operational helpers (git-mutator, health-audit, mesh-probe, safe-rg-audit, ast-migrate, hardware-telemetry.sh, clean-orphans.sh)
# - packages/sovereign-utils: Shared sovereign utilities and ecosystem helpers
# - projects/range/ranch: Ranch system (supersedes legacy mesh)
# - config/ports.env: Port SSOT for all 25xxx services
# - mise.toml / pitchfork.toml: Service orchestration
# - src/: hal-substrate, openfang, services, mcp, deploy
# - tools/: llama-swap, nuvio-webos, sovereign-router, etc.
#
# KEY COMMANDS:
#   bun /home/toxic/estate/helpers/git-mutator.ts status|commit-push|scan-secrets
#   bun /home/toxic/estate/helpers/health-audit.ts
#   mise -C /home/toxic/estate run health|status|up|down

## 🏗️ Build Server (NativeLink - :25155/:25157 & mbx-cache - :25148)
- **Primary Build Server**: NativeLink running on port `25155` (frontend) and `25157` (worker) via Pitchfork (`pitchfork.d/nativelink.toml`), providing Remote Execution API (REAPI) caching and execution. Supersedes legacy `buildsrv`.
- **Task Cache**: `mbx-cache` running on port `25148` via Pitchfork (`vendored/mr-boxington-cache`), wired as mise's remote task cache (`task.cache.remote_url`).
- **Worker & Cache Architecture**:
  - REAPI CAS and Action Cache hierarchies at `var/runtime/nativelink/`.
  - NVMe-backed shared compiler/package caches: `sccache` (Rust/C++), `ccache`, and `uv` (Python wheels/environments).
## 🛡️ Anti-Hallucination & Execution Rules
- **Tool Execution Proof**: NEVER fake completion declarations or fire consecutive todo done calls without tool execution proof.
- **Context Synthesis**: When user provides iterative/ADHD stream-of-consciousness, synthesize multi-turn context; do not anchor rigidly on a single token or username.

## 📁 Workspace Paths
- `packages/sovereign-utils` — Shared sovereign utilities and helpers.
- `projects/range/ranch` — Ranch architecture (supersedes legacy mesh).
