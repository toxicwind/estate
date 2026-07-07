# Milestone 1 Analysis Report: Context Tuning & Service Setup

## Executive Summary

This analysis details the exploration of Milestone 1 (Context Tuning & Service Setup) for the Sovereign Stack. It covers:

1. An examination of the binary search context size tuning script (`bin/test_max_ctx.py`).
2. Verification of the physical locations and properties of the required model and mmproj files.
3. A review of the current orchestration configuration (`process-compose.yaml`) and systemd unit (`sovereign-engine.service`).
4. A step-by-step strategy for the implementation agent to execute context size tuning, apply configurations, and relaunch the services.

---

## 1. Analysis of `bin/test_max_ctx.py`

The script `bin/test_max_ctx.py` is designed to run a binary search to find the highest stable context size (`ctx`) for the `llama-server` running the specified model and mmproj files on the local hardware configuration.

### Search Flow & Mechanics

1. **Process Clean-up**: At the start of each test iteration, a helper function `kill_all()` runs `pkill -9 -f llama-server` and `pkill -9 -f ollama` to guarantee no other servers occupy the VRAM.
2. **Server Startup**: The script launches the server subprocess with:
   - `-m` and `--mmproj` model paths.
   - `-c <ctx>` context size.
   - `-ngl 99` (offload all layers to GPU).
   - `-fa 1` (Flash Attention enabled).
   - `-ctk q4_0` and `-ctv q4_0` (KV cache key and value quantized to 4-bit).
   - `--host 127.0.0.1 --port 28080`.
   - `-t <CPU count>` thread count.
   - `--no-warmup` to bypass initialization latency.
3. **Readiness Verification**: The script polls the server's `/health` endpoint every second up to 30 times. If the process terminates early or the endpoint is unreachable within 30 seconds, it reports OOM/load failure.
4. **Completion Benchmarking**: A real completion request with a technical prompt (evaluating hybrid model structures and VRAM usage at high contexts) is dispatched to `/completion` with:
   - `n_predict: 100` tokens.
   - `temperature: 0.1`.
   - `timeout: 120` seconds.
     If the response contains valid text (indicated by `"content"` in the JSON payload), the test passes.
5. **Binary Search Range**:
   - Initial boundaries: `low = 4096`, `high = 131072`.
   - Initial verification check at 4096 (exits if failure).
   - Main loop computes `mid = ((low + high) // 2 // 4096) * 4096`, snapping the search midpoint to the nearest 4096-token boundary.
   - Loop converges when `low + 4096 >= high`.

---

## 2. Verification of Model and Projector Files

The model and mmproj files were verified to exist at the following exact paths:

- **Model File**:
  - **Path**: `/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf`
  - **Size**: 21,425,285,152 bytes (~20 GB)
- **Projector (mmproj) File**:
  - **Path**: `/home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf`
  - **Size**: 927,607,360 bytes (~884 MB)

These files match the constants configured in `bin/test_max_ctx.py`.

---

## 3. Configuration Review

### Current `process-compose.yaml` (Lines 10-37)

- **Model Path Configured**: Uses `/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf` (Needs update to the `Q5_K_XL` version).
- **mmproj Argument**: Missing from the command arguments (Needs addition of `--mmproj`).
- **Context Size**: Set to `--ctx-size 98304` (Needs update to the value output by the tuning script).
- **Parallel Settings**: Set to `--parallel 4` with continuous batching (`--cont-batching`).
- **Execution Binary**: Uses `/home/toxic/sovereign/bin/llama-server`, which is a symlink pointing to the verified binary `/home/toxic/ik_llama.cpp-main/build/bin/llama-server`.

### Current `sovereign-engine.service`

- **Location**: `/home/toxic/.config/systemd/user/sovereign-engine.service`
- **Lifecycle Commands**:
  - Starts the composition via `ExecStart=/usr/bin/process-compose -t=false -f /home/toxic/sovereign/process-compose.yaml -U`
  - Stops via `ExecStop=/usr/bin/process-compose -f /home/toxic/sovereign/process-compose.yaml down`
- **Status**: Currently `failed`/stopped.

---

## 4. Step-by-Step Execution Strategy

### Step 1: Context Size Search

1. Ensure no systemd services are currently hogging GPU memory:
   ```bash
   systemctl --user stop sovereign-engine.service
   ```
2. Execute the context testing script:
   ```bash
   python3 bin/test_max_ctx.py
   ```
3. Record the output value: `Highest stable context: <VALUE>` (e.g. 65536).

### Step 2: Configuration Update

1. Open `process-compose.yaml`.
2. Locate the global environment block and update the model path:
   ```yaml
   MODEL_PATH: "/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf"
   ```
3. Locate the `llama-server` process configuration block:
   - Change `-m` flag to point to the new model:
     ```yaml
     -m /home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf
     ```
   - Insert the `--mmproj` flag:
     ```yaml
     --mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf
     ```
   - Update `--ctx-size` flag with the value found in Step 1:
     ```yaml
     --ctx-size <VALUE>
     ```

### Step 3: Complete Process Cleanup

To prevent lockups or conflicting sockets, terminate any stray processes:

```bash
pkill -9 -f llama-server
pkill -9 -f process-compose
```

### Step 4: Systemd Service Relaunch

1. Reload systemd user daemon:
   ```bash
   systemctl --user daemon-reload
   ```
2. Enable the service:
   ```bash
   systemctl --user enable sovereign-engine.service
   ```
3. Start the service:
   ```bash
   systemctl --user start sovereign-engine.service
   ```

### Step 5: Verification & Diagnostics

1. Check the service status:
   ```bash
   systemctl --user status sovereign-engine.service
   ```
2. Confirm all health checks pass:
   - `curl -s http://127.0.0.1:25001/health` (should return "ok" or `{"status": "ok"}`)
   - `curl -s http://127.0.0.1:25008/v1/models` (should return the model list json)
   - `curl -s http://127.0.0.1:25004/api/health` (should return openfang's health check status)
3. Check process logs:
   - `tail -n 100 /home/toxic/sovereign/logs/llama-server.log`
   - `tail -n 100 /home/toxic/sovereign/logs/nfcot_proxy.log`
