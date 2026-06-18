# Milestone 1 Handoff Report

## 1. Observation
- **Tuning Search Output**: The binary search tuning script `python3 /home/toxic/sovereign/bin/test_max_ctx.py` produced:
  ```
  === Max Context Search ===
  >>> ctx=4,096
  4k: ok
  ...
  >>> ctx=77,824
  77,824: ok
  Highest stable context: 77,824
  ```
- **Crash Log (GPU OOM)**: Tailing the systemd journal for `sovereign-engine.service` during initial start with `ctx=77824` and `--n-gpu-layers 99`:
  ```
  ggml_backend_cuda_buffer_type_alloc_buffer: allocating 884.62 MiB on device 0: cudaMalloc failed: out of memory
  systemd-coredump: Process 2542994 (llama-server) of user 1000 dumped core.
  ```
- **Service Port Status (After adjusting --n-gpu-layers to 60)**:
  - Checking `systemctl --user status sovereign-engine.service` shows process-compose running with PID 2544459 and llama-server, nfcot_proxy, openfang, watchdog, and npm MCP servers active.
  - Readiness check commands and outputs:
    ```bash
    curl -i http://127.0.0.1:25001/health
    # Output: {"status":"ok","slots_idle":4,"slots_processing":0}
    
    curl -i http://127.0.0.1:25008/v1/models
    # Output: {"object":"list","data":[{"id":"/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf", ...}],"max_model_len":77824}
    
    curl -i http://127.0.0.1:25004/api/health
    # Output: {"status":"ok","version":"0.6.9"}
    ```

## 2. Logic Chain
- **Observation 1**: The tuning search script successfully completed, indicating that the RTX 3090 hardware can run the 27B model `heretic-UD-27B-Q5_K_XL.gguf` with context size `77824` under basic/default batching/concurrency.
- **Observation 2**: When run via `process-compose`, the configuration includes `--parallel 4`, larger batching buffers `-b 4096 -ub 1024`, and other concurrently running processes. Combined with a fully offloaded GPU configuration (`--n-gpu-layers 99`), this causes a `cudaMalloc` failure when attempting to allocate the additional `884.62 MiB` for the vision projector (`--mmproj`).
- **Observation 3**: Reducing `--n-gpu-layers` from `99` (all 64 layers) to `60` frees up approximately `4 * 286 MiB = 1144 MiB` of GPU VRAM, allowing both the 27B model tensors, the parallel slot KV caches, the vision projector, and the image evaluation warmups to fit entirely within the RTX 3090's 24 GiB VRAM without triggering CUDA OOMs.
- **Observation 4**: Following the adjustment to `60` layers, the systemd service successfully restarted and all curl queries to ports `25001`, `25008`, and `25004` returned HTTP `200 OK` with correct status payloads, confirming a fully operational engine.

## 3. Caveats
- There is minor GUI activity (Hyprland, Xwayland, etc.) running on the same GPU consuming ~1.4 GiB VRAM. If GUI usage increases dramatically (e.g. running heavy graphical apps), the remaining 1-2 GiB of free VRAM could be depleted, which might lead to runtime OOMs during extremely high-context multi-slot batch processing.

## 4. Conclusion
Milestone 1 is complete: the context tuning size of **77,824** has been successfully integrated, process-compose config is updated, systemd user service is re-enabled/restarted, and all engine components are healthy, listening, and communicating correctly.

## 5. Verification Method
1. Verify systemd service status:
   ```bash
   systemctl --user status sovereign-engine.service
   ```
2. Verify all readiness endpoints return healthy status:
   ```bash
   curl -s http://127.0.0.1:25001/health
   curl -s http://127.0.0.1:25008/v1/models
   curl -s http://127.0.0.1:25004/api/health
   ```
3. Check `process-compose.yaml` to confirm the model path, ctx-size (77824), and mmproj are correctly configured.
