# fleet-status {badges}

<!-- badges: start -->
<a href="https://github.com/toxicwind/estate">
  <img src="https://img.shields.io/badge/github-toxicwind/sovereign--projects-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub repo">
</a>
<!-- badges: end -->

## Reports the status of the sovereign AI mesh.

**What**: Query the sovereign mesh endpoints and return a formatted status report showing which ports are up, VRAM usage, current model, active context, and agent pool health.

**Why**: Check the health of the sovereign AI mesh — see which services are running, their latency, and current operational status.

**Who**: Simple status reporter for the sovereign AI mesh. Triggers on: "status", "fleet", "mesh health", "is the model running", "gpu usage", "vram", "agents", "how many tokens".

## Feature bullets

- **Four tool calls**: Queries key sovereign mesh health endpoints
  1. GET http://127.0.0.1:${NFCOT_PORT}/health → NF-CoT status
  2. GET http://127.0.0.1:${LLAMA_PORT}/health → beellama status
  3. GET http://127.0.0.1:${OPENFANG_PORT}/agents → agent pool
  4. GET http://127.0.0.1:${RANK_PORT}/health → fleet ranker
- **Response format**: Concise status table with port, service, status, latency
- **Port-specific**: Uses environment variables NFCOT_PORT, LLAMA_PORT, OPENFANG_PORT, RANK_PORT
- **Service-specific**: NF-CoT, beellama, agent pool, fleet ranker health checks

## Quick start

```bash
# Set required port environment variables
export NFCOT_PORT=<port>
export LLAMA_PORT=<port>
export OPENFANG_PORT=<port>
export RANK_PORT=<port>

# Run the status check
# (Implementation details are internal to the skill)
```

## Config / optional services

- **NFCOT_PORT**: Port for NF-CoT service health endpoint
- **LLAMA_PORT**: Port for beellama service health endpoint
- **OPENFANG_PORT**: Port for agent pool endpoint
- **RANK_PORT**: Port for fleet ranker service health endpoint
- **Environment variables**: All four port variables must be set for proper operation

## Dev / contributing

- Returns a concise status table including: port, service, status, latency
- Each tool call queries a specific sovereign mesh endpoint
- No polling, no timers — simple request/response health checks
- Agent pool health comes from OPENFANG_PORT/agents endpoint

## License + security

- **License**: Open Claw source (see `skill.toml`)
- **Security**: Read-only health checks — no modification of services, only status queries. Uses standard HTTP GET requests to localhost endpoints.