# Milestone 1 Review Report

## Review Summary

**Verdict**: APPROVE

All requirements for Milestone 1 are successfully met. The Stable Context Size of 77,824 has been verified, the model parameters and files are correctly configured in `process-compose.yaml`, the `sovereign-engine` user systemd service is active and running, and all network verification endpoints are live and correct.

---

## Verified Claims

- **Claim 1**: Stable context size (77,824) is correctly identified and configured in `process-compose.yaml`.
  - *Verification method*: Inspected `/home/toxic/sovereign/process-compose.yaml` line 24.
  - *Result*: PASS (configured with `--ctx-size 77824`).
  
- **Claim 2**: `process-compose.yaml` contains correct model path, context size, and `--mmproj` flag.
  - *Verification method*: Inspected `/home/toxic/sovereign/process-compose.yaml` lines 12, 19, 20, 24.
  - *Result*: PASS (model path `/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf`, context size 77824, `--mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf` are all correctly set).

- **Claim 3**: systemd user service `sovereign-engine.service` is running successfully (active).
  - *Verification method*: Executed `systemctl --user status sovereign-engine.service`.
  - *Result*: PASS (reported `active (running)`).

- **Claim 4**: Endpoint `http://127.0.0.1:25001/health` is live and correct.
  - *Verification method*: Queried via `curl`.
  - *Result*: PASS (returned `{"status":"ok","slots_idle":4,"slots_processing":0}`).

- **Claim 5**: Endpoint `http://127.0.0.1:25008/v1/models` is live and correct.
  - *Verification method*: Queried via `curl`.
  - *Result*: PASS (returned model info with ID matching the Heretic GGUF path and `max_model_len` exactly matching `77824`).

- **Claim 6**: Endpoint `http://127.0.0.1:25004/api/health` is live and correct.
  - *Verification method*: Queried via `curl`.
  - *Result*: PASS (returned `{"status":"ok","version":"0.6.9"}`).

---

## Findings

### [Minor] Finding 1: Multimodal Warmup VRAM Fallback
- **What**: During multimodal CLIP warmup, the GPU failed to allocate the compute buffer (`cudaMalloc failed: out of memory`).
- **Where**: `/home/toxic/sovereign/logs/llama-server.log` (lines 277-282)
- **Why**: The GPU (RTX 3090, 24GB VRAM) was heavily loaded by the model weights (16,996 MiB) and KV cache (1,843 MiB). The server fell back to CPU for the vision warmup compute buffer allocation.
- **Suggestion**: If faster vision processing is required in the future, the layer offload count could be reduced from 60 to 58 or 59 to free up more GPU VRAM, though this will run slightly more LLM layers on CPU. Since the fallback handles it gracefully and the endpoints are fully functional, this is accepted as minor.

---

## Coverage Gaps

- **Port conflicts** — risk level: Low — recommendation: Accept risk. If port 25001, 25008, or 25004 are occupied by external processes, the stack would fail to start.
- **VRAM depletion with high slot usage** — risk level: Low/Medium — recommendation: Monitor VRAM during active multi-slot generation to ensure KV cache allocation is stable under concurrent queries.

---

## Adversarial Challenges / Stress Test

### [Medium] Challenge 1: VRAM Warmup CLIP Allocation Fallback
- **Assumption challenged**: That the RTX 3090 GPU (24GB) has sufficient VRAM to allocate CLIP image projection compute buffers completely on GPU when running 60 offloaded layers of Qwen-27B.
- **Attack scenario**: The system warmups with an image size of 1472x1472. This requires a 558.58 MiB compute buffer, which failed on CUDA0 and fell back to CPU.
- **Blast radius**: Increased latency on vision queries (multimodal CLIP encoding steps run on CPU).
- **Mitigation**: Offload slightly fewer LLM layers if vision latency is critical, or use a smaller warmup image size/config.

### [Low] Challenge 2: Context Length Splitting Across Slots
- **Assumption challenged**: That a single request can consume the full 77,824 context size.
- **Attack scenario**: Because `--parallel 4` is configured, llama-server splits the context cache equally into 4 slots, giving 19,456 tokens per slot (`n_ctx_slot=19456`). If a single user request exceeds 19,456 tokens, it will trigger context shift/out-of-context errors.
- **Blast radius**: Large single-agent context requests are limited to 19,456 tokens.
- **Mitigation**: If full 77,824 tokens are needed for a single conversation, run the llama-server with `--parallel 1` or increase the total context size.
