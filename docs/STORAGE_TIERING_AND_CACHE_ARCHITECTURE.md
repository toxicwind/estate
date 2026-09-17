# Sovereign Storage Tiering & Cache Architecture

> **Hardware Drives & Topology**:
> - **Primary NVMe (`nvme1n1`)**: Crucial CT1000E100SSD8 1 TB (`/@` and `/@home` Btrfs subvolumes, `zstd:1` compressed).
> - **Secondary NVMe (`nvme0n1`)**: WD_BLACK SN850X 1000GB (PCIe Gen 4 x4, ~7,300 MB/s). Holds 138 GB active swap (`p4`) + 790 GB partition (`p3`).
> - **SATA SSD (`sda`)**: Samsung 870 QVO 1 TB (`sda4`, 860 GB ext4, mounted at `/mnt/sda4`).
> - **SATA HDD (`sdb`)**: Seagate IronWolf Pro 8 TB (`sdb2`, 7.3 TB NTFS, mounted at `/mnt/8TB`).

---

## 1. Core Principles: Latency vs. Bulk Storage

Local LLM inference requires memory-mapped I/O (`mmap`) to load model weights directly into VRAM and RAM. 
- **NVMe Flash Throughput**: **5,000–7,000 MB/s** sequential read. Loading a 15–20 GB GGUF takes ~2–3 seconds.
- **SATA HDD Throughput**: **150–200 MB/s** sequential read. Loading a 15–20 GB GGUF takes 1.5–2.5 minutes.

### Inviolable Invariant:
**All active model weights (`.gguf`, `.onnx`) MUST reside natively on NVMe flash (`nvme1n1` or `nvme0n1`). Never move active inference models to `/mnt/8TB`.**

---

## 2. Global Cache Migration & Symlink Hierarchy

To prevent the NVMe boot/home partition from filling up while maintaining zero runtime latency degradation, all compiler, package manager, and build caches have been centralized onto `/mnt/8TB/global-cache`.

### The Symlink Topology:
```text
/home/toxic/.bashrc
  └── export CACHE_DIR="$HOME/cache.symlinked-8tb"
        │
        ├──> /home/toxic/cache.symlinked-8tb  (Symlink)
        │     └──> /mnt/8TB/global-cache/     (Target on 8TB HDD)
        │           ├── bun/
        │           ├── ccache/
        │           ├── cmake/
        │           ├── cuda/
        │           ├── go-build/
        │           ├── go-mod/
        │           ├── huggingface/
        │           ├── npm/
        │           ├── pip/
        │           ├── pnpm/
        │           ├── sccache/
        │           ├── uv/
        │           └── zig/
        │
        ├──> /home/toxic/cache                (Fallback Symlink -> cache.symlinked-8tb)
        └──> /home/toxic/.cache/uv            (Symlink -> cache.symlinked-8tb/uv)
```

### Environment Variable Bindings (`~/.bashrc`):
```bash
export CACHE_DIR="$HOME/cache.symlinked-8tb"
export RUSTC_WRAPPER=sccache
export SCCACHE_DIR="$CACHE_DIR/sccache"
export CCACHE_DIR="$CACHE_DIR/ccache"
export GOCACHE="$CACHE_DIR/go-build"
export GOMODCACHE="$CACHE_DIR/go-mod"
export BUN_INSTALL_CACHE_DIR="$CACHE_DIR/bun"
export npm_config_cache="$CACHE_DIR/npm"
export PNPM_HOME="$CACHE_DIR/pnpm"
export UV_CACHE_DIR="$CACHE_DIR/uv"
export PIP_CACHE_DIR="$CACHE_DIR/pip"
export ZIG_GLOBAL_CACHE_DIR="$CACHE_DIR/zig"
export HF_HOME="$CACHE_DIR/huggingface"
export TORCH_HOME="$CACHE_DIR/torch"
export TRITON_CACHE_DIR="$CACHE_DIR/triton"
```

---

## 3. Modern Hugging Face (`hf`) Download Architecture

Hugging Face officially deprecated `huggingface-cli` in favor of **`hf`** (`/home/toxic/.local/bin/hf`).

### The Two Download Modes:

1. **Direct Standalone Model Download (Production Standard for GGUFs):**
   ```bash
   HF_HUB_ENABLE_HF_TRANSFER=1 hf download <repo_id> <filename.gguf> --local-dir /home/toxic/projects/models
   ```
   - `--local-dir` writes **actual standalone files directly** to the target NVMe path.
   - It **bypasses `$HF_HOME` completely** (no duplicate copy on the 8TB HDD).
   - Engages the Rust-based `hf-transfer` engine for multi-threaded parallel downloads.
   - At runtime, `llama-server` or `vLLM` opens the `.gguf` file directly via `mmap` at NVMe bus speeds.

2. **Shared Content-Addressed Hub Cache (Python / Transformers Standard):**
   ```bash
   hf download <repo_id>
   ```
   - Downloads into `$HF_HOME/hub/models--<org>--<repo>/` using SHA-256 blobs and commit snapshots.
   - Stored on the 8TB drive; shared across Python virtual environments.

---

## 4. Recovered Storage & Cleaned Artifacts Audit

On 2026-09-04, an exhaustive filesystem audit discovered and eliminated dead, unreferenced artifacts on NVMe without touching any active models:
- **60 GB of dead `.incomplete` downloads**: Aborted downloads from 2026-07-09 sitting in `projects/models/.cache/huggingface/download/`.
- **50 GB of abandoned `~/.cache/uv`**: Residual wheel archives prior to `UV_CACHE_DIR` redirection.
- **13 GB of pitchfork log bloat**: Dead SQLite `logs.db` (17.8 million debug rows) from inactive pitchfork supervisor.

**Result**: NVMe free headroom jumped from **4.2 GB (100% full)** to **95 GB available (90%)**, with all 40 active GGUF models running natively on NVMe.
