# Sovereign Swap Architecture — zram / zswap / NVMe Tiering

> **Hardware**: AMD Ryzen 7 8700F (Zen 4, 8C/16T, AVX-512), 62 GiB DDR5-6000, RTX 3090 24 GB VRAM, WD_BLACK SN850X 1 TB (OS + 138 GB swap), Crucial E100 1 TB (DRAM-less, /home), Samsung 870 QVO 1 TB + Seagate 7.3 TB HDD (cold storage)

> **Actual Workload**: Local LLM inference platform — 49 models across 4 llama.cpp forks, hot-swapped via llama-swap, GPU-offloaded on RTX 3090, MCP tool access, service mesh, Prometheus/Grafana observability.

---

## 1. Executive Summary

| Tier          | Technology     | Size                | Priority | Role                 |
| ------------- | -------------- | ------------------- | -------- | -------------------- |
| **L1 (hot)**  | **zswap pool** | 25% RAM = 15.5 GiB  | Highest  | Hot compressed cache |
| **L2 (warm)** | **NVMe swap**  | 138 GiB (SN850X p4) | Medium   | Warm spillover       |
| **L3 (cold)** | HDD/QVO        | 8+ TB               | Lowest   | Cold archive         |

**Current state (live, no reboot)**: zswap active, zram disabled, NVMe swap only. Load avg dropped **16 → 4.9** after enabling NVMe swap.

**Decision**: **Disable zram entirely, run zswap + NVMe swap**. Chris Down (Meta kernel MM) proves zram + disk swap causes **LRU inversion** — cold boot pages calcify in fast zram, hot working set spills to slow disk. zswap integrates with kernel reclaim, auto-evicts cold pages to NVMe.

---

## 2. Actual Workload Profile (What This Machine Does)

### Core Services (user `toxic`)

| Service           | Port        | Role                                                                                            | Memory Profile        |
| ----------------- | ----------- | ----------------------------------------------------------------------------------------------- | --------------------- |
| **llama-swap**    | 25100/25200 | Model orchestration — 49 models, 4 forks                                                        | 1-8 GB per model load |
| **mesh-front**    | 25100-25115 | Service mesh frontends (llama-swap, grafana, openfang, prometheus, hf-downloader, rust-web)     | ~50 MB each           |
| **openfang**      | 25103/25203 | Agent kernel web UI                                                                             | ~100 MB               |
| **mcpproxy**      | 25112/25113 | MCP proxy — 30+ servers (qdrant, fetch, github, sqlite, markitdown, prometheus, context7, etc.) | ~150 MB               |
| **qdrant**        | 6333        | Vector DB for embeddings                                                                        | ~600 MB               |
| **pitchfork**     | —           | Process supervisor                                                                              | ~40 MB                |
| **yote**          | —           | Background service                                                                              | ~130 MB               |
| **grafana**       | 25110       | Dashboards                                                                                      | ~200 MB               |
| **prometheus**    | 25105       | Metrics                                                                                         | ~25 MB                |
| **hf-downloader** | 25106       | Model fetching                                                                                  | ~25 MB                |

### LLM Model Fleet (49 models, 4 forks)

| Fork              | Binary                                                             | Models                                  | Typical VRAM | Use Case                                     |
| ----------------- | ------------------------------------------------------------------ | --------------------------------------- | ------------ | -------------------------------------------- |
| **beellama**      | `/home/toxic/projects/beellama.cpp/build-cuda86/bin/llama-server`  | 18 (EXAONE, Qwen Flash, Gemma, Strange) | 3-14 GB      | Primary — general chat, coding, long-context |
| **turboquant**    | `/home/toxic/projects/llama-cpp-turboquant/build/bin/llama-server` | 8 (Heretic, MN Grand)                   | 12-27 GB     | Creative, roleplay                           |
| **ik_llama**      | `/home/toxic/projects/ik_llama.cpp-main/build/bin/llama-server`    | 4 (Heretic UD/Q5)                       | 12-16 GB     | Auto-fit, defrag                             |
| **ik_turboquant** | `/home/toxic/projects/ik_turboquant/build/bin/llama-server`        | —                                       | —            | Experimental                                 |

**Routing**: Priority matrix with exclusive sets — only one model from `exclusive` set loads at a time. EXAONE (1.2B) stays preloaded as emergency fallback.

### GPU Memory Pressure

```
RTX 3090 24 GB VRAM
├── Reserved: 475 MiB
├── Active model KV cache: 1.4 GiB (typical 7B-14B)
├── Available for offload: ~22 GiB
└── Power: 300W cap, 50W idle
```

**Swap pressure source**: Hot model swap → anonymous pages (KV cache, embeddings) evicted to system RAM → zswap compresses → cold pages spill to NVMe.

### Desktop Overhead (Always Running)

| Process                                              | Memory  | Notes                                     |
| ---------------------------------------------------- | ------- | ----------------------------------------- |
| Zed editor                                           | 7.4 GB  | Primary IDE, TypeScript LSPs              |
| Firefox Nightly                                      | 1.3+ GB | 20+ content processes                     |
| Code Insiders                                        | 300+ MB | Secondary editor                          |
| Chromium headless                                    | 1.5+ GB | Browser automation (playwright/puppeteer) |
| Hyprland + QuickShell                                | 600 MB  | Wayland compositor + shell                |
| Telegram                                             | 540 MB  |                                           |
| LSPs (clangd, ts, pyright, harper, angular, graphql) | 500+ MB |                                           |

**Total baseline**: ~12-15 GB before any model loads.

---

## 3. Why Not zram + Disk Swap?

### The LRU Inversion Problem (Chris Down, Meta, March 2026)

```
zram (prio 100) + disk swap (prio 10):
  1. Boot: cold init pages → zram (fast, high prio)
  2. Hours later: zram FULL of cold pages
  3. Active workload swaps NOW → zram full → SPILLS TO DISK
  4. Hot pages on slow disk, cold pages in fast RAM = INVERTED
```

**zswap avoids this**: it's a **cache**, not a device. Kernel shrinker evicts LRU pages from zswap pool → disk swap _proactively_ under pressure. No priority inversion.

---

## 4. Kernel Parameter Reference (CachyOS / 6.10+)

### GRUB_CMDLINE_LINUX (persistent, limine)

```bash
# zswap — compression cache in front of swap device
zswap.enabled=1
zswap.compressor=zstd
zswap.max_pool_percent=25
zswap.shrinker_enabled=1
zswap.accept_threshold_percent=90

# AMD P-state (Zen 4, Ryzen 8700F)
amd_pstate=guided
cpufreq.default_governor=schedutil

# Transparent Huge Pages — madvise only (no khugepaged latency spikes)
transparent_hugepage=madvise

# NVMe — allow deep power states for idle
nvme_core.default_ps_max_latency_us=0
```

**Applied to all limine entries** (`/boot/limine.conf`):

- CachyOS BORE - znver4 LLM
- CachyOS Main
- CachyOS Server
- Backup - Original Server (madvise + quiet splash)

### /etc/sysctl.d/99-swap-vm.conf

```ini
# zswap optimization
vm.swappiness = 60                    # balanced; zswap is fast, aggressive OK
vm.page-cluster = 0                   # NVMe: single-page I/O, no readahead benefit
vm.vfs_cache_pressure = 50            # keep dentry/inode cache (docker, builds)

# Writeback tuning — prevent dirty-page stalls
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
vm.dirty_writeback_centisecs = 1500   # 15s intervals (vs 5s default)

# Compaction — only when needed
vm.compaction_proactiveness = 0
vm.extfrag_threshold = 500

# Memory pressure — early reclaim
vm.watermark_scale_factor = 10
vm.watermark_boost_factor = 0
```

### zram-generator.conf (DISABLED)

```ini
# [zram0]
# zram-size = 0
# compression-algorithm = zstd
# swap-priority = 100
```

---

## 5. zswap Deep Dive (Kernel 6.10+)

### Active Parameters (`/sys/module/zswap/parameters/`)

| Parameter                  | Value  | Rationale                                               |
| -------------------------- | ------ | ------------------------------------------------------- |
| `enabled`                  | `Y`    | On                                                      |
| `compressor`               | `zstd` | Best ratio/speed on Zen 4 (AVX-512 VAES)                |
| `max_pool_percent`         | `25`   | 62 GiB × 0.25 = 15.5 GiB pool → ~46 GiB effective @ 3:1 |
| `shrinker_enabled`         | `Y`    | Proactive LRU eviction under memory pressure            |
| `accept_threshold_percent` | `90`   | Hysteresis: resume accepting at 90% of max              |

### Deprecated (REMOVED 6.10+)

| Parameter                       | Removed | Replacement                             |
| ------------------------------- | ------- | --------------------------------------- |
| `zpool`                         | 6.18    | **zsmalloc only** (zbud/z3fold deleted) |
| `same_filled_pages_enabled`     | 6.10    | `zeromap` in swap layer                 |
| `non_same_filled_pages_enabled` | 6.10    | Always on                               |
| `exclusive_loads`               | 6.9     | Swap-cache-skip fast path               |

### Cgroup v2 Controls (Per-Workload)

```bash
# Disable zswap writeback for latency-critical (llama-swap, GPU inference)
echo 0 > /sys/fs/cgroup/llama-swap.slice/memory.zswap.writeback

# Limit zswap usage for heavy containers
echo 4G > /sys/fs/cgroup/docker.slice/memory.zswap.max

# Monitor
cat /sys/fs/cgroup/llama-swap.slice/memory.zswap.current
cat /sys/fs/cgroup/llama-swap.slice/memory.stat | grep zswap
```

---

## 6. AMD Zen 4 Specifics (Ryzen 7 8700F)

### amd-pstate Modes

| Mode        | Kernel Param         | Behavior                           | Best For              |
| ----------- | -------------------- | ---------------------------------- | --------------------- |
| **guided**  | `amd_pstate=guided`  | OS sets min/max, HW picks in range | **Default, balanced** |
| **active**  | `amd_pstate=active`  | OS hints via EPP (0=perf, 255=eff) | Laptop, efficiency    |
| **passive** | `amd_pstate=passive` | OS sets exact desired perf         | HPC, deterministic    |

**Recommendation**: `amd_pstate=guided` + `schedutil` governor. Zen 4 CPPC gives 166 performance levels (400 MHz – 4.68 GHz).

### AVX-512 + zstd

- Zen 4 supports **AVX-512 VAES, VPCLMULQDQ, GFNI** — zstd MT compression uses these
- Per-CPU `crypto_acomp_ctx` with PAGE_SIZE buffer → zero lock contention
- `zswap.max_pool_percent=25` keeps pool in L3-friendly working set

### Idle Power (C-states)

```bash
# Check current
cat /sys/devices/system/cpu/cpu*/cpuidle/state*/name

# Deeper C-states for idle (compile, LLM batch)
echo 1 | sudo tee /sys/module/amd_pstate/parameters/allow_cppc_deep_idle
```

---

## 7. NVMe Swap Device (WD_BLACK SN850X)

### Partition Layout

```
nvme0n1p4  138.3 GiB  Linux swap  (UUID: c24a45c7-e353-4a8c-a58e-979342980fc4)
```

### /etc/fstab Entry

```fstab
UUID=c24a45c7-e353-4a8c-a58e-979342980fc4  none  swap  sw,pri=10,nofail  0 0
```

### Discard / TRIM (Async)

```bash
# systemd-fstrim timer (weekly) handles swap partition
systemctl enable --now fstrim.timer

# Or manual
fstrim -v /dev/nvme0n1p4
```

### SN850X Specifics

- **DRAM-full controller** — no HMB needed
- **SLC cache** ~12% capacity (~120 GB) — sustained writes stay fast
- **Power states**: APST enabled by default (`nvme_core.default_ps_max_latency_us=0`)
- **Endurance**: 600 TBW — swap writes negligible (< 1 TB/yr typical)

---

## 8. GPU VRAM ↔ System Swap Interaction

### RTX 3090 24 GB VRAM

| Workload                | VRAM Pressure | System Swap Behavior                               |
| ----------------------- | ------------- | -------------------------------------------------- |
| llama-swap (7-35B GGUF) | 8-24 GB       | Offloads KV cache / layers to system RAM           |
| SDXL / Flux             | 12-20 GB      | CPU offload via `mmap` → anonymous pages → zswap   |
| Training (PyTorch)      | OOM risk      | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` |

### Cgroup Isolation for GPU Workloads

```bash
# /etc/systemd/system/llama-swap.slice.d/99-zswap.conf
[Slice]
MemoryZSwapWriteback=0
MemoryZSwapMax=8G
MemoryHigh=48G
MemoryMax=56G
CPUWeight=200
IOWeight=200
```

---

## 9. Monitoring & Observability

### Real-Time Swap Health

```bash
# zswap stats
watch -n 1 'cat /sys/kernel/debug/zswap/*'

# Key ratios
# Zswapped / Zswap = live compression ratio (target > 2.5:1)
# pool_limit_hit > 0 → increase max_pool_percent
# reject_compress_poor > 0 → data incompressible, zswap less useful

# vmstat swap events
vmstat 1 | awk '{print $7, $8, $9, $10}'  # si so bi bo

# Memory pressure (PSI)
cat /proc/pressure/memory
# some avg10 > 20% → moderate pressure
# full avg10 > 5% → severe, consider earlyoom
```

### Prometheus Exporters

```yaml
# node_exporter --collector.zswap
# Exposes:
# node_zswap_pool_total_size_bytes
# node_zswap_stored_pages
# node_zswap_written_back_pages
# node_zswap_pool_limit_hit_total
# node_zswap_reject_*
```

### Grafana Dashboard Panels

| Panel             | Query                                           | Alert Threshold |
| ----------------- | ----------------------------------------------- | --------------- |
| zswap pool usage  | `zswap_pool_total_size / (0.25 * mem_total)`    | > 85%           |
| Swap I/O rate     | `rate(node_vmstat_pswpout[5m])`                 | > 100/s         |
| Memory pressure   | `node_pressure_memory_some_avg10`               | > 20%           |
| Compression ratio | `zswapped_pages * 4096 / zswap_pool_total_size` | < 2.0           |

---

## 10. Benchmarking Methodology

### Baseline Capture (Pre-Change)

```bash
#!/bin/bash
# bench-swap-baseline.sh
set -euo pipefail

OUT="swap-baseline-$(date +%Y%m%d-%H%M%S).txt"
{
  echo "=== SYSTEM ==="
  free -h
  swapon --show
  cat /proc/cmdline
  sysctl vm.swappiness vm.page-cluster vm.vfs_cache_pressure
  cat /sys/module/zswap/parameters/*

  echo -e "\n=== STRESS: memory-pressure ==="
  # stress-ng --vm 8 --vm-bytes 90% --vm-keep -t 60s --metrics-brief

  echo -e "\n=== STRESS: compile ==="
  # time make -j16 -C /path/to/llama.cpp 2>&1 | tail -5

  echo -e "\n=== STRESS: LLM load ==="
  # curl -X POST http://localhost:25100/v1/chat/completions \
  #   -d '{"model":"qwen-27b","messages":[{"role":"user","content":"hi"}],"max_tokens":512}'
} | tee "$OUT"
```

### Key Metrics to Compare

| Metric                       | zram+disk (old) | zswap+disk (new) | Target   |
| ---------------------------- | --------------- | ---------------- | -------- |
| Load avg (idle)              | 16              | 4-5              | < 2      |
| Swap read latency (p99)      | 2-5 ms          | < 500 µs         | < 200 µs |
| Compilation time (llama.cpp) | baseline        | -15%             | faster   |
| LLM first-token latency      | baseline        | -30%             | faster   |
| OOM events/week              | 3-5             | 0                | 0        |

---

## 11. Rollback Procedure

```bash
# 1. Disable zswap
echo 0 | sudo tee /sys/module/zswap/parameters/enabled

# 2. Re-enable zram (if needed)
systemctl enable --now systemd-zram-setup@zram0

# 3. Restore limine (remove zswap params)
sed -i 's/zswap\.\w*=[^ ]* //g' /etc/default/limine
# OR edit /boot/limine.conf directly
# Then: limine-install

# 4. Reboot
reboot
```

---

## 12. Future Research (Phase 2+)

| Area                                        | Source                               | Status                     |
| ------------------------------------------- | ------------------------------------ | -------------------------- |
| **Multi-comp zram** (lz4 → zstd recompress) | Linux 6.2+, `recomp_algorithm`       | Experimental               |
| **Dictionary training** (JVM, browser, LLM) | Linux 6.4+, `zstd --train`           | Planned                    |
| **Ariadne-style hotness tracking**          | HPCA 2025 (arXiv:2502.12826)         | Userspace daemon via DAMON |
| **DAMON + DAMOS**                           | Kernel 6.14+, per-cgroup reclaim     | Watch                      |
| **Entropy-based algo selection**            | sinashan/adaptive-memory-compression | Research                   |

---

## 13. Quick Commands Cheatsheet

```bash
# Status
swapon --show
cat /sys/kernel/debug/zswap/pool_total_size
cat /sys/kernel/debug/zswap/stored_pages
cat /sys/kernel/debug/zswap/written_back_pages

# zswap live config
echo zstd | sudo tee /sys/module/zswap/parameters/compressor
echo 25 | sudo tee /sys/module/zswap/parameters/max_pool_percent
echo Y | sudo tee /sys/module/zswap/parameters/shrinker_enabled
echo 90 | sudo tee /sys/module/zswap/parameters/accept_threshold_percent

# AMD P-state
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_driver
cat /sys/devices/system/cpu/amd_pstate/status
echo guided | sudo tee /sys/devices/system/cpu/amd_pstate/status

# NVMe health
nvme smart-log /dev/nvme0n1
fstrim -v /dev/nvme0n1p4

# Cgroup for llama-swap
systemctl set-property llama-swap.slice MemoryZSwapWriteback=0
systemctl set-property llama-swap.slice MemoryZSwapMax=8G
```

---

## 14. References

1. **Chris Down**, "Debunking zswap and zram myths" (March 2026) — https://chrisdown.name/2026/03/24/zswap-vs-zram-when-to-use-what.html
2. **Liang et al.**, "Ariadne: Hotness-Aware Compressed Swap" (HPCA 2025) — arXiv:2502.12826
3. **Meta/Instagram**, "zswap in production: 5:1 compression, 25% disk write reduction" — LWN 2023
4. **Kernel Docs** — `Documentation/admin-guide/mm/zswap.rst`, `Documentation/admin-guide/blockdev/zram.rst`
5. **vijay-wang/mm_topics** — Swap subsystem deep dive (zswap/zram/swap tables)
6. **reapercanuk39/zram-tuning** — Multi-comp, writeback, PSI roadmap
7. **boundring/cachyos-zswap-migrate** — CachyOS migration tooling
8. **KSPP/linux** — amd-pstate docs, hardened kernels
