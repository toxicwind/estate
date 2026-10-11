# sublinear-lora-foundry

[![for-the-badge](https://img.shields.io/badge/GGUF-Q4_0?style=for-the-badge)](https://gguf.all) [![for-the-badge](https://img.shields.io/badge/llama-server-LoRA?style=for-the-badge)](https://github.com/ggml-org/llama.cpp) [![for-the-badge](https://img.shields.io/badge/VRAM-24GB-caption?style=for-the-badge)](https://nvidia.com)

## sublinear-lora-foundry

Heterogeneous multi-LoRA dynamic adapter swapping, memory scheduling, and zero-downtime inference on consumer GPUs (RTX 3090 24GB). Use when orchestrating multiple specialized fine-tuned models over a single base LLM, managing VRAM pressure, eliminating timeout crashes during high-context allocation, or operating air-gapped local model routers.

### Three architectural pillars

1. **Pinned Base Model + Quantized KV-Cache**: The 32B base model is pinned in VRAM at Q4_K_M (~19.2 GiB). By deploying Q8_0 or Q4_0 KV-cache quantization, KV memory overhead is compressed by 47% to 72% relative to FP16, unlocking 16k–32k context horizons without exceeding the 24,576 MiB hardware ceiling.

2. **In-Flight Dynamic LoRA Hot-Swapping**: Pre-registered Low-Rank Adaptation (LoRA) matrices reside in GPU VRAM with scale 0.0. The `lora_socket_router.py` daemon dynamically activates and scales adapters on the fly in sub-10ms via `llama-server`'s `/lora-adapters` endpoint without reloading base weights.

3. **Telemetric EKG Runtime Supervision & Out-of-Band Failover**: Continuous background polling of `/slots` and `/health` tracks instantaneous generation velocity ($v_{\text{gen}}$) and context saturation ($S_{\text{ctx}}$), triggering circuit-breaker redirection to secondary local ports (`:25104`) or remote free fallbacks when performance degrades below 15 tok/s.

### Microarchitectural Memory Formulations on RTX 3090 (24,576 MiB)

| Component / Layer | 8,192 Tokens | 16,384 Tokens | 32,768 Tokens | Notes / Status |
|---|---|---|---|---|
| **Base Model (Q4_K_M)** | 19,660 MiB | 19,660 MiB | 19,660 MiB | Pinned across 64 layers (`-ngl 99`) |
| **CUDA Context & Scratch** | 1,100 MiB | 1,100 MiB | 1,100 MiB | Activation buffers, FlashAttention-2 workspace |
| **KV Cache: FP16** | 2,048 MiB | 4,096 MiB | 8,192 MiB | **OOM at $\ge 16\text{k}$** ($19.66 + 4.10 + 1.10 = 24.86\text{ GiB}$) |
| **KV Cache: Q8_0 [Optimal]** | **1,088 MiB** | **2,176 MiB** | 4,352 MiB | **Fits 16k context with 1.64 GiB headroom** |
| **KV Cache: Q4_0 [Max Horizon]**| **576 MiB** | **1,152 MiB** | **2,304 MiB** | **Fits 32k context on single 24GB card** |
| **LoRA Adapters (4x Pinned)** | 480 MiB | 480 MiB | 480 MiB | Pre-registered rank-16/32 adapters |
| **Total VRAM (16k Q8_0 + LoRA)** | **22,328 MiB** | **23,416 MiB** | — | **Safe operating margin: 1,160 MiB headroom** |

### Operational Workflow

1. **Launch Primary `llama-server`**: Execute `bash scripts/llama_server_launcher.sh` with pre-registered LoRA adapters. Key invariants: `--cont-batching` and `--flash-attn` enabled; `--cache-type-k q8_0 --cache-type-v q8_0` active; adapters preloaded with `--lora-scaled <path> 0.0`.

2. **Launch the LoRA Socket Router**: Start the async proxy router on port `25000`:
   ```bash
   python3 scripts/lora_socket_router.py \
     --port 25000 \
     --primary-url http://127.0.0.1:25100 \
     --fallback-url http://127.0.0.1:25104 \
     --context-horizon 16384 \
     --min-velocity 15.0
   ```

3. **Dispatch Client Requests**: Clients send standard OpenAI-compatible requests, passing the target adapter via `model` or `X-LoRA-Adapter` header:
   ```bash
   curl -X POST http://127.0.0.1:25000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "X-LoRA-Adapter: coder" \
     -d '{"messages":[{"role":"user","content":"Refactor AST visitor logic"}],"temperature":0.2}'
   ```

### Telemetric EKG Invariants & Circuit Breaker Logic

- **Context Boundary Saturation ($S_{\text{ctx}}$)**: $S_{\text{ctx}} = \frac{\Omega_{\text{ctx}}}{\Omega_{\text{horizon}}}$
  - $S_{\text{ctx}} < 0.80$: **NOMINAL**
  - $0.80 \le S_{\text{ctx}} < 0.88$: **SATURATED** (Advisory logging)
  - $S_{\text{ctx}} \ge 0.88$: **THRASHING** (Preemptive checkpoint warning)

- **Instantaneous Generation Velocity ($v_{\text{gen}}$)**: $v_{\text{gen}} = \frac{Y_{\text{out}}}{\Delta t}$
  - When $v_{\text{gen}} < 15.0 \text{ tok/s}$, the router marks the engine as **STALLED** and triggers immediate failover to the fallback socket (`:25104` or remote free API).

### Gotchas & Operational Boundaries

- **Never use FP16 KV cache for $\ge 16\text{k}$ context on 32B models**: FP16 KV cache requires $4.1 \text{ GiB}$ at 16k tokens, guaranteeing an abrupt CUDA out-of-memory crash. Always enforce `q8_0` or `q4_0`.
- **Do not hot-swap LoRAs during active slot prompt ingestion**: The router verifies that `/slots` are not in `state: 1` (`PROCESSING_PROMPT`) before firing `POST /lora-adapters` to avoid corrupting KV tensors.
- **Ensure mlock is passed to llama-server**: Prevents Arch Linux/CachyOS kernel page thrashing to swap partition during heavy disk I/O.

### Quick start (3 commands max)

```bash
# Launch llama-server with LoRA adapters
bash scripts/llama_server_launcher.sh

# Launch LoRA Socket Router
python3 scripts/lora_socket_router.py \
  --port 25000 \
  --primary-url http://127.0.0.1:25100 \
  --fallback-url http://127.0.0.1:25104 \
  --context-horizon 16384 \
  --min-velocity 15.0

# Dispatch a client request with LoRA targeting
curl -X POST http://127.0.0.1:25000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-LoRA-Adapter: coder" \
  -d '{"messages":[{"role":"user","content":"Refactor AST visitor logic"}],"temperature":0.2}'
```

### Architecture

Directory structure:
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

### Dev / contributing

- Launch invariants must be preserved: `--cont-batching`, `--flash-attn`, `--cache-type-k q8_0 --cache-type-v q8_0`, `--lora-scaled <path> 0.0`
- LoRA adapters must be pre-registered with scale 0.0 in VRAM
- EKG monitor polls `/slots` and `/health` at interval < 1s
- Adapter scheduler calculates VRAM allocation before each allocation
- All VRAM calculations validated against RTX 3090 24GB ceiling (24,576 MiB)
- Contributions must maintain zero-downtime hot-swap capability (< 10ms adapter activation)

### License

Open Claw — see `skill.toml` for details.

### Security

- Never use FP16 KV cache for $\ge 16\text{k}$ context on 32B models — guarantees abrupt CUDA OOM crash
- Do not hot-swap LoRAs during active slot prompt ingestion — avoids corrupting KV tensors
- Ensure mlock is passed to llama-server — prevents kernel page thrashing to swap
- Report shape only for secrets; never inspect values or delete SECRET entries