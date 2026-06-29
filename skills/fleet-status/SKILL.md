---
name: fleet-status
description: >
  Reports the status of the sovereign AI mesh. Shows which ports are up,
  VRAM usage, current model, active context, and agent pool health.
  Triggers on: "status", "fleet", "mesh health", "is the model running",
  "gpu usage", "vram", "agents", "how many tokens".
---

# Fleet Status Skill

## Usage
Query the sovereign mesh endpoints and return a formatted status report.

## Tool calls
1. GET http://127.0.0.1:${NFCOT_PORT}/health → NF-CoT status
2. GET http://127.0.0.1:${LLAMA_PORT}/health → beellama status
3. GET http://127.0.0.1:${OPENFANG_PORT}/agents → agent pool
4. GET http://127.0.0.1:${RANK_PORT}/health → fleet ranker

## Response format
Return a concise status table. Include: port, service, status, latency.
