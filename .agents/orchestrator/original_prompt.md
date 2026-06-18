# Original User Request

## Initial Request — 2026-06-18T11:54:43-06:00

Optimize the Sovereign Stack LLM execution (determining max stable context size, process-compose config, service auto-start) and compile the `lucebox-hub` library with Ampere TMA Emulation optimizations.

Working directory: /home/toxic/sovereign
Integrity mode: development

## Requirements

### R1. Determine Max Stable Context Size
Find the highest stable context size for the RTX 3090 GPU using `bin/test_max_ctx.py` with `heretic-UD-27B-Q5_K_XL.gguf` and `mmproj-27B-F16.gguf` under Q4_0 KV cache settings. Update the `llama-server` command in `process-compose.yaml` with the optimal `--ctx-size` and restart/enable the `sovereign-engine` systemd user service.

### R2. Compile lucebox-hub
Compile `lucebox-hub` inside `/home/toxic/lucebox-hub` using CMake, ensuring the DFlash and Megakernel (Ampere TMA Emulation) optimizations are enabled. If any external dependencies or fork modifications are required, fork them privately (GitHub client is already authenticated).

### R3. MTProto Service Integration
Add the Telethon Overlord daemon (`python3 /home/toxic/agents/telethon_overlord/overlord.py`) as a managed process under `process-compose.yaml` using the environment variables from `/home/toxic/agents/telethon_overlord/.env`.

## Acceptance Criteria

### Context Tuning & Service
- [ ] `test_max_ctx.py` is executed and a stable maximum context size is found.
- [ ] `process-compose.yaml` is updated with the determined context size.
- [ ] `sovereign-engine` user service is running successfully and is marked as active.

### Lucebox Hub Compilation
- [ ] `lucebox-hub` is compiled successfully using CMake with DFlash/Megakernel optimization flags.

### Telegram MTProto Overlord
- [ ] `process-compose.yaml` contains the `telethon_overlord` process configuration.
- [ ] The overlord script is running successfully under `process-compose` and logs show it connects to Telegram without authorization prompts (using existing session).
