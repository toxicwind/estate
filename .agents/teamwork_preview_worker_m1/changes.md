# Implementation Changes and Execution Log - Milestone 1

## Summary of Actions

1. **GPU Memory Cleanup**: Checked and stopped `sovereign-engine.service` and ensured no other background instances of `llama-server` or `ollama` were using GPU VRAM.
2. **Context Size Tuning Search**: Ran the binary search script `python3 /home/toxic/sovereign/bin/test_max_ctx.py` in the background (task-74).
3. **Capture stable context**: Extracted the highest stable context value from the tuning search: **77,824**.
4. **Configuration Update**:
   - Updated `/home/toxic/sovereign/process-compose.yaml`.
   - Changed model path to `/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf` for environment variable `MODEL_PATH` and llama-server argument `-m`.
   - Set `--ctx-size` under the `llama-server` process configuration to `77824`.
   - Added `--mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf`.
   - Optimized `--n-gpu-layers` to `60` (from `99`) to prevent GPU OOM crash during llama-server multimodal projector loading and image warmup evaluation under process-compose's multi-slot configuration.
5. **Service Management**:
   - Reloaded systemd daemon: `systemctl --user daemon-reload`.
   - Enabled user service: `systemctl --user enable sovereign-engine.service`.
   - Restarted user service: `systemctl --user restart sovereign-engine.service`.
6. **Health and Connectivity Verification**: Verified status and successfully queried all three readiness endpoints.

## Configuration Diff for `process-compose.yaml`

```diff
 environment:
   - "SOVEREIGN_HOME=/home/toxic/sovereign"
-  - "MODEL_PATH=/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf"
+  - "MODEL_PATH=/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf"
   - "PYTHONUNBUFFERED=1"

 processes:
   llama-server:
     command: >-
       /home/toxic/sovereign/bin/llama-server
-      -m /home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf
+      -m /home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf
+      --mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf
       --host 0.0.0.0 --port 25001
       --jinja
-      --n-gpu-layers 99
-      --ctx-size 98304
+      --n-gpu-layers 60
+      --ctx-size 77824
```

## Readiness Curl Outputs

- **Port 25001 (`/health`)**:
  ```json
  { "status": "ok", "slots_idle": 4, "slots_processing": 0 }
  ```
- **Port 25008 (`/v1/models`)**:
  ```json
  {
    "object": "list",
    "data": [
      {
        "id": "/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf",
        "object": "model",
        "created": 1781805634,
        "owned_by": "llamacpp",
        "meta": {
          "vocab_type": 2,
          "n_vocab": 248320,
          "n_ctx_train": 262144,
          "n_embd": 5120,
          "n_params": 26895998464,
          "size": 21414291456
        },
        "max_model_len": 77824
      }
    ]
  }
  ```
- **Port 25004 (`/api/health`)**:
  ```json
  { "status": "ok", "version": "0.6.9" }
  ```
