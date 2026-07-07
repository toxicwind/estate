# Sovereign Stack Milestone 1 Analysis — Context Tuning & Service Setup

## Executive Summary

This analysis details the investigation of Milestone 1 (Context Tuning & Service Setup) for the Sovereign Stack. Through direct execution of the context search script and auditing of existing configuration files, we have determined the optimal service configurations.

The primary finding is that the target model **`heretic-UD-27B-Q5_K_XL.gguf`** with vision projector **`mmproj-27B-F16.gguf`** successfully runs on the host RTX 3090 GPU (24GB VRAM) with a maximum stable context size of **73,728 tokens** using `q4_0` KV cache quantization and Flash Attention. The current production configuration in `process-compose.yaml` utilizes an outdated model and incorrect context size limits, requiring update and migration.

---

## 1. Context Size Search Methodology (`bin/test_max_ctx.py`)

The context tuning script `bin/test_max_ctx.py` automates the identification of the maximum context size that the hardware can support without triggering an Out-of-Memory (OOM) error or causing inference failures.

### Execution Flow

1. **Process Cleanup (`kill_all`)**: Before each test iteration, the script forcefully terminates any running instances of `llama-server` and `ollama` (`pkill -9 -f`) to free up GPU memory.
2. **Server Spawning**: The `llama-server` is started as a subprocess with:
   - `-m`: The target model (`heretic-UD-27B-Q5_K_XL.gguf`).
   - `--mmproj`: The vision projector (`mmproj-27B-F16.gguf`).
   - `-c`: The test context size (in tokens).
   - `-ngl 99`: Offloads all 64 layers of the Qwen3.6 27B model to the GPU.
   - `-fa 1`: Enables Flash Attention for reduced VRAM scaling.
   - `-ctk q4_0` & `-ctv q4_0`: Quantizes KV cache keys and values to 4-bit, saving ~72% VRAM over float16 cache.
   - `--host 127.0.0.1 --port 28080 --no-warmup`.
3. **Health Polling**: The script polls the server's `/health` endpoint for up to 30 seconds. If the endpoint is unresponsive, it reads the server's stdout/stderr. If `cudaMalloc failed` or `out of memory` is detected, it returns an "OOM on load" failure.
4. **Verification via Inference**: If the server starts successfully, the script sends a HTTP POST to `/completion` with a 100-token generation request (`n_predict: 100`) using `BENCH_PROMPT`. If the server responds with a valid JSON completion, the test is marked as successful.
5. **Binary Search**:
   - Initial bounds: `low = 4,096`, `high = 131,072`.
   - Iteration steps by multiples of `4,096` tokens.
   - If the test succeeds, `low` is updated to `mid`. If it fails (due to load OOM or inference timeout/error), `high` is updated to `mid`.
   - The loop terminates when `low + 4096 >= high`.

### Test Execution Results

The background run of `/home/toxic/sovereign/bin/test_max_ctx.py` produced the following log:

```
=== Max Context Search ===
>>> ctx=4,096
4k: ok

>>> ctx=65,536
65,536: ok

>>> ctx=98,304
98,304: OOM on load

>>> ctx=81,920
81,920: invalid response

>>> ctx=73,728
73,728: ok

>>> ctx=77,824
77,824: invalid response

Highest stable context: 73,728
```

- **Conclusion**: **73,728 tokens** is the maximum context size that can be safely loaded and queried under the target configuration.

---

## 2. Model & Projector Location Verification

We verified that the files required for the new model setup exist and are correctly situated in the model directory:

- **Model Directory**: `/home/toxic/models/Qwen3.6-27B-Heretic-UD/`
- **Model File**:
  - Path: `/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf`
  - Size: `21,425,285,152 bytes` (~20.0 GB)
- **Vision Projector (mmproj) File**:
  - Path: `/home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf`
  - Size: `927,607,360 bytes` (~884.6 MB)

Combined, these files occupy **~20.9 GB** of disk/VRAM space, which fits within the RTX 3090's 24 GB VRAM ceiling, provided KV cache is quantized.

---

## 3. Configuration Audits

### 3.1. Process-Compose Configuration (`process-compose.yaml`)

The file `/home/toxic/sovereign/process-compose.yaml` orchestrates the stack services (llama-server, nfcot_proxy, openfang, watchdog, yote_telegram, yote_daemon).

The `llama-server` process configuration shows the following parameters:

- **Model**: `/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf` (**Mismatch**: Pointing to the old Q2 quantized model rather than the new Q5_K_XL model).
- **Vision Projector**: None configured (**Mismatch**: `--mmproj` is missing entirely).
- **Context Size**: `--ctx-size 98304` (**Mismatch**: The Q5_K_XL model OOMs at 98,304 tokens; it must be updated).
- **Cache Quantization**: `--cache-type-k q4_0 --cache-type-v q4_0` (Matches optimal setup).
- **Parallelism**: `--parallel 4` (This configures 4 parallel execution slots, which divides the KV cache size, but the total VRAM allocation is bounded by `--ctx-size`).

### 3.2. Systemd Service Configuration (`sovereign-engine.service`)

The systemd user unit `/home/toxic/.config/systemd/user/sovereign-engine.service` defines the background lifecycle of the stack:

- **ExecStart**: `/usr/bin/process-compose -t=false -f /home/toxic/sovereign/process-compose.yaml -U`
  - Runs process-compose headlessly (`-t=false`) using the specified yaml configuration and enables the Unix domain socket interface (`-U`).
- **ExecStop**: `/usr/bin/process-compose -f /home/toxic/sovereign/process-compose.yaml down`
  - Stops the running services gracefully.
- **Restart / Resiliency**: Configured with `Restart=on-failure` and a 5-second backoff (`RestartSec=5`).

---

## 4. Step-by-Step Migration and Deployment Strategy

To apply the context tuning results and upgrade the Sovereign Stack to the new model without service interruption, follow these instructions step-by-step:

### Step 1: Stop the Running Sovereign Service

Cleanly stop the existing systemd user service to release all active VRAM allocations.

```bash
systemctl --user stop sovereign-engine.service
```

### Step 2: Update `process-compose.yaml`

Modify the `llama-server` configuration in `/home/toxic/sovereign/process-compose.yaml` to point to the new model, add the vision projector, and adjust the context size.

**Proposed Changes:**

1. Under `environment:`, change `MODEL_PATH`:
   ```yaml
   - "MODEL_PATH=/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf"
   ```
2. Under `processes.llama-server.command`, modify:
   - `-m` path to match the new model path.
   - Add the `--mmproj` parameter pointing to the vision projector.
   - Change `--ctx-size` to `73728`.

**Command Section Before Update:**

```yaml
command: >-
  /home/toxic/sovereign/bin/llama-server
  -m /home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf
  --host 0.0.0.0 --port 25001
  --jinja
  --n-gpu-layers 99
  --ctx-size 98304
...
```

**Command Section After Update:**

```yaml
command: >-
  /home/toxic/sovereign/bin/llama-server
  -m /home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf
  --mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf
  --host 0.0.0.0 --port 25001
  --jinja
  --n-gpu-layers 99
  --ctx-size 73728
...
```

### Step 3: Reload Systemd User Daemon

Tell systemd to reload its configuration files so that any changes to the service file (if modified) are registered.

```bash
systemctl --user daemon-reload
```

### Step 4: Restart and Enable the Service

Start the engine service and enable it to persist across user logins.

```bash
systemctl --user enable sovereign-engine.service
systemctl --user start sovereign-engine.service
```

### Step 5: Verification and Monitoring

Confirm that the service is running and all sub-processes initialized healthy.

1. **Check Systemd Status**:
   ```bash
   systemctl --user status sovereign-engine.service
   ```
2. **Check Process-Compose Output**:
   Check the process logs to ensure llama-server, nfcot_proxy, openfang, and other dependent tasks are reported as healthy:

   ```bash
   # View process-compose orchestrator logs
   tail -n 100 /home/toxic/sovereign/logs/process-compose.log

   # View llama-server initialization logs
   tail -n 100 /home/toxic/sovereign/logs/llama-server.log
   ```

3. **Verify API Endpoints**:
   Test the readiness of the primary LLM server:
   ```bash
   curl -s http://127.0.0.1:25001/health
   ```
   A response of `{"status": "ok"}` indicates a successful deployment.
