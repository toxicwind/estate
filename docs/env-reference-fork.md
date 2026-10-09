# Sovereign / Ranch Fork Environment Variables Reference

This reference documents custom, source-owned environment variables introduced specifically in the **Sovereign / Ranch** fork (`sovereign/projects/tau`, `brand`, `herd`, `shep`, and mesh infrastructure).

---

## 1. Mesh, Port SSOT, & Infrastructure Daemons

| Variable | Default | Description |
| :--- | :--- | :--- |
| `HINDRA_API_URL` | `http://127.0.0.1:25117` | Endpoint URL for the local Hindsight knowledge mesh daemon. |
| `MBX_CACHE_PORT` | `25148` | Port for the Pitchfork-managed `mbx-cache` remote task cache (formerly `brand`; the `brand`/`brandd` naming is retired). |
| `PAPER_POLLER_PORT` | `25149` | Port for the HFT-style arXiv/alphaXiv paper poller daemon. |
| `ANTIGRAVITY_USER_AGENT_VERSION` | `4.3.0` | Sovereign override for Antigravity backend protocol headers. |

---

## 2. CI/CD Push-Building & Automation

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BRAND_ROOT` | `/home/toxic/brand` | Root directory for `brand` job queues, active runs, logs, and compiled binary caches. |
| `OMP_NATIVE_CARGO_PROFILE` | `local` | Cargo profile override (`local` / `release`) optimized for Zen 4 native target architectures. |
| `RUSTFLAGS` | `-C target-cpu=native -C link-arg=-fuse-ld=mold` | Compiler performance flags enforcing mold linker and native CPU optimizations. |

---

## 3. Custom Integration & Wrapper Flags

| Variable | Default | Description |
| :--- | :--- | :--- |
| `OMP_SHELL_PATH` | `/bin/bash` | Override shell path for `brush-core` embedded shell execution bypasses. |
| `GITHUB_ACTOR` | `toxicwind` | GitHub Packages and Maven authentication handle for sovereign registry pulls. |
| `CLX_NO_PROGRESS` | `1` | Suppresses progress bars in custom CLI utilities during headless agent execution. |
| `CLX_TEXT_MODE` | `1` | Forces plain text mode for UI rendering in constrained terminal environments. |
