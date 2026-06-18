# Milestone 1: Context Tuning & Service Setup Analysis

## Core Summary
The Sovereign Stack is transitioning from the legacy `Qwen3.6-27B-Heretic-Cerebellum` model to the newer `Qwen3.6-27B-Heretic-UD` model, which requires incorporating an `mmproj` vision component. The current configuration files contain legacy path references, missing parameters, and incorrect context limits, which can be resolved by executing the context search scripts and applying targeted configuration patches.

---

## 1. Analysis of `bin/test_max_ctx.py`
The `bin/test_max_ctx.py` script conducts an automated search for the maximum stable context length of the model on the host GPU.

### How the Context Search is Conducted
The script uses a **binary search algorithm** to find the threshold context size:
- **Range Boundary**: It starts with a lower bound `low = 4096` and an upper bound `high = 131072`.
- **Search Iteration**: At each step, it computes the mid-point rounded down to the nearest multiple of 4,096:
  $$\text{mid} = \left\lfloor \frac{\text{low} + \text{high}}{2 \times 4096} \right\rfloor \times 4096$$
- **Step Evaluation**: It invokes `test_ctx(mid)` and updates the search bounds:
  - If successful: `low = mid`, updating `best = mid`.
  - If it fails (due to OOM or startup timeout): `high = mid`.
  - The loop continues until the search interval shrinks below 4,096 tokens (`low + 4096 < high`).
- **Initial Verification**: Before starting the search, it validates a baseline context of 4,096 tokens. If this fails, the script aborts immediately.

### Context Size Test (`test_ctx` function)
For each test candidate size, the function:
1. **Frees VRAM**: Kills any active `llama-server` and `ollama` processes (`kill_all`) to ensure no memory contention.
2. **Launches Server**: Starts `llama-server` in the background with `subprocess.Popen` using specific parameters:
   - `-m` (Model path: `/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf`)
   - `--mmproj` (Vision projector: `/home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf`)
   - `-c` (Context size candidate)
   - `-ngl 99` (GPU offload layers - offloads all layers)
   - `-fa 1` (Flash Attention enabled)
   - `-ctk q4_0` / `-ctv q4_0` (Key/Value cache quantized to 4-bit)
   - `--no-warmup` (Skip KV cache allocation pre-fill at load)
3. **Health Checking**: Polls the endpoint `http://127.0.0.1:28080/health` every second for up to 30 seconds.
   - If the server fails to launch, the script checks the stderr/stdout for memory allocation failure messages (`cudaMalloc failed` or `out of memory`).
4. **Completion Test**: Once the health check succeeds, it sends a POST request using `curl` to `http://127.0.0.1:28080/completion` with `n_predict: 100` and a long technical prompt.
   - If the request returns valid JSON containing `"content"` within the timeout, the test is marked successful (`True`); otherwise, it is marked failed (`False`).

*Note: In the same directory, there is an even more comprehensive script, `bin/ultimate_max_ctx_v8.py`, which performs binary searches across three KV cache quantization settings (`q4_0`, `q8_0`, `f16`), queries the system VRAM dynamically using `nvidia-smi`, and saves results in JSON format.*

---

## 2. Model & Projector Verification
The existence, paths, and metadata of the targeted model files have been verified:

| Component | Verified Path | Size (Bytes) | Size (GB) |
|---|---|---|---|
| **Model (GGUF)** | `/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf` | `21,425,285,152` | ~21.4 GB |
| **Projector (MMPROJ)** | `/home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf` | `927,607,360` | ~0.93 GB |

*Verification Command:* `ls -la /home/toxic/models/Qwen3.6-27B-Heretic-UD/`

---

## 3. Configuration Review & Gaps
A thorough review of `process-compose.yaml` and the systemd service file was conducted.

### 1. `process-compose.yaml` Gaps
- **Model Path Mismatch**: Line 12 (`MODEL_PATH`) and Line 19 (`-m` flag in `llama-server`) point to a legacy model `/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf` instead of the newly targeted `Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf`.
- **Missing Projector flag**: The `llama-server` command in `process-compose.yaml` does not specify the `--mmproj` flag, which is mandatory for loading vision capability for `heretic-UD-27B-Q5_K_XL.gguf`.
- **Untuned Context Size**: The `--ctx-size` is hardcoded to `98304` (Line 23), which may be suboptimal or unstable compared to the dynamically searched threshold.

### 2. systemd User Service (`/home/toxic/.config/systemd/user/sovereign-engine.service`)
The user service is configured correctly to run `process-compose` non-interactively:
```ini
ExecStart=/usr/bin/process-compose -t=false -f /home/toxic/sovereign/process-compose.yaml -U
ExecStop=/usr/bin/process-compose -f /home/toxic/sovereign/process-compose.yaml down
```
- **Current Status**: The service was found in a `failed` (inactive) state due to a failure during `process-compose ... down` in the previous session.

---

## 4. Proposed Configuration Changes (Diff Patch)

The following modifications should be applied to `/home/toxic/sovereign/process-compose.yaml` once the tuned context size is determined:

```diff
--- process-compose.yaml
+++ process-compose.yaml
@@ -10,3 +10,3 @@
 environment:
   - "SOVEREIGN_HOME=/home/toxic/sovereign"
-  - "MODEL_PATH=/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf"
+  - "MODEL_PATH=/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf"
   - "PYTHONUNBUFFERED=1"
@@ -17,3 +17,4 @@
     command: >-
       /home/toxic/sovereign/bin/llama-server
-      -m /home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf
+      -m /home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf
+      --mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf
       --host 0.0.0.0 --port 25001
       --jinja
       --n-gpu-layers 99
-      --ctx-size 98304
+      --ctx-size <TUNED_CONTEXT_SIZE>
       --cache-type-k q4_0 --cache-type-v q4_0
```

---

## 5. Execution Strategy for Implementer (Step-by-Step)

The implementer should execute the following sequence to safely determine the context size, update configurations, and deploy the persistent systemd service:

### Step 1: Pre-run Cleanup
Ensure no running engine processes interfere with the tuning benchmark:
```bash
systemctl --user stop sovereign-engine.service
pkill -9 -f llama-server
pkill -9 -f process-compose
```

### Step 2: Run Context Size Search
Run the context size testing script and monitor output:
```bash
python3 /home/toxic/sovereign/bin/test_max_ctx.py
```
*(Alternatively, execute `python3 bin/ultimate_max_ctx_v8.py` to test q4_0 KV cache limits and obtain a detailed JSON metric report).*
Record the printed **Highest stable context** value (e.g. `118784`, `122880`, etc.).

### Step 3: Apply Configuration Updates
1. Edit `/home/toxic/sovereign/process-compose.yaml` to update the model paths, add the `--mmproj` flag, and insert the tuned context size.
2. If necessary, update other utility scripts like `v.sh`, `dep.sh`, or `mise.toml` to replace the hardcoded Cerebellum model paths with the new UD model path for consistency.

### Step 4: Restart & Enable systemd User Service
Run the systemd user commands to reload unit configurations, start the engine service, and enable startup persistence:
```bash
# Force systemd user manager to load any changes to the unit file
systemctl --user daemon-reload

# Enable the service so it starts automatically on user login
systemctl --user enable sovereign-engine.service

# Start the service
systemctl --user restart sovereign-engine.service
```

### Step 5: Verify Deployment
Verify that all processes inside process-compose are running and healthy:
```bash
# Check systemd status
systemctl --user status sovereign-engine.service

# Check proxy health
curl -s http://127.0.0.1:25008/health | jq
```
Check the logs at `/home/toxic/sovereign/logs/llama-server.log` to confirm the correct model, projector, and context size were loaded successfully.
Ensure system linger is enabled for user `toxic` so the user manager persists across sessions:
```bash
loginctl enable-linger toxic
```
