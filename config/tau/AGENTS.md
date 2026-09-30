# AGENTS.md — .tau Sovereign Architecture Source of Truth
# Source: .local/bin/agent -> .local/bin/tau -> /home/toxic/sovereign/agent
#   (cli framework: projects/sovereign-projects/tau/packages/coding-agent/src/cli.ts)
#   invoked by: bash via /home/toxic/sovereign/agent (shebang: #!/usr/bin/env bash)
#   bun path: /home/toxic/.bun/bin/bun
#   config: PI_CONFIG_DIR=$HOME/.tau, PI_CODING_AGENT_DIR=$HOME/.tau/agent
#   single default profile, no toxic
# References: debate.md (449l; line refs 195/218/241/44/54/59/332/36/401/33/315); SYNTHESIS.md; verify_report.md (PASS); fill_confirm.md (PASS); computer-use.json (first-class); no-echo-ban.md (toxic-persona MANDATORY #2)
#
# SOVEREIGN REPO: /home/toxic/sovereign (first-class operational repo)
# - AGENTS.md: /home/toxic/.tau/AGENTS.md → /home/toxic/sovereign/AGENTS.md (symlink, full docs)
# - helpers/: Bun/TS operational helpers (git-mutator, health-audit, mesh-probe, safe-rg-audit, ast-migrate, hardware-telemetry.sh, clean-orphans.sh)
# - packages/sovereign-utils: Shared sovereign utilities and ecosystem helpers
# - projects/range/ranch: Ranch system (supersedes legacy mesh)
# - config/ports.env: Port SSOT for all 25xxx services
# - mise.toml / pitchfork.toml: Service orchestration
# - src/: hal-substrate, openfang, services, mcp, deploy
# - tools/: llama-swap, nuvio-webos, sovereign-router, etc.
#
# KEY COMMANDS:
#   bun /home/toxic/sovereign/helpers/git-mutator.ts status|commit-push|scan-secrets
#   bun /home/toxic/sovereign/helpers/health-audit.ts
#   mise -C /home/toxic/sovereign run health|status|up|down

## 🏗️ Build Server (buildsrv - :25148)
- **Daemon**: Running on port `25148` via Pitchfork (`/home/toxic/sovereign/tools/buildsrv/buildsrvd.py`).
- **Heavy Builds**: Use `buildsrv submit --name <name> --repo <dir> --toolchain <bun|rust|go|python> --cmd "<cmd>"` for heavy builds rather than running long compilation in turn shell.
- **Worker & Cache Architecture**:
  - 2-worker concurrent queue preventing resource exhaustion.
  - NVMe-backed shared compiler/package caches: `sccache` (Rust/C++), `ccache`, and `uv` (Python wheels/environments).

## 🛡️ Anti-Hallucination & Execution Rules
- **Tool Execution Proof**: NEVER fake completion declarations or fire consecutive todo done calls without tool execution proof.
- **Context Synthesis**: When user provides iterative/ADHD stream-of-consciousness, synthesize multi-turn context; do not anchor rigidly on a single token or username.

## 📁 Workspace Paths
- `packages/sovereign-utils` — Shared sovereign utilities and helpers.
- `projects/range/ranch` — Ranch architecture (supersedes legacy mesh).
