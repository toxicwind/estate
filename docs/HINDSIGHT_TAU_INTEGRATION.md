# Sovereign Hindsight & Tau Long-Term Memory Architecture

> **Harness**: Tau Coding Agent (`/home/toxic/sovereign/agent`)
> **Memory Backend**: Vectorize Hindsight (`ghcr.io/vectorize-io/hindsight:latest`)
> **Inference Engine**: Herd (`github.com/mostlygeek/llama-swap` Go binary on port 25100)
> **Model**: `beellama/qwen-flash-64k` (Qwen 3.5 9B DeepSeek-v4 Flash, 64K context, 119 tokens/sec)

---

## 1. Network Topology & Service Map

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           SOVEREIGN LOCAL STACK                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ Tau Coding Agent                                                │   │
│   │ Executable: /home/toxic/sovereign/agent                         │   │
│   │ Config: ~/.tau/config.yml (memory.backend: hindsight)           │   │
│   │ Client: /home/toxic/projects/sovereign-projects/tau/.../client.ts│  │
│   └────────────────────────────────┬────────────────────────────────┘   │
│                                    │ Recall / Reflect                   │
│                                    ▼                                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ Hindsight Server (Docker Container, --network host)             │   │
│   │ API Port: 25117 (/health, /v1/banks/{id}/recall, etc.)          │   │
│   │ Control Plane Port: 25118 (Web Dashboard)                       │   │
│   │ Storage: Docker named volume `hindsight-data` (/home/hindsight) │   │
│   └────────────────────────────────┬────────────────────────────────┘   │
│                                    │ OpenAI API calls (port 25100)      │
│                                    ▼                                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ Herd / Llama-Swap (Port 25100)                                  │   │
│   │ Engine: beellama.cpp (build-cuda86/bin/llama-server)            │   │
│   │ Model: Qwen3.5-9B-DeepSeek-V4-Flash-IQ4_XS.gguf                 │   │
│   │ Context: 65,536 tokens (64K)                                    │   │
│   │ Acceleration: CUDA 12.8 / Flash Attention / sm_86 (RTX 3090)   │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Port Allocations & Environmental Variables

| Port | Service | Protocol | Role |
|:---:|---|:---:|---|
| **25100** | **Herd** (`llama-swap`) | HTTP / OpenAI | Local LLM inference endpoint (`/v1/chat/completions`) |
| **25117** | **Hindsight API** | HTTP / REST | Memory ingest, semantic recall, agentic reflection |
| **25118** | **Hindsight Control Plane** | HTTP / Web | Interactive UI dashboard and bank management |

### Hindsight Container Environment (`sovereign/stack/services/hindsight.sh`)
```bash
HINDSIGHT_API_PORT="25117"
HINDSIGHT_CP_PORT="25118"
HINDSIGHT_API_LLM_PROVIDER="openai"
HINDSIGHT_API_LLM_BASE_URL="http://127.0.0.1:25100/v1"
HINDSIGHT_API_LLM_API_KEY="llama-swap-local-key"
HINDSIGHT_API_LLM_MODEL="beellama/qwen-flash-64k"
```

---

## 3. Tau Configuration (`~/.tau/config.yml` & `~/.tau/agent/config.yml`)

Tau includes native first-class integration for Hindsight. Profiles have been consolidated into a single default profile:

```yaml
memory:
  backend: hindsight

hindsight:
  apiUrl: "http://127.0.0.1:25117"
  scoping: per-project-tagged
  autoRecall: true
  autoRetain: true
  retainMode: full-session
```

### Extension Registration
Tau automatically loads the Hindsight extension via `~/.tau/agent/settings.json`:
```json
{
  "extensions": [
    "/home/toxic/.hindsight/coding-agents/dist/pi.js"
  ]
}
```
And the symlink at `~/.tau/agent/extensions/hindsight.js`.

---

## 4. Key Architectural Fixes Applied

1. **Model Upgraded from 1.2B to 9B 64K**:
   - Previous flawed setting used `beellama/exaone-4-0-1-2b-iq4xs` (1.2B, 32K context), which failed structured extraction and reflection.
   - Upgraded to `beellama/qwen-flash-64k` (9B DeepSeek-v4 Flash), achieving **119 tokens/second** with **64,000 token context** and only ~6 GB VRAM consumption.
2. **RPATH Origin Patch**:
   - Fixed `beellama.cpp` binary by running `patchelf --set-rpath '$ORIGIN'` on `llama-server` and its shared libraries, eliminating the need for hardcoded `LD_LIBRARY_PATH` exports.
3. **Environment Variable Name Fix**:
   - Corrected Hindsight configuration to use `HINDSIGHT_API_LLM_BASE_URL` (previously misnamed `API_URL`).
4. **Host Network Binding**:
   - Docker container runs with `--network host` and `--pull missing` to allow direct access to loopback port `25100` with zero NAT overhead.
5. **Launcher Consolidation**:
   - `/home/toxic/sovereign/agent` is the canonical executable, with symlinks in `~/.local/bin/agent` and `~/.local/bin/tau`.
   - Includes a non-blocking asynchronous health check that automatically ensures Herd and Hindsight are running upon launch.
