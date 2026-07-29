# Sovereign Architecture — Single Source of Truth

> **Hardware**: AMD Ryzen 7 8700F (Zen 4, 8C/16T, AVX-512 VAES/VPCLMULQDQ/GFNI) · 62 GiB DDR5-6000 · NVIDIA RTX 3090 24 GB (sm_86, no FP8)
>
> **Storage Topology**:
>
> | Device      | Model                  | Size   | Role            | Partition Layout                                                          |
> | ----------- | ---------------------- | ------ | --------------- | ------------------------------------------------------------------------- |
> | **nvme0n1** | WD_BLACK SN850X        | 1 TB   | **OS + Swap**   | p1: 600M EFI (vfat) · p2: 2G ext4 · p3: 790G (unused) · **p4: 138G swap** |
> | **nvme1n1** | Crucial CT1000E100SSD8 | 1 TB   | **Boot + Home** | p1: 4.1G /boot (vfat) · p2: 927G /home (btrfs, @home subvol)              |
> | **sda**     | Samsung 870 QVO        | 1 TB   | **Cold SSD**    | sda4: 860G ext4 (archives, datasets)                                      |
> | **sdb**     | Seagate ST8000NT001    | 7.3 TB | **Bulk HDD**    | sdb2: 7.3T NTFS (media, backups, cold storage)                            |
> | sdc/sdd     | —                      | 0 B    | Empty bays      | —                                                                         |
>
> **OS**: CachyOS (linux-cachyos-bore), Limine bootloader, Btrfs root (@ subvol), systemd + pitchfork process supervisor
>
> **Core Principle**: Local-first LLM inference platform. Every service has a stable 25xxx port. llama-swap is the _only_ LLM front door.

---

## 1. Memory & Swap Architecture

### Tiered Swap (No zram)

| Tier          | Technology                      | Size               | Priority | Role                                         |
| ------------- | ------------------------------- | ------------------ | -------- | -------------------------------------------- |
| **L1 (hot)**  | **zswap pool** (zstd, shrinker) | 25% RAM = 15.5 GiB | Highest  | Compressed RAM cache in front of swap device |
| **L2 (warm)** | **NVMe swap** (SN850X p4)       | 138 GiB            | Medium   | Warm spillover, async discard                |
| **L3 (cold)** | HDD / QVO                       | 8+ TB              | Lowest   | Cold archive, never touches L1/L2            |

**zram is DISABLED** — Chris Down (Meta kernel MM, March 2026) proves zram + disk swap causes **LRU inversion**: cold boot pages calcify in fast zram, hot working set spills to slow disk. zswap integrates with kernel reclaim, auto-evicts LRU pages to NVMe _proactively_.

### Kernel Command Line (All Limine Entries)

```bash
zswap.enabled=1 zswap.compressor=zstd zswap.max_pool_percent=25 \
zswap.shrinker_enabled=1 zswap.accept_threshold_percent=90 \
amd_pstate=guided cpufreq.default_governor=schedutil \
transparent_hugepage=madvise nvme_core.default_ps_max_latency_us=0
```

### Sysctl (`/etc/sysctl.d/99-zswap-vm.conf`)

```ini
vm.swappiness = 60
vm.page-cluster = 0
vm.vfs_cache_pressure = 50
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
vm.dirty_writeback_centisecs = 1500
vm.watermark_scale_factor = 10
vm.watermark_boost_factor = 0
vm.compaction_proactiveness = 0
vm.extfrag_threshold = 500
```

### Cgroup Isolation (llama-swap slice)

```bash
systemctl set-property llama-swap.slice \
  MemoryZSwapWriteback=0 \
  MemoryZSwapMax=8G \
  MemoryHigh=48G \
  MemoryMax=56G \
  CPUWeight=200 \
  IOWeight=200
```

---

## 2. The Four llama.cpp Forks — Why They Exist

| Fork              | Binary Path                                                        | Upstream Base                | Unique Value                                                                                                               | Models Served                                                                             |
| ----------------- | ------------------------------------------------------------------ | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **beellama.cpp**  | `/home/toxic/projects/beellama.cpp/build-cuda86/bin/llama-server`  | llama.cpp + Anbeeld's DFlash | **DFlash speculative decoding** (Qwen/Gemma drafters), TurboQuant KV (turbo2/3/4), reasoning loop guard, mmproj multimodal | 18 models: EXAONE, Qwen Flash (64-256k), Gemma 12B (MTP/DFlash), Strange, Qwen 27B DFlash |
| **turboquant**    | `/home/toxic/projects/llama-cpp-turboquant/build/bin/llama-server` | llama.cpp + TheTom/buun      | **TurboQuant KV cache** (turbo2/3/4/TCQ), heretic/mn-grand creative models, fused CUDA kernels                             | 8 models: Heretic 27B (64-256k), MN-GRAND 23B                                             |
| **ik_llama**      | `/home/toxic/projects/ik_llama.cpp-main/build/bin/llama-server`    | llama.cpp + ik               | **Auto-fit** (dynamic ngl), **defrag** (--fit-margin), `LLAMA_API_KEY=` keyless auth                                       | 4 models: Heretic UD/Q5                                                                   |
| **ik_turboquant** | `/home/toxic/projects/ik_turboquant/build/bin/llama-server`        | ik_llama + turboquant        | Experimental merge of auto-fit + TurboQuant KV                                                                             | — (experimental)                                                                          |

### Why Not Upstream?

- **DFlash**: Upstream llama.cpp has DFlash but beellama adds cross-ctx tuning, TurboQuant KV integration, reasoning loop guard
- **TurboQuant KV**: Upstream has partial turbo2; full turbo2/3/4 + TCQ + fused kernels are fork-only (Gabe Ortiz / signalnine)
- **Auto-fit / defrag**: ik_llama's `--fit --fit-margin 512 --defrag-thold 0.1` dynamically sizes ngl to VRAM, defrags KV on pressure — not upstream
- **gemma4-assistant arch**: Required for Gemma 4 MTP models; upstream llama.cpp lacks this architecture

### Fork Lineage

```
llama.cpp (upstream)
    ├─ beellama.cpp (Anbeeld) ── DFlash + TurboQuant KV + reasoning guard
    ├─ turboquant (TheTom/buun) ── TurboQuant KV (turbo2/3/4, TCQ)
    ├─ ik_llama (ik) ── auto-fit + defrag + keyless auth
    └─ ik_turboquant (merge) ── experimental
```

---

## 3. club3090 Pattern — Local LLM as Tier-3 Provider

**Definition**: Any OpenAI-compatible server on `http://127.0.0.1:8020/v1` is auto-eligible as `"local"` provider in the AST Matrix router.

```python
# sovereign-router/free_zed_gateway/gateway.py
"base": os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8020/v1"),  # club3090 style
```

**In practice**: llama-swap runs on `:25100` (external) and `:25200` (internal). The AST Matrix router at `:25104` treats any `:8020` endpoint as a local fallback tier. This pattern originated from the `club3090` project (local RTX 3090 inference) and was adopted because:

- **No API keys** for local inference
- **Same OpenAI schema** — drop-in replacement for cloud providers
- **Tier-3 in RouteLLM elo** — used only when cloud providers fail or for privacy

**Current club3090 endpoints in this stack**:

- `llama-swap` on `:25100` (primary, 49 models via 4 forks)
- `mcp-llama-swap` MCP server pointing to `:25100/v1`
- `openfang` agent kernel can route to local via same pattern

---

## 4. Routing Matrix — Priority, Exclusive Sets, Eviction Costs

### Priority Ladder (Higher = More Protected)

| Tier              | Models                                           | Priority | Use Case                           |
| ----------------- | ------------------------------------------------ | -------- | ---------------------------------- |
| **Emergency**     | EXAONE 1.2B (IQ4_XS → Q8_0)                      | 31-35    | Always preloaded, coding/emergency |
| **Utility**       | Qwen 9B Flash (DeepSeek-V4 distilled)            | 28-30    | Fast general chat                  |
| **Heavy**         | Qwen 27B DFlash (IQ4_XS, Q4_K_M, MTP)            | 25-27    | Quality reasoning                  |
| **Balanced**      | Gemma 4 12B (Unified/MTP/Uncensored/DFlash)      | 21-24    | Coding + general                   |
| **Context Tiers** | Qwen Flash 64k/96k/128k/256k, Gemma 64k/96k/128k | 11-20    | Long-context                       |
| **Creative**      | Strange 64k, MN-GRAND, Heretic 27B               | 4-10     | Roleplay, creative                 |
| **Experimental**  | Cerebellum, Holo 35B MoE                         | 0        | Research                           |

### Exclusive Sets (Only One Loaded at a Time)

```
exclusive:
  df9b | df9bs | df9da | qdf27 | qdf27m | gm4u | gm4m | gm4un | gm4df
  | qf64 | qf96 | qf128 | qf256 | qfm64 | qfm128
  | gm64 | gm96 | gm128 | gmm64 | gmm128 | st64
  | mg64 | mg96 | mg128 | h128 | h256 | hu64 | hu96 | hq5
  | cb96 | df96 | ho64 | exa1 | exa2 | exa3 | exa4 | exa5
```

**Effect**: Loading any model in this set unloads _all others_ in the set. Prevents VRAM OOM from multiple 27B models.

### Eviction Costs (Lower = Evicted First)

```yaml
exa1: 35 # Never evict (emergency)
...
df96: 1 # Evict first (27B DFlash, heavy)
ho64: 1 # Holo MoE, evict first
```

---

## 5. llama-swap — The LLM Front Door

### Ports

| Port      | Role                                                       |
| --------- | ---------------------------------------------------------- |
| **25100** | Public OpenAI-compatible API (`/v1`, `/ui`, `/models/sse`) |
| **25200** | Internal backend (mesh-front proxies here)                 |

### Config (`/home/toxic/sovereign/tools/llama-swap/config.yaml`)

- **Health checks**: 300s timeout, 600s TTL
- **Preload**: `beellama/exaone-4-0-1-2b-iq4xs` on startup (3.3 GiB, ~70 tok/s idle)
- **Hooks**: SQLite event log at `/tmp/llama-swap-events.log`
- **Metrics**: In-memory 5000 samples, 1m flush

### Inference Chain

```
Clients (Zed, OpenFang, IDEs, Grok)
         │
         ▼
llama-swap :25100 (toxicwind Go fork)
  │  internal/astmatrix/  — 6 strategies, ELO, circuit breakers
  │  SQLite WAL health DB — request history, model health, healing events
  ▼
Fork backends :25001-25099
  ├─ beellama      (DFlash, TurboQuant KV, reasoning guard)
  ├─ turboquant    (TurboQuant KV, creative models)
  ├─ ik_llama      (auto-fit, defrag)
  └─ ik_turboquant (experimental merge)
```

---

## 6. AST Matrix Router — 6 Strategies (Go Port inside llama-swap)

Ported from TypeScript (`tools/sovereign-router/sovereign-router-ts/router.ts`) to Go (`llama-swap-main/internal/astmatrix/`).

| Strategy             | Behavior                                                  |
| -------------------- | --------------------------------------------------------- |
| **hybrid** (default) | sticky → ast_race of top-weighted → circuit_chain         |
| **ast_race**         | Parallel 4 providers; first AST/code-shaped response wins |
| **sticky_affinity**  | 30-min session sticky for multi-turn                      |
| **weighted_elo**     | Dynamic ELO from success/latency                          |
| **circuit_chain**    | Sequential with open/half-open circuit breakers           |
| **fifo_matrix**      | Bounded FIFO queue (back-pressure)                        |

### Providers (7)

1. **llama-swap** (local) — 49 models, 4 forks
2. **OpenRouter** — cloud fallback
3. **NVIDIA NIM** — Nemotron, Llama, Qwen, DeepSeek, Mistral, Phi, Gemma
4. **Groq** — LPU speed
5. **Cerebras** — wafer-scale
6. **Google** — Gemini
7. **Mistral** — Mistral API

### Health DB (SQLite WAL)

- Request history → ELO updates
- Model health → healing events
- Circuit breaker state (closed/open/half-open)

---

## 7. Sovereign MCP Gateway (`:25120`)

Trust boundary + resource allocator in front of upstream MCP servers (e.g. `byte-vision-mcp` on `:25121`).

| Feature                          | Implementation                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------------- |
| **Circuit breaker**              | Per upstream (closed/half-open/open) — poisoned/down upstream quarantined           |
| **Sticky session affinity**      | `notifications/initialized` pins session to one upstream (commitment game)          |
| **Provenance-tagged tool union** | `tools/list` namespaced `<upstream>__<tool>`; `server/discover` synthesized locally |
| **502 failover**                 | Next healthy upstream on error                                                      |

**Self-serve**: `GET /health`, `GET /ui`. Unit tested at 100% coverage (`bun run test:gateway:cov`).

---

## 8. Sovereign Monitor — Agentic Runtime Intelligence

| Module                  | Coverage | Purpose                                                                                                     |
| ----------------------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| `recursive-fallback.ts` | 88%+     | Multi-level try/catch with helpers, recursive decomposition, watchdog escalation (ReAct/Reflexion grounded) |
| `watchdog.ts`           | 100%     | Bounded agentic-loop watchdog: judge → SIGINT → SIGKILL, audit trail, MCP stdio exclusion                   |
| `repo-radar.ts`         | 100%     | Autonomous repo discovery via shallow GHAS queries; novelty scoring; autonomy signal detection              |

**Default failure discipline** for every non-trivial tool call:

```
primary → fix_syntax (coerce input) → scaffold (write helper) → borrow_ghas (discover pattern)
→ retrieve_tool (shallow MCP query) → recurse (decompose + retry smaller) → escalate (watchdog trips)
```

Each catch block has its own nested try/catch — **no single point of failure**.

---

## 9. Service Mesh — All 25xxx Ports

| Service              | Port        | Runtime             | Role                                                 |
| -------------------- | ----------- | ------------------- | ---------------------------------------------------- |
| **llama-swap**       | 25100/25200 | Go (toxicwind fork) | LLM front door + AST Matrix router                   |
| **rust-web**         | 25101       | Rust                | Ops dashboard + embedded watchdog                    |
| **yote**             | 25102       | Bun                 | Telegram / status                                    |
| **openfang**         | 25103/25203 | Rust                | Agent kernel — 206 models, 61 skills, Discord bridge |
| **sovereign-router** | 25104       | Bun (TS)            | 5-strategy AST Matrix (external tooling)             |
| **prometheus**       | 25105       | Go                  | Metrics                                              |
| **hf-downloader**    | 25106       | Bun                 | GGUF download UI                                     |
| **null-g-proxy**     | 25107       | Bun                 | Extra LLM proxy                                      |
| **mcpproxy**         | 25109       | Go                  | MCP federation (43 MCPs → 1 endpoint)                |
| **grafana**          | 25110       | Go                  | Optional dashboards                                  |
| **ghas-api**         | 25112       | Bun                 | GitHub Advanced Search API                           |
| **ghas-mcp**         | 25113       | Bun                 | GHAS MCP (HTTP, depends on ghas-api)                 |
| **mesh-hub**         | 25115       | Bun                 | 20 GHAS features × every service                     |
| **byte-vision**      | 25121       | Go binary           | Vision MCP (OCR / screenshot analysis)               |
| **byte-vision-p**    | 25120       | Bun                 | **Sovereign MCP Gateway**                            |
| **tailscale-funnel** | —           | Bash                | Tailscale Funnel → rust-web only                     |
| **redis**            | 25199       | Redis               | Session cache, telemetry                             |
| **qdrant**           | 25133       | Qdrant              | Vector DB (0.0.0.0)                                  |

**No Caddy, no landing** — path routing fought real services (`/api/*` → openfang vs rust-web). Every service owns its 25xxx port. Artifacts archived under `/home/toxic/archive/caddy-removed-*`.

---

## 10. GPU & VRAM Management

### RTX 3090 (sm_86, 24 GB VRAM)

| Component                                  | Allocation               |
| ------------------------------------------ | ------------------------ |
| Reserved                                   | 475 MiB                  |
| Desktop (Hyprland + QuickShell + XWayland) | ~200-400 MiB             |
| Active model KV cache                      | 1.4 GiB (typical 7B-14B) |
| **Available for offload**                  | **~22 GiB**              |

### LACT Undervolt Profile (Quiet)

```yaml
fan_curve:
  - temp: 50°C, duty: 30%
  - temp: 60°C, duty: 45%
  - temp: 70°C, duty: 65%
  - temp: 80°C, duty: 85%
hysteresis:
  change_threshold: 4
  spindown_delay_ms: 12000
power_cap: 300W  # range 100-365W
clock_offset: {0: -80}  # MHz on P0
thermal_target: 80°C
```

**Measured idle**: 35°C, 30% fan (~1190 RPM), 50W draw.

---

## 11. Monitoring & Observability

### Real-Time Swap Health

```bash
# zswap stats
watch -n 1 'cat /sys/kernel/debug/zswap/*'

# Compression ratio
bc <<< "scale=2; $(cat /sys/kernel/debug/zswap/stored_pages) * 4096 / $(cat /sys/kernel/debug/zswap/pool_total_size)"

# PSI
cat /proc/pressure/memory
```

### Key Thresholds

| Metric                  | Warning  | Critical |
| ----------------------- | -------- | -------- |
| zswap pool usage        | > 85%    | > 95%    |
| `pool_limit_hit`        | > 0/min  | > 10/min |
| PSI `some` avg10        | > 20%    | > 50%    |
| Swap read latency (p99) | > 500 µs | > 2 ms   |
| Compression ratio       | < 2.5:1  | < 2.0:1  |

### Prometheus Exporters

```yaml
# node_exporter --collector.zswap
node_zswap_pool_total_size_bytes
node_zswap_stored_pages
node_zswap_written_back_pages
node_zswap_pool_limit_hit_total
node_zswap_reject_*
```

---

## 12. Rollback Procedure

```bash
# 1. Disable zswap
echo 0 | sudo tee /sys/module/zswap/parameters/enabled

# 2. Re-enable zram
systemctl enable --now systemd-zram-setup@zram0

# 3. Restore limine (remove zswap params)
sed -i 's/zswap\.\w*=[^ ]* //g' /etc/default/limine
limine-install

# 4. Reboot
reboot
```

---

## 13. Future Research (Phase 2+)

| Area                                        | Source                               | Status                     |
| ------------------------------------------- | ------------------------------------ | -------------------------- |
| **Multi-comp zram** (lz4 → zstd recompress) | Linux 6.2+, `recomp_algorithm`       | Experimental               |
| **Dictionary training** (JVM, browser, LLM) | Linux 6.4+, `zstd --train`           | Planned                    |
| **Ariadne-style hotness tracking**          | HPCA 2025 (arXiv:2502.12826)         | Userspace daemon via DAMON |
| **DAMON + DAMOS**                           | Kernel 6.14+, per-cgroup reclaim     | Watch                      |
| **Entropy-based algo selection**            | sinashan/adaptive-memory-compression | Research                   |

---

## 14. Quick Commands

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
