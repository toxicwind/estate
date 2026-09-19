# Tau: The Sovereign AI Agent Engine

> **Name note:** `.omp` == `.tau` — renamed monorepo. `alias omp` is leftover from install; real CLI is `tau` (`opencode`).
Tau (formerly OMP) is the AI-native agent engine for the Sovereign ecosystem, designed for 1M+ context reasoning and multi-tool orchestration.

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
- ~~[Architecture Guide](/docs/ARCHITECTURE.md)~~ — removed 2026-09-19: `docs/ARCHITECTURE.md` does not exist
- ~~[Setup Guide](/docs/SETUP.md)~~ — removed 2026-09-19: `docs/SETUP.md` does not exist
- [Contributor Guide](/CONTRIBUTING.md)
- [Packages Overview](/docs/packages/)

---
- **Harness state:** See `.tau/harness-ref.json` (mesh URL `25127` mcpproxy-go, subagent `inkling-small:free`, env deconfused, `.pi`/`.omp` symlinks verified, temp `1.0`, effort mapped).
- **Commit reference:** `fa7f8ad` in sovereign-projects root.
*(Managed by the Sovereign infrastructure pipeline.)*
