# Kimi Code Fork Feasibility Research

**Date**: 2026-07-28
**Question**: Is the Kimi Code CLI we run (`kimi-code` v0.29.2, binary `/home/toxic/.kimi-code/bin/kimi`) open source, and can we maintain a `kimi-code-sovereign` fork?
**Verdict**: **(a) — Yes. Official open-source repo exists under MIT. A fork is fully feasible.** (Evidence below.)

---

## 1. Official repository (verdict a — confirmed)

| Fact | Value | Source |
|---|---|---|
| Repo | https://github.com/MoonshotAI/kimi-code | `gh api repos/MoonshotAI/kimi-code` |
| License | **MIT** (`LICENSE` at repo root) | API `.license.spdx_id = MIT` |
| Stars | ~5,442 (as of 2026-07-28) | API `.stargazers_count` |
| Language | TypeScript (pnpm monorepo) | API + root tree |
| Created / pushed | 2026-05-22 / actively pushed (2026-07-28, same day as audit) | API |
| Docs site | https://moonshotai.github.io/kimi-code/ (repo `homepage` field) | API |
| npm package | `@moonshot-ai/kimi-code@0.29.2` — **exact version match** with our binary (`kimi --version` → `0.29.2`), published by GitHub Actions with provenance | `npm view @moonshot-ai/kimi-code` |
| Native releases | GitHub Releases ship `kimi-code-linux-x64.zip` etc. for tag `@moonshot-ai/kimi-code@0.29.2` — this is where our 162 MB SEA binary comes from | `gh api .../releases/latest` |

Note: the bare `kimi-code` npm package (v1.0.11, `whitesmith/kimi-code`) is an **unrelated third-party proxy wrapper** — not the CLI we run. The real one is the scoped `@moonshot-ai/kimi-code`.

## 2. Build system (from repo root + `apps/kimi-code/package.json`)

- **Monorepo**: pnpm workspaces (`pnpm-workspace.yaml`), `apps/` (kimi-code CLI, kimi-web, vis), `packages/` (agent-core, agent-core-v2, node-sdk, telemetry, kap-server, …).
- **Bundler**: `tsdown`; **tests**: `vitest`; **lint**: `oxlint --type-aware`; **changesets** for versioning; `Makefile`, `flake.nix` also present.
- **Library build**: `pnpm --filter @moonshot-ai/kimi-code run build` → `dist/main.mjs` (the npm `bin: kimi`).
- **Native single-executable build**: `apps/kimi-code/scripts/native/build.mjs` (`build:native:sea` / `build:native:release` profiles) — confirms the local 162 MB ELF is a SEA-compiled bundle (Node SEA-style; embedded JS visible in `strings` output, e.g. `FEEDBACK_ISSUE_URL = "https://github.com/MoonshotAI/kimi-code/issues"`).
- **CI publishing**: `changeset publish` with npm provenance (`publishConfig.provenance: true`) — release pipeline is fully in-repo and reproducible.

Because the source is MIT and the full build (including the SEA native binary) is scripted in-repo, **binary forensics / SEA extraction (paths b/c) are unnecessary** — we fork the TypeScript source directly.

## 3. Fork plan: `kimi-code-sovereign` — patch points

All locations verified to exist in `main` today:

1. **Thinking default (keep thinking on)**
   `packages/agent-core-v2/src/kosong/model/thinking.ts` is the self-described "single authority on thinking semantics" — it resolves the `[thinking]` config section (`enabled` / `effort` / `keep`) against model metadata, with the "always-on clamp" for `always_thinking` models. Patch the `ThinkingDefaults` resolution (in `model.types.ts` / the persistence wrapper `app/kosongConfig/configSection`) so our fleet defaults to thinking enabled at the effort we want, instead of model-catalog defaults.

2. **MCP config (`mcp.json` schema / loading)**
   Dual loaders exist: `packages/agent-core/src/mcp/config-loader.ts` and `packages/agent-core-v2/src/agent/mcp/config-loader.ts`; legacy migration in `packages/migration-legacy/src/{paths.ts,steps/mcp.ts}`. Patch here to add sovereign-specific schema extensions (e.g. default federation to our mcpproxy :25109, or auto-injecting the byte-vision-proxy gateway :25120).

3. **Quota / telemetry**
   Telemetry is a clean interface in `packages/agent-core/src/telemetry.ts` (`TelemetryClient`, with a `noopTelemetryClient` already exported), wired in `apps/kimi-code/src/cli/telemetry.ts` — gated by `enabled: options.config.telemetry !== false` (i.e. config `telemetry = false` already opts out; no `telemetry.toml` quota counters found — `gh search code 'quota'` returned nothing). Fork patch: flip the default to opt-out (or hard-wire `noopTelemetryClient`) so nothing phones home regardless of config. Cloud appender lives in `packages/agent-core-v2/src/app/telemetry/cloudAppender.ts` + `packages/telemetry/`.

4. **Tool-select (progressive tool disclosure)**
   Registered as an experimental flag in `packages/agent-core/src/flags/registry.ts`: id `tool-select`, env `KIMI_CODE_EXPERIMENTAL_TOOL_SELECT`, **`default: false`**; implementation flag in `packages/agent-core-v2/src/agent/toolSelect/flag.ts`. Fork patch: flip `default` to `true` (keeps MCP tool schemas out of the top-level `tools[]` and loads them on demand via `select_tools` — useful with our 43-MCP federation).

### Suggested mechanics

- `git remote add upstream https://github.com/MoonshotAI/kimi-code.git`; fork under our own org as `kimi-code-sovereign`, track `main` (repo is pushed daily — expect frequent rebases; keep patches small and localized to the four points above).
- Build: `pnpm install && pnpm --filter @moonshot-ai/kimi-code run build` for the JS bundle; `pnpm -C apps/kimi-code run build:native:sea` for a drop-in replacement of `/home/toxic/.kimi-code/bin/kimi` (verify with `kimi --version` + a smoke run; `scripts/native/smoke.mjs` exists for exactly this).
- Publish flow is changesets-based; for a private fork just build locally — no npm publish needed.
- Rename/branding: MIT permits it with license retention; binary name and `@moonshot-ai` scope would need changing only if we distribute.

## 4. Evidence log (commands run, 2026-07-28)

- `npm view kimi-code` → unrelated wrapper; `npm view @moonshot-ai/kimi-code` → v0.29.2, MIT, deps: none, repo `MoonshotAI/kimi-code/apps/kimi-code`, published yesterday via OIDC.
- `gh api orgs/MoonshotAI/repos --jq '.[].name'` → `kimi-cli` (older Python CLI, Apache-2.0) and `kimi-code-zed-extension` also present; `gh search repos 'kimi-code'` → `MoonshotAI/kimi-code`, MIT, 5442★.
- `strings /home/toxic/.kimi-code/bin/kimi | grep -i github.com` → embedded JS bundle with `FEEDBACK_ISSUE_URL = "https://github.com/MoonshotAI/kimi-code/issues"` — binary provenance confirmed as this repo.
- `gh api repos/MoonshotAI/kimi-code/releases/latest` → tag `@moonshot-ai/kimi-code@0.29.2` with `kimi-code-linux-x64.zip` asset (our binary's origin).
- `gh api .../contents/{package.json,apps/kimi-code/package.json,packages/telemetry/README.md,packages/agent-core/src/telemetry.ts,packages/agent-core-v2/src/kosong/model/thinking.ts,packages/agent-core/src/flags/registry.ts,apps/kimi-code/src/cli/telemetry.ts}` → build system + patch points above.
- `/home/toxic/.kimi-code/bin/kimi --version` → `0.29.2` (exact match to latest npm/release).

**Nothing blocked.** No local files were modified besides this report.
