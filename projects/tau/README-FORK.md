# Tau Engine Fork — Architecture & Audit

## Structure

```
tau/
├── package.json          ← root wrapper, workspaces → engine/packages/*
├── vendor/               ← upstream repos (oh-my-pi, kimi-code-sovereign, etc.) — READ-ONLY REFERENCE ONLY
│   └── oh-my-pi/         ← upstream oh-my-pi source (canonical tracking mirror, never edited directly)
├── engine/               ← main working tree (fork of oh-my-pi with sovereign changes)
│   ├── packages/         ← canonical packages — ALL code lives here
│   ├── crates/           ← Rust crates (pi-ast, pi-builtins, pi-iso, pi-natives, pi-shell, pi-voice, pi-walker)
│   ├── vendor/           ← empty placeholder (submodules defined but not cloned)
│   ├── package.json      ← primary workspace definition
│   ├── Cargo.toml        ← Rust workspace
│   └── .gitmodules       ← upstream submodule references
├── packages/             ← compatibility mirror synced from engine/packages/
├── scripts/              ← build, CI, release scripts
├── .tau/                 ← harness state (sessions, stats, config)
└── README-FORK.md        ← this file
```

## How It Works

- **engine/** is the fork of upstream oh-my-pi. All code changes go here.
- **vendor/** holds upstream reference repos that track real remotes (pullable via git submodule). It is strictly read-only reference material: do not make direct changes or development edits here.
- **packages/** is a compatibility mirror synced from engine/ — root package.json workspaces point here.
- **crates/** contains the Rust native layer (pi-natives, pi-ast, etc.).

## Upstream Sync

```bash
cd tau/engine/vendor/oh-my-pi && git pull origin main
cd tau/engine && git submodule update --init --recursive
```

Then re-sync: `rsync -av engine/packages/ packages/`

## Session Audit — Diff Dataframes

### engine/vendor/oh-my-pi vs engine/packages (sovereign fork)

Saved: `.tau/agent/sessions/-projects-sovereign-projects-tau/2026-09-08T06-07-13-107Z_01a07fa0-b2d3-76df-9cd1-b3c185165228/engine-vendor-diff.csv`

- **414 total differences**
- **209 items only in engine** — sovereign additions
- **205 items only in vendor** — upstream-only (not yet in engine)

### Sovereign additions (only in engine):

| Category | Count | Items |
|----------|-------|-------|
| Provider registries | 90+ | aimlapi, alibaba, baseten, cerebras, coreweave, deepinfra, devin, exa, firepass, fireworks, github-copilot, gitlab-duo, gmi-cloud, google-antigravity, huggingface, kagi, kilo, kimi-code, litellm, llama-cpp, lm-studio, meta, minimax, mistral, moonshot, nanogpt, novita, nvidia, ollama, openai-codex, opencode, openrouter, parallel, perplexity, qianfan, sakana, siliconflow, synthetic, tavily, together, umans, venice, vllm, wafer, wafer-serverless, xai, xiaomi, yolo-auto, zai, zenmux, zhipu |
| hashline package | 1 | New sovereign patch language |
| wire package | 1 | Networking layer |
| examples/ | 20+ | SDK examples, hooks, extensions |
| dist/ build artifacts | 5+ | browser-relay, collab-web, stats, tui |
| test fixtures | 30+ | Core tests, edit tests, eval tests |

### Upstream-only (only in vendor, NOT in engine):

| Category | Count | Items |
|----------|-------|-------|
| cline-pass | 10+ | infra, model, tests |
| activity logging | 5+ | activity, stats/traces |
| sharpshooter | 5+ | memory prompts |
| video tools | 5+ | vcs, video |
| MCP tools | 10+ | mcp, workpool |

## Code Quality Rules (from AGENTS.md)

1. **Verify live, then claim.** No "done" without curl/lsof/nvidia-smi/tsgo --noEmit.
2. **Fail loud.** Never 2>/dev/null, never \|\| true.
3. **No commit without explicit user request.** Fork stays private under toxicwind.
4. **Multi-strategy.** Non-trivial work → 3+ approaches, benchmark, keep runner-up.
5. **TDD/BDD.** Failing assertion first, then fix.
6. **Use emergence tools first.** GHAS → ast-grep → Tombi for TOML.
7. **call_tool_destructive is DEFAULT for state changes.** Read-only = inspection only.
8. **No /dev/null, no banner echo.** Both waste tokens.
9. **Fix bashrc nested quote issue.** Use functions instead of aliases.
10. **CUDA-aware.** RTX 3090 — validate with nvidia-smi.
11. **Stop stacking long commands.** Sub-second probes. Reserve 60|120 for intentional jobs.
12. **No head truncation.** Read full files — 1M context available.
13. **Timeout/failfast/high-frequency is FIRST-CLASS everywhere.** No insane monolithic timeouts.
14. **Dynamic ${ENV_VAR} interpolation is first-class** in configs/scripts.
15. **Lint + test after EVERY code change; coverage floor 82%.**
16. **BACKGROUNDING IS FIRST-CLASS.** Long ops MUST run in background, tracked by PID.
17. **GOAL = ENDLESS TODO.** TODO.md is continuous improvement, not finite list.

## Provider Registry Map

All provider files live in `engine/packages/ai/src/registry/`:

```
registry/
├── aiand.ts           ← AI And provider
├── aimlapi.ts         ← AIML API
├── alibaba-coding-plan.ts
├── alibaba-token-plan.ts
├── anthropic.ts
├── api-key-login.ts
├── api-key-validation.ts
├── aws.ts
├── azure.ts
├── baseten.ts
├── bedrock-mantle.ts
├── cerebras.ts
├── cloudflare-ai-gateway.ts
├── coreweave.ts
├── cursor.ts
├── deepinfra.ts
├── deepseek.ts
├── devin.ts
├── exa.ts
├── firepass.ts
├── fireworks.ts
├── github-copilot.ts
├── gitlab-duo.ts
├── gitlab-duo-workflow.ts
├── gmi-cloud.ts
├── google.ts
├── google-antigravity.ts
├── google-gemini-cli.ts
├── google-vertex.ts
├── huggingface.ts
├── kagi.ts
├── kilo.ts
├── kimi-code.ts
├── litellm.ts
├── llama-cpp.ts
├── lm-studio.ts
├── meta.ts
├── minimax.ts
├── mistral.ts
├── moonshot.ts
├── nanogpt.ts
├── novita.ts
├── nvidia.ts
├── ollama.ts
├── ollama-cloud.ts
├── openai.ts
├── openai-codex.ts
├── openai-codex-device.ts
├── opencode-go.ts
├── opencode-zen.ts
├── openrouter.ts
├── parallel.ts
├── perplexity.ts
├── qianfan.ts
├── qwen-portal.ts
├── sakana.ts
├── siliconflow.ts
├── siliconflow-cn.ts
├── synthetic.ts
├── tavily.ts
├── together.ts
├── umans.ts
├── venice.ts
├── vercel-ai-gateway.ts
├── vllm.ts
├── wafer-serverless.ts
├── wafer.ts
├── xai.ts
├── xai-oauth.ts
├── xiaomi.ts
├── xiaomi-token-plan-ams.ts
├── xiaomi-token-plan-cn.ts
├── xiaomi-token-plan-sgp.ts
├── yolo-auto.ts
├── zai.ts
├── zenmux.ts
├── zhipu-coding-plan.ts
└── oauth/
    ├── devin.ts
    ├── gitlab-duo-workflow.ts
    ├── minimax-code.ts
    ├── opencode.ts
    ├── openrouter.ts
    └── wafer.ts
```
