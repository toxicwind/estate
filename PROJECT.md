# Project: Sovereign Stack Optimization and Lucebox Hub Compilation

## Architecture
- `process-compose.yaml` coordinates:
  - `llama-server` (ik_llama, CUDA, Qwen3.6-27B) on port 25001
  - `nfcot_proxy` (latent injection proxy) on port 25008
  - `openfang` on port 25004
  - `sovereign_watchdog`
  - `yote_telegram`
  - `yote_daemon`
  - `telethon_overlord` (to be added)
- `sovereign-engine.service` (systemd user service) manages process-compose lifecycle.
- `lucebox-hub`: C++ inference engine codebase with custom CUDA kernels (DFlash, Megakernel).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Context Tuning & Service Setup (R1) | Find max stable context size, update process-compose, restart systemd service | None | DONE |
| 2 | MTProto Service Integration (R3) | Integrate telethon_overlord daemon into process-compose | M1 | PLANNED |
| 3 | Compile lucebox-hub (R2) | Compile lucebox-hub with DFlash & Megakernel optimizations | None | IN_PROGRESS |

## Interface Contracts
### llama-server ↔ nfcot_proxy
- Host/Port: 127.0.0.1:25001 (llama-server)
- Port: 127.0.0.1:25008 (nfcot_proxy)
- Verification: `/health` endpoints and API completions.

### process-compose ↔ telethon_overlord
- Executable: `python3 /home/toxic/agents/telethon_overlord/overlord.py`
- Environment variables sourced from `/home/toxic/agents/telethon_overlord/.env`.

## Code Layout
- Sovereign codebase: `/home/toxic/sovereign`
- Lucebox-hub codebase: `/home/toxic/lucebox-hub`
