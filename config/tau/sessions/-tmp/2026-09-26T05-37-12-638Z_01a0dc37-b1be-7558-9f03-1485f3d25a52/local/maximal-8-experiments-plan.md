# Plan: Maximal 8 Empirical Experiments — Sovereign Scaffolding, Tau & ACP Integration

## Context
Standard enterprise inference frameworks (vLLM, HuggingFace Accelerate) enforce heavy synchronous CUDA driver barriers and staging copies when offloading model layers to CPU RAM, inflating per-layer offload latencies to ~75 ms. On our bare-metal workstation (AMD Ryzen 7 8700F Phoenix APU + NVIDIA RTX 3090 24GB SM86), the physical link is PCIe 4.0 x8 (capped by Phoenix CPU lane provisioning at 12.72 GB/s empirical DMA saturation, with dynamic Gen 2 -> Gen 4 link renegotiation). 

Rather than isolated throwaway scripts in `/tmp`, all 8 experiments are built directly into our **Sovereign scaffolding** (`/home/toxic/estate`), tightly integrated with **Tau** (`projects/sovereign-projects/tau`), and exposed over **ACP (Agent Client Protocol)**. This upgrades the sovereign codebase with a permanent, production-grade MoE PCIe streaming engine, live ACP hardware telemetry, and Tau skills/tools auditable via `tau-session-audit` and executable via `tau-tmux`.

---

## Approach

### Part 1: Sovereign MoE Streaming Engine (`/home/toxic/estate/tools/pcie-moe/`)
Create a permanent engine directory `/home/toxic/estate/tools/pcie-moe/` containing the 8 progressive experiments and shared low-level CUDA/Triton utilities:

- **Shared Driver Primitive**: `/home/toxic/estate/tools/pcie-moe/cuda_substrate.py`
  - Encapsulates `cudaHostAlloc` (`cudaHostAllocMapped | cudaHostAllocWriteCombined`), `cudaHostGetDevicePointer`, and raw `cuMemcpyHtoDAsync_v2` via ctypes.
  - Zero PyTorch tensor allocation overhead; wraps pointers into raw 64-bit integer virtual addresses for direct SM/DMA access.

- **Experiment 1 (Hardware Bounds & Dynamic Link Renegotiation)**:
  - File: `/home/toxic/estate/tools/pcie-moe/exp1_link_bandwidth.py`
  - Action: Benchmark pinned H2D/D2H DMA throughput across buffer sizes ($64\text{ KB}$ to $2\text{ GB}$).
  - Hardware Telemetry: Concurrently reads `/sys/bus/pci/devices/0000:01:00.0/current_link_speed` every $10\text{ ms}$ to log the exact latency of the ASPM dynamic upgrade from Gen 2 (5.0 GT/s) to Gen 4 (16.0 GT/s).
  - Output: Structured JSON payload with saturation curve and transition delay.

- **Experiment 2 (Framework Dispatch & Synchronization Tax Decomposition)**:
  - File: `/home/toxic/estate/tools/pcie-moe/exp2_dispatch_tax.py`
  - Action: Microsecond-precision comparison of moving an 8-bit weight matrix ($11008 \times 4096$, $45.1\text{ MB}$) across 4 dispatch paths:
    1. PyTorch Eager: `tensor.to('cuda', non_blocking=True)` + `stream.synchronize()`.
    2. PyTorch Custom Stream: Background stream + stream-wait event.
    3. Ctypes Runtime API: `cudaMemcpyAsync` + `cudaEventRecord`.
    4. Direct Driver API: `cuMemcpyHtoDAsync_v2` without Python GIL locks.
  - Output: CPU dispatch latency vs GPU bus transfer latency.

- **Experiment 3 (Triton SM Direct Zero-Copy Tile & Coalescing Sweep)**:
  - File: `/home/toxic/estate/tools/pcie-moe/exp3_triton_zerocopy_tile.py`
  - Action: Direct GPU SM register loads across the PCIe 4.0 x8 bus from host RAM without DMA engine.
  - Parameter Sweep: `BLOCK_M` $\in [16, 32, 64]$, `BLOCK_N` $\in [32, 64, 128]$, `BLOCK_K` $\in [32, 64, 128]$, `num_warps` $\in [4, 8]$, `num_stages` $\in [1, 2, 3]$.
  - Morphe Principle: Casts raw integer mapped host addresses directly inside Triton IR (`B_host_ptr_int.to(tl.pointer_type(tl.int8))`).
  - Output: Matrix of effective GB/s per tile geometry against the $12.72\text{ GB/s}$ DMA ceiling.

- **Experiment 4 (Asynchronous Double-Buffered Ring-Buffer Streaming)**:
  - File: `/home/toxic/estate/tools/pcie-moe/exp4_double_buffered_dma.py`
  - Action: Zero-bubble overlapped expert streaming. Stream 1 transfers Expert $N+1$ weights over the physical link ($12.72\text{ GB/s}$) while Stream 0 computes Tensor Core GEMM on Expert $N$.
  - Synchronization: Pure GPU-side hardware events (`cudaStreamWaitEvent`), completely eliminating CPU-side barriers (`stream.synchronize()`).
  - Output: Overlap efficiency percentage and per-layer latency comparison.

- **Experiment 5 (PTX Cache-Directive Surgery — Morphe Bytecode on GPU IR)**:
  - File: `/home/toxic/estate/tools/pcie-moe/exp5_ptx_cache_surgery.py`
  - Action: Morphe bytecode surgery applied to GPU instructions: compile Triton kernel to PTX, parse the instruction stream, and rewrite memory load directives:
    - `.ca` (Cache at all levels — L1 and L2).
    - `.cg` (Cache at global level only — bypass L1, avoid SMEM eviction).
    - `.cs` (Cache streaming — evict-first policy for one-pass expert weights).
  - Output: L2 cache hit/miss rates and stall cycle comparison under consecutive expert evaluations.

- **Experiment 6 (Host Memory Substrates Benchmark on CachyOS Bore Kernel)**:
  - File: `/home/toxic/estate/tools/pcie-moe/exp6_memory_substrates.py`
  - Action: Benchmark 4 allocation strategies under Linux 7.2 CachyOS Bore kernel on the 8700F:
    1. Standard pageable RAM.
    2. Pinned RAM (`cudaHostAllocDefault`).
    3. Write-Combined Pinned RAM (`cudaHostAllocMapped | cudaHostAllocWriteCombined`).
    4. Unified Virtual Memory (`cudaMallocManaged` with `cudaMemAdviseSetAccessedBy`).
  - Output: Latency and throughput breakdown per substrate.

- **Experiment 7 (Tiered MoE Routing Simulation with Zipfian Distribution)**:
  - File: `/home/toxic/estate/tools/pcie-moe/exp7_tiered_moe_simulation.py`
  - Action: Simulate a 32-expert MoE layer (Mixtral/DeepSeek style) with $\alpha = 1.2$ Zipfian routing for 512 tokens.
  - Tiered Architecture: Top 8 hot experts cached in RTX 3090 GDDR6X VRAM; 24 cold experts streamed dynamically via Exp 4's async double-buffer pipeline.
  - Output: End-to-end token latency and speedup vs corporate offload baseline.

- **Experiment 8 (Sovereign Telemetry Service & Dashboard)**:
  - File: `/home/toxic/estate/tools/pcie-moe/server.ts`
  - Action: Bun HTTP + WebSocket daemon running on port 25219 (SSOT configured in `ports.env`).
  - Endpoints:
    - `GET /api/status`: Real-time PCIe link generation, width, ASPM status, GPU VRAM, temperature, and power.
    - `POST /api/run/:exp_id`: Executes experiments 1–7 and streams JSON results.
    - `GET /`: Interactive web console with live SVG throughput meters and latency breakdown.

---

### Part 2: Tau Integration (`projects/sovereign-projects/tau`)
Make the 8 experiments directly controllable, runnable, and auditable through the Tau coding-agent framework:

1. **Sovereign Skill Creation**:
   - Target: `/home/toxic/estate/skills/sm86-moe-bench/SKILL.md` (symlinked into `~/.tau/agent/skills/sm86-moe-bench`).
   - Content: Defines intent triggers ("sm86 bench", "pcie moe bench", "profile pcie zero copy"), CLI usage, and expected JSON structures.
   - Helper Runner: `/home/toxic/estate/skills/sm86-moe-bench/helper/bench.ts` (executes specific experiment IDs or full suite via Bun).

2. **Tau Tool Registration**:
   - Target: `/home/toxic/projects/sovereign-projects/tau/packages/coding-agent/src/tools/sm86-moe-bench.ts`
   - Class `Sm86MoeBenchTool` registered in `essential-tools.ts` or as an ecosystem discoverable tool.
   - Schema:
     ```typescript
     interface Sm86MoeBenchArgs {
       experiment: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | "all";
       telemetry?: boolean;
     }
     ```
   - Execution: Invokes Bun/Python engine in `/home/toxic/estate/tools/pcie-moe/` and returns structured JSON metrics directly to the model context.

3. **Tau Tmux Lab Recipe**:
   - Integration with `skill://tau-tmux`:
     - Creates detached session `tau-moe-lab`.
     - Pane 0: Active compute kernel runner (`exp4_double_buffered_dma.py`).
     - Pane 1: Dynamic PCIe link renegotiation monitor (`nvidia-smi` + sysfs loop).
     - Pane 2: Real-time telemetry feed from port 25219.

4. **Tau Session Audit Logging**:
   - Every benchmark execution writes a structured event trace into `~/.tau/sessions/` with `type: "tool_result"` and `tool: "sm86_moe_bench"`, making all test runs verifiable via `bun run /home/toxic/estate/skills/tau-session-audit/helper/audit.ts`.

---

### Part 3: ACP (Agent Client Protocol) Integration
Expose the PCIe MoE streaming suite to any ACP-connected editor (Zed, Neovim) or frontend client:

1. **ACP Custom Request & Tool Handler**:
   - Target: `/home/toxic/projects/sovereign-projects/tau/packages/coding-agent/src/modes/acp/acp-agent.ts`
   - In `AcpAgent`, register support for the `sovereign/pcieMoeBench` method:
     - Routes incoming ACP RPC requests to `Sm86MoeBenchTool`.
     - Emits standard ACP `progress` notifications as the benchmark progresses through each layer/tile sweep.
2. **ACP Telemetry Event Mapping**:
   - Target: `/home/toxic/projects/sovereign-projects/tau/packages/coding-agent/src/modes/acp/acp-event-mapper.ts`
   - Maps PCIe link state changes (e.g. Gen 2 -> Gen 4 link ramp events) and streaming throughput metrics into ACP `session/update` event envelopes, allowing connected editor status bars to display live PCIe streaming bandwidth ($12.72\text{ GB/s}$) and active expert caching status.

---

### Part 4: Sovereign Service & Health Orchestration
1. **Port Registration**:
   - File: `/home/toxic/estate/config/ports.env`
   - Add: `PCIE_MOE_PORT=25219` (maintaining the strict 25xxx Port SSOT).
2. **Health Audit Integration**:
   - File: `/home/toxic/estate/helpers/health-audit.ts`
   - Add check: `auditPcieMoeHealth()`:
     - Verifies RTX 3090 PCIe link status (`sysfs current_link_width == 8`, `max_link_speed == 16.0 GT/s`).
     - Verifies `cudaHostAlloc` availability and telemetry daemon response on port 25219.
3. **Supervisor Entry**:
   - File: `/home/toxic/estate/pitchfork.toml`
   - Register `[daemons.pcie-moe-telemetry]` so Pitchfork manages the Bun telemetry service alongside Openfang and Caddy.

---

## Critical Files & Anchors

1. `/home/toxic/estate/docs/MORPHE_PATCHING.md:85-119` — Architectural reference for bytecode-level extraction and runtime shimming.
2. `/home/toxic/estate/config/ports.env:1-35` — Sovereign port SSOT.
3. `/home/toxic/estate/helpers/health-audit.ts:1-50` — Sovereign health-check harness.
4. `/home/toxic/projects/sovereign-projects/tau/packages/coding-agent/src/modes/acp/acp-agent.ts:612-680` — ACP Agent protocol handler and session dispatcher.
5. `/home/toxic/projects/sovereign-projects/tau/packages/coding-agent/src/tools/essential-tools.ts:1-40` — Tau tool registry.

---

## Verification

Concrete automated verification steps across all 8 experiments and sovereign integrations:

1. **Exp 1**: `python /home/toxic/estate/tools/pcie-moe/exp1_link_bandwidth.py`
   - Pass criteria: Tabular output for all sizes ($64\text{ KB}$ to $2\text{ GB}$); peak DMA saturation measured between $12.0\text{--}13.0\text{ GB/s}$; link upgrade event detected and logged.
2. **Exp 2**: `python /home/toxic/estate/tools/pcie-moe/exp2_dispatch_tax.py`
   - Pass criteria: Microsecond dispatch time for Path 4 (Driver API) $<15\ \mu\text{s}$ vs Path 1 (PyTorch Eager) $>150\ \mu\text{s}$.
3. **Exp 3**: `python /home/toxic/estate/tools/pcie-moe/exp3_triton_zerocopy_tile.py`
   - Pass criteria: Compiles all tile sweeps without memory faults; logs peak tile configuration.
4. **Exp 4**: `python /home/toxic/estate/tools/pcie-moe/exp4_double_buffered_dma.py`
   - Pass criteria: Numerical correctness matches PyTorch reference; overlap efficiency $>80\%$.
5. **Exp 5**: `python /home/toxic/estate/tools/pcie-moe/exp5_ptx_cache_surgery.py`
   - Pass criteria: Disassembles and runs `.cs` modified PTX; records L2 cache stall delta.
6. **Exp 6**: `python /home/toxic/estate/tools/pcie-moe/exp6_memory_substrates.py`
   - Pass criteria: Validates all 4 substrates; Write-Combined mapped RAM outperforms standard pageable by $>2\times$.
7. **Exp 7**: `python /home/toxic/estate/tools/pcie-moe/exp7_tiered_moe_simulation.py`
   - Pass criteria: 32 experts, 512 tokens; end-to-end latency $<25\text{ ms}$ per layer (vs $75\text{ ms}$ offload baseline).
8. **Exp 8 & Telemetry**: `bun run /home/toxic/estate/tools/pcie-moe/server.ts` & `curl -s http://localhost:25219/api/status`
   - Pass criteria: Returns HTTP 200 with JSON payload containing `pcie_gen: 4`, `pcie_width: 8`, `vram_allocated_mb`.
9. **Tau & ACP Integration Verification**:
   - Tau Skill: `tau --skills "sm86-moe-bench" -p "run sm86-moe-bench exp 1"` completes successfully.
   - ACP RPC: Run test ACP probe `bun test /home/toxic/projects/sovereign-projects/tau/packages/coding-agent/test/acp-agent.test.ts` to ensure no ACP protocol regressions.
   - Health Audit: `bun run /home/toxic/estate/helpers/health-audit.ts` prints PASS for the PCIe MoE subsystem.

---

## Assumptions & Contingencies

1. **Ryzen 7 8700F Silicon Limit**: The CPU physically provisions 8 lanes (PCIe 4.0 x8) to the dGPU slot. All bandwidth comparisons strictly treat $12.72\text{ GB/s}$ as $100\%$ bus saturation.
2. **BAR1 Size Independence**: BAR1 is 256 MiB in VBIOS. All zero-copy GPU reads operate via DMA bus-mastering and mapped virtual device pointers (`cudaHostAllocMapped`), which bypass BAR1 completely.
3. **ACP Protocol Versioning**: ACP follows protocol version 1. Custom telemetry methods are namespaced under `sovereign/*` and degrade gracefully if the connected client does not register custom telemetry listeners.
4. **Port Availability**: Port 25219 is reserved for `PCIE_MOE_PORT` in `ports.env`. If occupied, `server.ts` cleans up stale sockets before binding.
