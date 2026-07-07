# Handoff Report: Milestone 1 Exploration

This handoff details the analysis of the Context Tuning & Service Setup tasks for the Sovereign Stack.

## 1. Observation

- **Context Tuning Script Location & Definition**: The script is located at `/home/toxic/sovereign/bin/test_max_ctx.py`.
  - It defines model and backend paths on lines 16-19:
    ```python
    HOME = pathlib.Path("/home/toxic")
    MODEL = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "heretic-UD-27B-Q5_K_XL.gguf"
    MMPROJ = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "mmproj-27B-F16.gguf"
    SERVER = HOME / "ik_llama.cpp-main" / "build" / "bin" / "llama-server"
    ```
  - It runs a binary search with initial boundaries specified on lines 112-113:
    ```python
    low = 4096
    high = 131072
    ```
  - Step size logic on lines 126-127:
    ```python
    while low + 4096 < high:
        mid = ((low + high) // 2 // 4096) * 4096
    ```
  - Verification payload uses a POST query to `http://127.0.0.1:28080/completion` with:
    ```json
    {"prompt": ..., "n_predict": 100, "temperature": 0.1}
    ```
- **Model and Projector Path Verification**:
  - Verification via `list_dir` on `/home/toxic/models/Qwen3.6-27B-Heretic-UD` returned:
    - `"heretic-UD-27B-Q5_K_XL.gguf" (sizeBytes: "21425285152")`
    - `"mmproj-27B-F16.gguf" (sizeBytes: "927607360")`
- **Process Orchestration Configuration**:
  - Config file is at `/home/toxic/sovereign/process-compose.yaml`.
  - Current configuration uses different model name:
    ```yaml
    MODEL_PATH=/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf
    ```
  - Under `llama-server` process, the command uses `-m /home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf`, `--ctx-size 98304` and does not include `--mmproj` (Lines 18-37).
  - Executable `/home/toxic/sovereign/bin/llama-server` is a symlink:
    ```
    /home/toxic/sovereign/bin/llama-server -> /home/toxic/ik_llama.cpp-main/build/bin/llama-server
    ```
- **Systemd Service Unit**:
  - Config file: `/home/toxic/.config/systemd/user/sovereign-engine.service`.
  - Currently failed/inactive (exit code 3 from `systemctl --user status sovereign-engine`).

## 2. Logic Chain

1. Since the `test_max_ctx.py` uses hardcoded path constants to `heretic-UD-27B-Q5_K_XL.gguf` and `mmproj-27B-F16.gguf`, and since these files are verified to be present under `/home/toxic/models/Qwen3.6-27B-Heretic-UD/`, the search script will run targeting the correct new weights.
2. Because the current `process-compose.yaml` specifies an older Cerebellum model (`Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf`) and does not specify `--mmproj`, it must be edited to reference the new model path and projector path to launch correctly.
3. Since the production service uses `--parallel 4`, which spawns 4 parallel slots in llama.cpp, while the tuning script `test_max_ctx.py` performs tests under single-slot (sequential) conditions without `--parallel`, we must plan for potential VRAM usage discrepancies between search results and deployment configurations.
4. Systemd service execution executes `/usr/bin/process-compose` pointing to `process-compose.yaml`, so modifying `process-compose.yaml` and running `systemctl --user restart sovereign-engine` is the exact command sequence required to apply these tuning changes.

## 3. Caveats

- **Single vs Parallel Context limits**: `test_max_ctx.py` executes `llama-server` in single-request mode. Under production load with `--parallel 4`, multiple slots will allocate parallel context slots which might lead to OOM errors even if the tested context size passes under single-slot conditions.
- **Warmup bypass**: The script uses `--no-warmup`. The actual runtime memory usage might slightly differ when deep prompt sharing or KV cache allocation occurs during actual traffic.
- **Hardware limits**: We assume no other resource-intensive GPU operations are running simultaneously. If another program consumes VRAM during binary search, the calculated limit will be artificially lowered.

## 4. Conclusion

Milestone 1 is ready for implementation by the implementer agent. A binary search tuning script is available and correctly configured for the new `Q5_K_XL` model and projector. The service setup uses a process-compose orchestration suite controlled by a systemd user unit. Applying the results of the tuning run and updating the YAML model path, adding the `--mmproj` flag, and restarting the service will satisfy all Milestone 1 goals.

## 5. Verification Method

1. **Executing the tuning run**: Run `python3 bin/test_max_ctx.py` and ensure the script runs to completion, outputting the `Highest stable context: <VALUE>`.
2. **Checking configuration values**: Inspect `process-compose.yaml` post-edit to verify `-m` and `--mmproj` flags point to the target path and `--ctx-size` is updated.
3. **Checking daemon health**: Run:
   ```bash
   systemctl --user daemon-reload
   systemctl --user restart sovereign-engine
   systemctl --user status sovereign-engine
   ```
4. **Verifying service connectivity**: Run `curl -s http://127.0.0.1:25001/health` and verify it returns a successful `"ok"` response.
