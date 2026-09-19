# Tau Engine Fork — Architecture & Audit

## Structure

```
tau/
├── package.json          ← REMOVED 2026-09-19: no root package.json exists (only package.json.bak); engine/packages/*/package.json are standalone
├── vendor/               ← upstream mirror (oh-my-pi only; a full sovereign-projects checkout, NOT a read-only upstream mirror)
│   └── oh-my-pi/         ← sovereign-projects checkout (origin = github.com/toxicwind/sovereign-projects), NOT an upstream oh-my-pi mirror
├── engine/               ← main working tree (fork of oh-my-pi with sovereign changes)
│   ├── packages/         ← canonical packages — ALL code lives here
│   ├── crates/           ← REMOVED 2026-09-19: no crates/ under engine/; Rust crates live at tau/crates/ (pi-ast, pi-builtins, pi-iso, pi-natives, pi-shell, pi-voice, pi-walker)
│   ├── vendor/           ← upstream mirror: engine/vendor/oh-my-pi (full sovereign-projects checkout, not a placeholder)
│   ├── package.json      ← primary workspace definition
│   ├── Cargo.toml        ← Rust workspace
│   └── .gitmodules       ← upstream submodule references
├── packages/             ← REMOVED 2026-09-19: this compatibility mirror does not exist; the root CLI resolves via dist/omp
├── scripts/              ← build, CI, release scripts
├── .tau/                 ← REMOVED 2026-09-19: no .tau/ at repo root; the tau launcher keeps session state at ~/.tau (user home)
└── README-FORK.md        ← this file
```

## How It Works

- **engine/** is the fork of upstream oh-my-pi. All code changes go here.
- **vendor/** holds a full sovereign-projects checkout (`vendor/oh-my-pi`, `engine/vendor/oh-my-pi`; origin = github.com/toxicwind/sovereign-projects) — it is the fork's own monorepo state, not a read-only upstream mirror. (Corrected 2026-09-19.)
- ~~**packages/** compatibility mirror~~ — removed 2026-09-19: `tau/packages/` does not exist; the root CLI (`dist/omp` via the `tau` launcher) resolves packages from `engine/packages/` directly.
- **crates/** (`tau/crates/`, at repo root — not under `engine/`) contains the Rust native layer (pi-natives, pi-ast, etc.). (Corrected 2026-09-19.)

## Upstream Sync

```bash
cd tau/engine/vendor/oh-my-pi && git pull origin main   # NOTE 2026-09-19: origin here is github.com/toxicwind/sovereign-projects (the fork's own monorepo), NOT upstream oh-my-pi; this advances the fork, it does not track upstream oh-my-pi
cd tau/engine && git submodule update --init --recursive
```

~~Then re-sync: `rsync -av engine/packages/ packages/`~~ — removed 2026-09-19: `tau/packages/` does not exist, so this target is bogus.

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
## Provider Registry Map (corrected 2026-09-19)

There is no per-vendor file map under `engine/packages/ai/src/registry/` — that directory holds
auth/build machinery (`oauth/`, `hooks/`, `engine/`, `registry.ts`), not per-vendor files. The
85-file map that used to be here was stale and has been removed. Provider wiring is split:

- **Per-vendor descriptors**: `engine/packages/catalog/src/provider-models/descriptors.ts`
  (compiled model catalog in `src/models.json`: 69 providers; identity/classification rules in
  `engine/packages/catalog/src/compat/rules/providers/*.kdl`, generated into `src/compat/rules.json`).
- **Auth providers**: `engine/packages/catalog/src/compat/auth-ids.ts`, generated from
  `engine/packages/catalog/src/compat/rules/auth/*.kdl` (82 auth providers as of 2026-09-19).
- **Wire adapters**: `engine/packages/ai/src/providers/` — ~12 lazy wire families
  (`anthropic*.ts`, `openai-*.ts`, `google*.ts`, `ollama.ts`, `azure-openai-responses.ts`,
  `bedrock-mantle.ts`, `cursor/`, `devin/`, `github-copilot-headers.ts`, `gitlab-duo*.ts`,
  `kimi.ts`, `synthetic.ts`). Most OpenAI-compatible vendors ride the shared OpenAI wire via
  their catalog descriptor; they do not have dedicated files.
