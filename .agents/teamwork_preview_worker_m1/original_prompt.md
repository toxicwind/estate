## 2026-06-18T17:56:37Z
You are teamwork_preview_worker_m1.
Your working directory is /home/toxic/sovereign/.agents/teamwork_preview_worker_m1.
Your task is to execute the implementation and verification steps for Milestone 1:
1. Ensure no other instances are using GPU memory: run `systemctl --user stop sovereign-engine.service` and pkill any stray llama-server or ollama.
2. Run the tuning search script: `python3 /home/toxic/sovereign/bin/test_max_ctx.py`.
3. Capture the "Highest stable context: <VALUE>" from the output.
4. Update `process-compose.yaml`:
   - Change the model path to `/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf`.
   - Update `--ctx-size` under the llama-server process configuration to the found stable context size.
   - Add the `--mmproj /home/toxic/models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf` flag in the command block.
5. Reload and restart systemd user service:
   - `systemctl --user daemon-reload`
   - `systemctl --user enable sovereign-engine.service`
   - `systemctl --user restart sovereign-engine.service`
6. Verify service health and connectivity:
   - `systemctl --user status sovereign-engine.service`
   - Run readiness curls for:
     - `http://127.0.0.1:25001/health`
     - `http://127.0.0.1:25008/v1/models`
     - `http://127.0.0.1:25004/api/health`
7. Write your changes and execution log to `/home/toxic/sovereign/.agents/teamwork_preview_worker_m1/changes.md` and complete `handoff.md`.
8. Send a message back to the orchestrator (conversation ID: 11881832-de99-4b70-8a3a-8e164d2806d9) referencing the files and results.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
