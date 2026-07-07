# Handoff Report: Milestone 1 (Context Tuning & Service Setup)

## 1. Observation

- **Model Files**:
  - Model file `heretic-UD-27B-Q5_K_XL.gguf` (size `21425285152` bytes) and projector `mmproj-27B-F16.gguf` (size `927607360` bytes) exist in `/home/toxic/models/Qwen3.6-27B-Heretic-UD/`.
- **Search Script (`bin/test_max_ctx.py`)**:
  - Line 17–19 defines target files:
    ```python
    MODEL = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "heretic-UD-27B-Q5_K_XL.gguf"
    MMPROJ = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "mmproj-27B-F16.gguf"
    SERVER = HOME / "ik_llama.cpp-main" / "build" / "bin" / "llama-server"
    ```
  - It runs a binary search (Lines 112-137) over context sizes between 4,096 and 131,072.
  - Launches `llama-server` (Lines 39-52) with `-ngl 99`, `-fa 1`, `-ctk q4_0`, `-ctv q4_0` (which matches `q4_0` KV cache settings) and checks `/health` via `curl` (Line 64) followed by `/completion` benchmark query (Line 86) using `curl`.
- **Process Compose Config (`process-compose.yaml`)**:
  - Line 12 defines environment legacy path:
    ```yaml
    - "MODEL_PATH=/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf"
    ```
  - Line 19–24 defines `llama-server` process settings:
    ```yaml
    -m /home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf
    --host 0.0.0.0 --port 25001
    --jinja
    --n-gpu-layers 99
    --ctx-size 98304
    --cache-type-k q4_0 --cache-type-v q4_0
    ```
    No `--mmproj` flag is set.
- **Systemd User Service (`/home/toxic/.config/systemd/user/sovereign-engine.service`)**:
  - Configured to execute:
    ```ini
    ExecStart=/usr/bin/process-compose -t=false -f /home/toxic/sovereign/process-compose.yaml -U
    ```
  - Active state is currently `failed`.
- **GPU Resource**:
  - System has a single `NVIDIA GeForce RTX 3090` with `24101 MiB` total VRAM; current baseline VRAM usage is `1494MiB`.

## 2. Logic Chain

1. The new model `heretic-UD-27B-Q5_K_XL.gguf` requires `mmproj-27B-F16.gguf` to boot (verified by model definitions and `bin/test_max_ctx.py`).
2. Current `process-compose.yaml` points to a legacy model (`Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf`) and does not specify `--mmproj`.
3. Running `process-compose` with the legacy config will load the wrong model and fail to enable vision capabilities.
4. Running the context tuning script (`bin/test_max_ctx.py`) first is necessary to determine the maximum stable context length under the new model setup with `q4_0` KV Cache.
5. Updating `process-compose.yaml` with the correct model, projector, and tuned context size, and restarting/enabling the systemd service completes the Milestone 1 configuration.

## 3. Caveats

- Did not run the context search script directly because the role is read-only explorer and systemd service needs to be stopped first.
- Assumed `q4_0` KV cache settings are required based on `bin/test_max_ctx.py` and current config.
- Assumed standard user systemd command constraints apply.

## 4. Conclusion

The legacy configs must be updated with the newly verified path of `heretic-UD-27B-Q5_K_XL.gguf` and its projector `mmproj-27B-F16.gguf`. A step-by-step strategy has been formulated for the implementer agent to execute the search, edit `process-compose.yaml`, and restart/enable the `sovereign-engine.service` systemd service.

## 5. Verification Method

1. **Model Files**: Verify paths manually:
   `ls -la /home/toxic/models/Qwen3.6-27B-Heretic-UD/`
2. **Context Tuning Execution**: Run `python3 bin/test_max_ctx.py` and inspect logs.
3. **Config Patching**: Inspect `/home/toxic/sovereign/process-compose.yaml` to verify the model path, mmproj flag, and context size.
4. **Service Health**: Verify systemd status:
   `systemctl --user status sovereign-engine.service`
   Verify API response:
   `curl -s http://127.0.0.1:25008/health`

## Remaining Work (For Implementer)

- Stop the `sovereign-engine` user service.
- Execute the context tuning script `bin/test_max_ctx.py`.
- Patch `/home/toxic/sovereign/process-compose.yaml` as per the diff in `analysis.md`.
- Start and enable the systemd service.
- Enable user linger (`loginctl enable-linger toxic`).
