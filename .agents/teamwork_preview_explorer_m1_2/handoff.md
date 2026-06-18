# Handoff Report - Milestone 1 Context Tuning & Service Setup

## 1. Observation
- **Context Search Script Output**:
  - Run Command: `python3 /home/toxic/sovereign/bin/test_max_ctx.py`
  - Output verbatim:
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
- **Model Files Existence**:
  - Listed Directory: `/home/toxic/models/Qwen3.6-27B-Heretic-UD`
  - Output details:
    - `"name":"heretic-UD-27B-Q5_K_XL.gguf","sizeBytes":"21425285152"` (20.0 GB)
    - `"name":"mmproj-27B-F16.gguf","sizeBytes":"927607360"` (884.6 MB)
- **Current `process-compose.yaml` (Lines 11-23)**:
  ```yaml
  environment:
    - "SOVEREIGN_HOME=/home/toxic/sovereign"
    - "MODEL_PATH=/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf"
    - "PYTHONUNBUFFERED=1"

  processes:
    llama-server:
      command: >-
        /home/toxic/sovereign/bin/llama-server
        -m /home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf
        --host 0.0.0.0 --port 25001
        --jinja
        --n-gpu-layers 99
        --ctx-size 98304
  ```
- **Current `sovereign-engine.service` (Lines 5-11)**:
  ```ini
  [Service]
  Type=simple
  WorkingDirectory=/home/toxic/sovereign
  ExecStart=/usr/bin/process-compose -t=false -f /home/toxic/sovereign/process-compose.yaml -U
  ExecStop=/usr/bin/process-compose -f /home/toxic/sovereign/process-compose.yaml down
  Restart=on-failure
  RestartSec=5
  ```

---

## 2. Logic Chain
1. Based on the **Context Search Script Output**, testing context sizes above 73,728 results in failure (`81,920` returns `invalid response` or server errors; `98,304` results in `OOM on load`), while context size `73,728` successfully passes both initialization and inference tests.
2. Based on the **Model Files Existence** check, the target model `heretic-UD-27B-Q5_K_XL.gguf` and its vision projector `mmproj-27B-F16.gguf` exist at `/home/toxic/models/Qwen3.6-27B-Heretic-UD/`.
3. Based on the **Current `process-compose.yaml`**, the service is currently using an older model (`Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf`) with context size set to `98,304` and lacks the `--mmproj` projector argument.
4. If the model is upgraded to `heretic-UD-27B-Q5_K_XL.gguf` under the current `process-compose.yaml` settings without reducing `--ctx-size` and adding `--mmproj`, the system will crash during startup due to OOM at `98,304` context size, and will not load vision functionality.
5. Therefore, a migration is required to update the configuration to model `heretic-UD-27B-Q5_K_XL.gguf`, add `--mmproj`, change the context size to `73728`, reload systemd configuration, and restart the service.

---

## 3. Caveats
- The maximum stable context size of 73,728 was determined using a single execution thread with no concurrency (`--parallel 1` implicitly in `test_max_ctx.py`). The production `process-compose.yaml` specifies `--parallel 4`. If the actual system allocates separate KV cache slots per parallel client, running with `--parallel 4` at `73728` context size might still cause OOM. However, `llama-server` sharing mechanics usually split the overall cache. If VRAM issues persist post-update, reducing `--parallel` or decreasing `--ctx-size` to `65,536` are the recommended fallbacks.
- VRAM allocation was tested while the host GPU has ~1.4 GB occupied by system/GUI tasks. If background VRAM usage spikes, the stable threshold may shift.

---

## 4. Conclusion
The maximum stable context size for the upgraded model config (`heretic-UD-27B-Q5_K_XL.gguf` + `mmproj-27B-F16.gguf`) is **73,728 tokens**. To deploy this:
1. Stop the `sovereign-engine.service` systemd unit.
2. Edit `/home/toxic/sovereign/process-compose.yaml` to point `MODEL_PATH` and `llama-server -m` to `/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf`.
3. Add `--mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf` to the `llama-server` arguments list.
4. Reduce `--ctx-size` from `98304` to `73728`.
5. Run `systemctl --user daemon-reload`, then enable and restart `sovereign-engine.service`.

---

## 5. Verification Method
1. **Apply Configuration Edits**: Make the proposed edits in `/home/toxic/sovereign/process-compose.yaml`.
2. **Execute Deployment Commands**:
   ```bash
   systemctl --user stop sovereign-engine.service
   systemctl --user daemon-reload
   systemctl --user start sovereign-engine.service
   ```
3. **Verify Service Health**:
   - Check service status: `systemctl --user status sovereign-engine.service`
   - Check llama-server readiness: `curl -s http://127.0.0.1:25001/health` (should respond with `{"status": "ok"}`)
   - Check process health via logs: `tail -n 50 /home/toxic/sovereign/logs/llama-server.log`
4. **Invalidation Conditions**:
   - If `llama-server.log` reports `cudaMalloc failed` or `out of memory` at startup, the context size must be reduced to `65,536` or `49,152`.
   - If the curl health check fails to return `ok` within 60 seconds, check the systemd journal logs via `journalctl --user -u sovereign-engine.service -n 50`.
