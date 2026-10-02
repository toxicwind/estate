# Sublinear LoRA Foundry: High-Density Multi-Adapter Serving on RTX 3090 24GB

A production-grade, zero-downtime runtime architecture for orchestrating multiple task-specialized LoRA adapters over 32B foundation models (`Qwen2.5-Coder-32B-Instruct`, `Qwen2.5-32B-Instruct`) in Q4_K_M GGUF on a single consumer GPU (NVIDIA RTX 3090 24,576 MiB).

## Summary

Serving large 32B foundation models while retaining specialized agent capabilities (e.g. surgical code refactoring, formal AST analysis, mathematical proofs) typically forces operators into full model-reloading cycles or distributed multi-GPU clusters. On fixed 24GB VRAM hardware, naive deployment triggers severe out-of-memory (OOM) failures or latency collapse when context scales beyond 8k tokens.

The **Sublinear LoRA Foundry** solves this through three unified architectural pillars:
1. **Pinned Base Model + Quantized KV-Cache**: The 32B base model is pinned in VRAM at Q4_K_M (~19.2 GiB). By deploying **Q8_0 or Q4_0 KV-cache quantization**, KV memory overhead is compressed by 47% to 72% relative to FP16, unlocking 16k–32k context horizons without exceeding the 24,576 MiB hardware ceiling.
2. **In-Flight Dynamic LoRA Hot-Swapping**: Pre-registered Low-Rank Adaptation (LoRA) matrices reside in GPU VRAM with scale 0.0. The `lora_socket_router.py` daemon dynamically activates and scales adapters on the fly in sub-10ms via `llama-server`'s `/lora-adapters` endpoint without reloading base weights.
3. **Telemetric EKG Runtime Supervision & Out-of-Band Failover**: Continuous background polling of `/slots` and `/health` tracks instantaneous generation velocity ($v_{\text{gen}}$) and context saturation ($S_{\text{ctx}}$), triggering circuit-breaker redirection to secondary local ports (`:25104`) or remote free fallbacks when performance degrades below 15 tok/s.

---

## Microarchitectural Memory Formulations on RTX 3090 (24,576 MiB)

### 1. Mathematical Breakdown of KV Cache Footprint

For a transformer architecture with $L$ layers, $n_{\text{kv\_heads}}$ key-value heads, head dimension $d_{\text{head}}$, and sequence length $S$:

$$\text{Elements per Token} = 2 \times L \times n_{\text{kv\_heads}} \times d_{\text{head}}$$

For `Qwen2.5-32B` ($L=64$, $n_{\text{kv\_heads}}=8$, $d_{\text{head}}=128$):
$$\text{Elements per Token} = 2 \times 64 \times 8 \times 128 = 131,072 \text{ elements/token}$$

The resulting VRAM footprint across quantization formats:
- **FP16 (2.00 bytes/element)**: $131,072 \times 2 = 262,144 \text{ bytes/token} = 256.0 \text{ KiB/token}$
- **Q8_0 (~1.0625 bytes/element)**: $34/32 \times 131,072 = 139,264 \text{ bytes/token} = 136.0 \text{ KiB/token}$
- **Q4_0 (~0.5625 bytes/element)**: $18/32 \times 131,072 = 73,728 \text{ bytes/token} = 72.0 \text{ KiB/token}$

#### VRAM Allocation Matrix Across Context Horizons

| Component / Layer | 8,192 Tokens | 16,384 Tokens | 32,768 Tokens | Notes / Status |
| :--- | :--- | :--- | :--- | :--- |
| **Base Model (Q4_K_M)** | 19,660 MiB | 19,660 MiB | 19,660 MiB | Pinned across 64 layers (`-ngl 99`) |
| **CUDA Context & Scratch** | 1,100 MiB | 1,100 MiB | 1,100 MiB | Activation buffers, FlashAttention-2 workspace |
| **KV Cache: FP16** | 2,048 MiB | 4,096 MiB | 8,192 MiB | **OOM at $\ge 16\text{k}$** ($19.66 + 4.10 + 1.10 = 24.86\text{ GiB}$) |
| **KV Cache: Q8_0 [Optimal]** | **1,088 MiB** | **2,176 MiB** | 4,352 MiB | **Fits 16k context with 1.64 GiB headroom** |
| **KV Cache: Q4_0 [Max Horizon]**| **576 MiB** | **1,152 MiB** | **2,304 MiB** | **Fits 32k context on single 24GB card** |
| **LoRA Adapters (4x Pinned)** | 480 MiB | 480 MiB | 480 MiB | Pre-registered rank-16/32 adapters |
| **Total VRAM (16k Q8_0 + LoRA)** | **22,328 MiB** | **23,416 MiB** | — | **Safe operating margin: 1,160 MiB headroom** |

---

## Execution Components & Directory Structure

```
skills/sublinear-lora-foundry/
├── SKILL.md                          # Comprehensive architecture & operating guide
├── scripts/
│   ├── lora_socket_router.py         # Async proxy, hot-swap manager, and EKG monitor
│   ├── llama_server_launcher.sh      # Hardware-optimized llama-server invocation script
│   └── adapter_scheduler.py          # Batch scheduling & VRAM allocation calculator
└── references/
    └── lora_manifest.json            # Dynamic adapter registry and alias mapping
```

---

## Operational Workflow

### 1. Launch Primary `llama-server`
Execute the launcher with pre-registered LoRA adapters:
```bash
bash scripts/llama_server_launcher.sh
```
Key launch invariants:
- `--cont-batching` and `--flash-attn` enabled.
- `--cache-type-k q8_0 --cache-type-v q8_0` active.
- Adapters preloaded with `--lora-scaled <path> 0.0`.

### 2. Launch the LoRA Socket Router
Start the async proxy router on port `25000`:
```bash
python3 scripts/lora_socket_router.py \
  --port 25000 \
  --primary-url http://127.0.0.1:25100 \
  --fallback-url http://127.0.0.1:25104 \
  --context-horizon 16384 \
  --min-velocity 15.0
```

### 3. Dispatch Client Requests with Dynamic LoRA Targeting
Clients send standard OpenAI-compatible requests, passing the target adapter via `model` or header:
```bash
curl -X POST http://127.0.0.1:25000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-LoRA-Adapter: coder" \
  -d '{
    "messages": [{"role": "user", "content": "Refactor AST visitor logic"}],
    "temperature": 0.2
  }'
```

---

## Telemetric EKG Invariants & Circuit Breaker Logic

The router evaluates live telemetry against strict physical bounds:
1. **Context Boundary Saturation ($S_{\text{ctx}}$)**:
   $$S_{\text{ctx}} = \frac{\Omega_{\text{ctx}}}{\Omega_{\text{horizon}}}$$
   - $S_{\text{ctx}} < 0.80$: **NOMINAL**.
   - $0.80 \le S_{\text{ctx}} < 0.88$: **SATURATED** (Advisory logging).
   - $S_{\text{ctx}} \ge 0.88$: **THRASHING** (Preemptive checkpoint warning).
2. **Instantaneous Generation Velocity ($v_{\text{gen}}$)**:
   $$v_{\text{gen}} = \frac{Y_{\text{out}}}{\Delta t}$$
   - When $v_{\text{gen}} < 15.0 \text{ tok/s}$, the router marks the engine as **STALLED** and triggers immediate failover to the fallback socket (`:25104` or remote free API).

---

## Gotchas & Operational Boundaries

- **Never use FP16 KV cache for $\ge 16\text{k}$ context on 32B models**: FP16 KV cache requires $4.1 \text{ GiB}$ at 16k tokens, guaranteeing an abrupt CUDA out-of-memory crash when desktop display servers or LoRAs allocate memory. Always enforce `q8_0` or `q4_0`.
- **Do not hot-swap LoRAs during active slot prompt ingestion**: The router verifies that `/slots` are not in `state: 1` (`PROCESSING_PROMPT`) before firing `POST /lora-adapters` to avoid corrupting KV tensors.
- **Ensure mlock is passed to llama-server**: Prevents Arch Linux/CachyOS kernel page thrashing to swap partition during heavy disk I/O.