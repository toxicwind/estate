# Tau: The Sovereign AI Agent Engine

> **Name note:** `.omp` == `.tau` — renamed monorepo. `alias omp` is leftover from install; real CLI is `tau` (`opencode`).
Tau (formerly OMP) is the AI-native agent engine for the Sovereign ecosystem, designed for 1M+ context reasoning and multi-tool orchestration.

> **Fork lineage:** Tau is a sovereign fork of [oh-my-pi](https://github.com/can1357/oh-my-pi) — itself a fork of [Pi](https://github.com/badlogic/pi-mono) by [Mario Zechner](https://github.com/mariozechner). This tree merges upstream **v18.2.6**.

## Architecture
- **Engine Core:** Located in `packages/coding-agent/` and `packages/agent/`.
- **Orchestration:** Built for federated tool use via MCP and high-performance inference through the Herd inference router.
- **Monorepo Integration:** Part of the Sovereign workspace architecture (see `/README.md` in the monorepo root).

## Upstream & Vendor Policy
> ⚠️ **CRITICAL: `vendor/` is strictly for upstream tracking and reference only.**
- Never edit or commit working code directly inside `vendor/` or `engine/vendor/`.
- `vendor/oh-my-pi/` mirrors canonical upstream to diff schemas, track dependency changes, and pull updates.
- Active monorepo development, workspace packages, and custom enhancements live exclusively in `packages/`, `crates/`, and `extensions/`.

## Getting Started
1. **Setup:** Ensure you are running from the monorepo root.
2. **Development:** Use the standard Tau CLI, aliased in your `.bashrc`:
   `alias tau='/home/toxic/.local/bin/tau --cwd="$PWD"'`

## ⚡ Hardware Architecture & Build Concurrency (Ryzen 7 8700F)
> **Build Throttle Notice**: Rust builds are configured with `jobs = 12` in `.cargo/config.toml` (target-cpu `znver4`).
- **Why throttled to 12?** The AMD Ryzen 7 8700F has 8 cores / 16 threads sharing a unified **16 MiB L3 cache**. Unbounded 16-thread `rustc` bursts saturate L3 cache lines and memory bus bandwidth simultaneously alongside `sccache`, causing desktop/shell input lag (loadavg > 24). Clamping to 12 jobs leaves 4 hardware threads dedicated to shell, editor, and system daemons while maintaining >90% compilation throughput.
- **To UNCAP to 100% (16 threads)**:
  ```bash
  cargo build -j 16
  # Or remove `jobs = 12` in .cargo/config.toml
  ```
- **CPU Scaling Governor**: Workstation uses `powersave` governor by default. For maximal burst performance during compilation:
  ```bash
  echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
  ```

## Documentation Index
- [Contributor Guide](CONTRIBUTING.md)
- [Packages Overview](../docs/packages/)

## Upstream v18.2.6 snapshot (oh-my-pi)

Factual highlights from the merged upstream release that apply to Tau (read `.omp` as `.tau`):

- **Scale:** 60+ providers · 31 built-in tools · 14 LSP ops · 28 DAP ops · ~80k lines of Rust core (search, shell, AST, PTY, desktop control, image decode, BPE counting — all in-process, no fork/exec on the hot path).
- **Entry points:** interactive TUI (`tau`), one-shot (`tau -p`), RPC (`tau --mode rpc`), and ACP (`tau acp`) for editor integration.
- **Subagents & review:** `task` fans out into isolated worktrees with schema-validated yields; `/review` spawns parallel reviewer subagents with P0–P3 verdicts; Agent Hub (`Alt+A`) supervises live subagents — see [docs/agent-hub.md](docs/agent-hub.md).
- **Providers:** 60+ providers incl. Command Code, Charm Hyper, OpenCode Go/Zen; 23 `web_search` backends (`providers.webSearchOrder`, new `providers.webSearchExclude`); new `providers.judgmentProvider` backend knob. Full reference: [omp.sh/docs/providers](https://omp.sh/docs/providers).
- **Eval:** Python retained subprocess kernel; JavaScript on an isolated subprocess with Bun Worker fallback (Ruby/Julia kernels retired upstream).
- **Compaction:** provider-native replay (`providerReplayThroughEntryId`), `/clear` reset boundaries, `previousSummary` separation — see [docs/compaction.md](docs/compaction.md).
- **Collab/share:** new `collab.autoStart` (`off`/`view`/`control`) auto-hosts interactive sessions; `/share` obfuscates secrets before upload — see [docs/collab.md](docs/collab.md).
- **Extensions:** runtime model discovery (`fetchDynamicModels`, 15s hard-bounded fetch), masked secret login prompts, `deliverAs: "aside"` injection at step boundaries, explicit `session_stop` block-vs-advisory semantics — see [docs/extensions.md](docs/extensions.md).
- **Docs added upstream in this merge:** [Agent Hub](docs/agent-hub.md), [LSP config](docs/lsp-config.md), [Magic keywords](docs/magic-keywords.md), [Vibe mode](docs/vibe-mode.md), [Session operations](docs/session-operations-export-share-fork-resume.md), [SDK](https://omp.sh/docs/sdk), [tools reference](https://omp.sh/docs/tools).

---
## Estate docs

- **Fleet knowledgebase** — the canonical estate map, active crews, repo index,
  standing rules, and docs index (source of truth; this README does not
  duplicate it):
  <https://github.com/toxicwind/sovereign-projects/blob/main/docs/fleet-knowledgebase.md>
- **Master README** — the doc-graph root:
  <https://github.com/toxicwind/sovereign-projects/blob/main/README.md>
