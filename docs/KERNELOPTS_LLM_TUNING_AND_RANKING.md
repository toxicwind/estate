# Kernelopts LLM Tuning & Algorithmic Ranking Reference

> **Target Platform**: AMD Ryzen 7 8700F (Zen 4, 8C/16T) · 62 GiB DDR5-6000 · NVIDIA GeForce RTX 3090 24 GB (GA102, Ampere sm_86)
> **Active Bootloader**: Limine (`/boot/limine.conf`) on `/dev/nvme1n1p1`
> **Audit Tool**: `/home/toxic/.local/bin/kernelopt-audit` (executable in `$PATH`)

---

## 1. Algorithmic Ranking of Available Kernels

Using the multi-dimensional scoring model in `kernelopt-audit` (evaluating GPU stream sync, PCIe bus power states, P-state locks, CPU scheduling jitter, and TLB efficiency):

| Rank | Composite (0–100) | LLM Latency | Throughput | Kernel Entry | Scheduler | Status |
|:---:|:---:|:---:|:---:|---|---|:---:|
| **#1** | **100.0** | **100.0** | **100.0** | **`CachyOS BORE - znver4 LLM`** | **BORE** | `CONFIG` |
| **#2** | **100.0** | **100.0** | **100.0** | **`Backup - Original Server`** | **SERVER** | `CONFIG` |
| **#3** | **93.9** | **91.4** | **96.2** | **`CachyOS Main`** | **CACHYOS** | `CONFIG` |
| **#4** | **93.6** | **89.3** | **100.0** | **`LIVE CURRENT (7.1.5-1-cachyos-server)`** | **SERVER** | **`LIVE NOW`** |
| **#5** | **93.6** | **89.3** | **100.0** | **`CachyOS Server`** | **SERVER** | `CONFIG` |

---

## 2. Deep Dissection of the NVIDIA Low-Latency Stack

The difference between the #1 ranked entry (`CachyOS BORE - znver4 LLM`) and the live running kernel comes down to three NVIDIA parameters that eliminate CPU-GPU synchronization and clock latency.

### A. `nvidia.NVreg_RegistryDwords="OverrideMaxPerf=0x1"`
- **Subsystem**: NVIDIA Resource Manager (RM) registry parser (`os-registry.c`).
- **The "Registry Dword" Origin**: Inside NVIDIA's unified driver code, settings are designed around the Windows Registry (`HKLM\SYSTEM\CurrentControlSet\Services\nvlddmkm`). In Linux, NVIDIA built a virtual registry parser in `os-registry.c` accepting semicolon-delimited `Key=Value` strings.
- **The GSP Architecture**: In modern drivers (`nvidia-open` 610.43.03 on this machine), hardware control logic runs on an on-die RISC-V coprocessor called the **GSP (GPU System Processor)**. The Linux kernel driver is an RPC client that forwards registry overrides to the GSP firmware mailbox.
- **The Problem It Solves (The GeForce P2 Downclock)**:
  - On consumer GeForce hardware (like the RTX 3090), NVIDIA enforces an artificial memory clock drop from **P0 (maximum boost, ~19.5 Gbps GDDR6X)** to **P2 (downclocked by 200–500 MHz)** the moment a CUDA context is initialized.
  - Furthermore, transitioning between P-states takes **10–30 ms of Phase-Locked Loop (PLL) lock time**.
- **The Effect**: `OverrideMaxPerf=0x1` pins the GPU into maximum P-state permanently, bypassing the P2 CUDA downclock and eliminating frequency-scaling latency pauses between generation tokens.

### B. `nvidia.NVreg_EnableStreamMemOPs=1`
- **Subsystem**: CUDA Driver Core (`nvidia.ko` parameter `NVreg_EnableStreamMemOPs:int`).
- **Mechanism**: Enables direct hardware execution of `cuStreamWaitValue32()` and `cuStreamWriteValue32()`.
- **The Problem It Solves**: In high-speed token generation loops (vLLM, llama.cpp), the CPU orchestrates operations across multiple CUDA streams. Traditionally, stream synchronization requires host-side CPU barriers, kernel mode transitions, or interrupt-driven ringbuffer polling.
- **The Effect**: Allows GPU compute and copy engines to wait on and write to memory addresses (in host RAM or VRAM) directly inside the hardware command stream, eliminating CPU-GPU polling jitter.

### C. `nvidia.NVreg_UsePageAttributeTable=1`
- **Subsystem**: Memory management subsystem in `nvidia.ko`.
- **Mechanism**: Configures whether the driver uses x86 Page Attribute Tables (PAT) for Write-Combining (WC) caching.
- **The Problem It Solves**: CPU-to-GPU memory copies over the PCIe bus need Write-Combining to burst 64-byte cachelines. Without PAT, the driver falls back to legacy x86 MTRRs (limited to ~8 registers). When MTRRs conflict or exhaust, the driver falls back to Uncached (UC), reducing PCIe transfer bandwidth by up to 10×.
- **The Effect**: Directly sets the PAT bit in page table entries, guaranteeing maximum theoretical PCIe Gen 4 x16 throughput (~31.5 GB/s bidirectional).

---

## 3. AMD Zen 4 (Ryzen 7 8700F) CPU & Bus Tuning

### A. `rcu_nocbs=8-15` (Jitter-Free Compute Cores)
- **Linux Subsystem**: `kernel/rcu/tree_plugin.h`.
- **Mechanism**: Declares logical CPU threads 8 through 15 as "no-callback" CPUs.
- **The Effect**: Linux Read-Copy-Update (RCU) softirq processing is offloaded to background threads pinned to cores 0–7. Threads 8–15 run pure compute loops without periodic RCU softirq interrupts, eliminating frame drops and latency spikes during prompt ingestion.

### B. `pcie_aspm=off` & `pci=noaer` (Bus Responsiveness)
- **Linux Subsystem**: `drivers/pci/pcie/aspm.c`.
- **Mechanism**: Disables PCIe Active State Power Management.
- **The Effect**: Prevents the PCIe Gen 4 link from entering L0s/L1 power-saving link sleep states. Eliminates PCIe link retraining latency when dispatching CUDA kernels to the RTX 3090.

### C. `mitigations=off` (Maximum IPC)
- **Linux Subsystem**: `arch/x86/kernel/cpu/bugs.c`.
- **The Effect**: Disables speculative execution mitigations (Spectre v1/v2, Meltdown, Retbleed, BHI). Removes branch predictor barrier flushes and retpolines on Zen 4 silicon, yielding a **5% to 15% increase in compute IPC**.

### D. `processor.max_cstate=5` & `idle=mwait`
- **Linux Subsystem**: `drivers/acpi/processor_idle.c`.
- **The Effect**: Binds CPU idle states to avoid C6 package power-down sleep latency (which takes >100 µs to wake). Uses native hardware `MWAIT` for immediate thread wake-up.

### E. `amd_pstate=active` & `amd_pstate.prefcore=1`
- **The Effect**: Engages autonomous Energy Performance Preference (EPP) hardware scaling on Zen 4 and prioritizes scheduling hot threads onto the highest-frequency binned cores in the silicon die.

---

## 4. Scheduler Comparison: BORE vs. Server EEVDF

- **`vmlinuz-linux-cachyos-bore` (BORE Scheduler)**:
  - Burst-Oriented Response Enhancer.
  - Dynamically detects CPU-burst behavior: tasks that yield or sleep (like local agents, TUI editors, API servers waiting on network) are prioritized over pure number-crunchers.
  - **Verdict for Sovereign**: Prevents terminal/IDE lag when an LLM inference job maxes out CPU cores during prompt evaluation.
- **`vmlinuz-linux-cachyos-server` (Server EEVDF)**:
  - Tuned for maximum multi-threaded batch throughput across server sockets.
  - Excellent sustained compute, but higher scheduling latency variance for interactive CLI/TUI tools.
