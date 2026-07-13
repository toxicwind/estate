# null-g-proxy — OpenAI-Compatible AI Proxy for Antigravity IDE

[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-%E2%89%A518-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![Hono](https://img.shields.io/badge/Hono-Framework-E36002?style=flat-square)](https://hono.dev/)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-6BA539?style=flat-square&logo=openapiinitiative&logoColor=white)](http://localhost:8787/openapi.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**Self-hosted OpenAI-compatible proxy that exposes every AI capability of the [Antigravity IDE](https://antigravity.dev) — chat completions, Git intelligence, knowledge base, terminal execution, and code intelligence — as a single REST API.**

---

## What is this?

`null-g-proxy` is a lightweight local server that bridges any OpenAI-compatible client (Claude Code, Cursor, Continue, custom scripts) to the Antigravity IDE's internal AI engine. It auto-discovers the running IDE, proxies requests to it, and returns responses in the standard OpenAI format.

The Antigravity IDE runs Gemini, Claude, and GPT models with deep code awareness. `null-g-proxy` makes all of that available over HTTP so you can:

- Use it as a **drop-in OpenAI-compatible backend** from Claude Code, Cursor, Continue, or any other AI client
- Call it from shell scripts, CI pipelines, or autonomous agents
- Integrate it into your own tools via a well-documented REST API with interactive Swagger UI

---

## Features

| Capability | Description |
|---|---|
| **Chat Completions** | OpenAI-compatible `POST /v1/chat/completions` with streaming and multi-turn support |
| **Multi-model** | Switch between Gemini, Claude, and GPT models per request |
| **Streaming** | Server-Sent Events (SSE) for real-time response streaming |
| **Multi-turn sessions** | Persistent cascade sessions for stateful conversations |
| **Agentic mode** | Antigravity autonomously plans and executes complex multi-step tasks |
| **Git intelligence** | AI-generated commit messages, repo listing, worktree management |
| **Knowledge base** | CRUD and full-text search over a personal Markdown knowledge base |
| **Terminal execution** | Sandboxed shell execution with a security denylist (HTTP 403 on blocked commands) |
| **Code search** | ripgrep-powered codebase search with file glob and result limit filters |
| **Code lint** | ESLint / TypeScript compiler lint via HTTP |
| **Swagger UI** | Interactive API docs at `GET /docs` |
| **Zero-config** | Auto-discovers the running Antigravity IDE — no manual port configuration needed |

---

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| **Antigravity IDE** | Any | Must be running locally |
| **Node.js** | >= 18 | |
| **npm** | >= 9 | |
| **ripgrep** (`rg`) | Any | Optional — code search falls back to `grep` |
| **pm2** | >= 5 | Optional — for persistent process management |

---

## Installation

```bash
git clone https://github.com/cristianoaredes/null-g-proxy.git
cd null-g-proxy
npm install
```

---

## Running

**Development (hot-reload):**

```bash
npm run dev
```

**Production (compiled):**

```bash
npm run build
npm start
```

**With PM2 (recommended for persistent use):**

```bash
npm run build
pm2 start dist/index.js --name null-g-proxy
pm2 save
```

The server starts on **port 8787** by default:

```
[proxy] Connected: port=61971 workspace="my-workspace"
[proxy]   GET    http://localhost:8787/health
[proxy]   GET    http://localhost:8787/v1/models
[proxy]   POST   http://localhost:8787/v1/chat/completions
...
```

> **Note:** The proxy uses lazy discovery — it connects to the Antigravity IDE only on the first real API request, not on `/health`. Make sure the IDE is running before sending requests.

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `PORT` | `8787` | HTTP port to listen on |
| `ANTIGRAVITY_PORT` | *(auto)* | Override language server port (disables auto-discovery) |
| `ANTIGRAVITY_CSRF_TOKEN` | *(auto)* | Override CSRF token (required when `ANTIGRAVITY_PORT` is set) |
| `ANTIGRAVITY_WORKSPACE` | *(auto)* | Filter discovery by workspace name (for multi-project setups) |

**Manual override example:**

```bash
ANTIGRAVITY_PORT=61971 \
ANTIGRAVITY_CSRF_TOKEN=ab59ee2d-93f0-40ba-8784-ed77b1bfe34f \
npm start
```

---

## API Reference

### Health and Models

```bash
# Server status, uptime, active features
curl http://localhost:8787/health

# List available models in OpenAI format
curl http://localhost:8787/v1/models

# Interactive Swagger UI
open http://localhost:8787/docs
```

### Chat Completions

`POST /v1/chat/completions` — OpenAI-compatible endpoint with streaming, multi-turn, and agentic mode.

```bash
curl -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "antigravity/gemini-3-flash",
    "messages": [
      {"role": "user", "content": "Explain dependency injection in one paragraph."}
    ]
  }'
```

**Streaming (SSE):**

```bash
curl -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "antigravity/gemini-3-flash",
    "stream": true,
    "messages": [{"role": "user", "content": "Count from 1 to 5."}]
  }'
```

**Agentic mode** (Antigravity plans and executes autonomously):

```bash
curl -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "antigravity/gemini-3.1-pro-high",
    "agentic": true,
    "messages": [{"role": "user", "content": "Refactor all console.log statements in src/ to use a proper logger."}]
  }'
```

**Multi-turn conversations** — reuse a session via `cascade_id`:

```bash
# Turn 1 — start a session
RESP=$(curl -s -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"antigravity/gemini-3-flash","messages":[{"role":"user","content":"My name is Alice."}]}')

SESSION=$(echo $RESP | jq -r '.system_fingerprint')

# Turn 2 — continue the same session
curl -s -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"antigravity/gemini-3-flash\",\"cascade_id\":\"$SESSION\",\"messages\":[{\"role\":\"user\",\"content\":\"What is my name?\"}]}"

# End the session
curl -X DELETE http://localhost:8787/v1/chat/sessions/$SESSION
```

### Git Intelligence

**AI-generated commit message from staged diff:**

```bash
curl -X POST http://localhost:8787/v1/git/commit-message \
  -H "Content-Type: application/json" \
  -d '{"workingDir": "/path/to/your/repo", "style": "conventional"}'
```

```json
{
  "message": "feat(auth): add JWT token refresh endpoint\n\nImplements /api/auth/refresh...",
  "subject": "feat(auth): add JWT token refresh endpoint",
  "body": "Implements /api/auth/refresh that issues new access tokens..."
}
```

> Commit message generation typically takes 30–90 seconds depending on diff size and model load.

**List Git repos in `~/workspace`:**

```bash
curl http://localhost:8787/v1/git/repos
```

**Create a Git worktree:**

```bash
curl -X POST http://localhost:8787/v1/git/worktree \
  -H "Content-Type: application/json" \
  -d '{"repo": "myproject", "branch": "feature/new-ui"}'
```

### Knowledge Base

Markdown files stored in `~/.gemini/antigravity/knowledge/` (global) or `<projectDir>/.antigravity/knowledge/` (per-project).

```bash
# Create a knowledge item
curl -X POST http://localhost:8787/v1/knowledge/items \
  -H "Content-Type: application/json" \
  -d '{"name": "auth-notes", "content": "# Auth Notes\n\nWe use JWT with 15min expiry and refresh tokens."}'

# Full-text search (name matches weighted 5x)
curl "http://localhost:8787/v1/knowledge/search?q=authentication"

# List all items
curl http://localhost:8787/v1/knowledge/list
```

### Terminal Execution

```bash
curl -X POST http://localhost:8787/v1/terminal/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la", "cwd": "/Users/user/workspace", "timeout": 30000}'
```

```json
{"stdout": "total 48\n...", "stderr": "", "exitCode": 0}
```

Blocked commands (recursive deletion, privilege escalation, shell injection, fork bombs, network attacks) return **HTTP 403**.

### Code Intelligence

**Search codebase with ripgrep:**

```bash
curl "http://localhost:8787/v1/code/search?q=resolveInstance&workspace=/path/to/project&glob=*.ts&max=10"
```

**Lint a file (ESLint or tsc):**

```bash
curl "http://localhost:8787/v1/code/lint?file=/path/to/project/src/index.ts"
```

---

## Available Models

| Model ID | Provider | Best for | Timeout |
|---|---|---|---|
| `antigravity/gemini-3.1-pro-high` | Google | Complex reasoning, best quality | 120 s |
| `antigravity/gemini-3.1-pro-low` | Google | Balanced quality/speed | 90 s |
| `antigravity/gemini-3-flash` | Google | Fast, simple tasks | 60 s |
| `antigravity/claude-sonnet-4.6-thinking` | Anthropic | Extended thinking, analysis | 180 s |
| `antigravity/claude-opus-4.6-thinking` | Anthropic | Highest reasoning quality | 300 s |
| `antigravity/gpt-oss-120b` | OpenAI | Large capacity, versatile | 120 s |

Default: `antigravity/gemini-3.1-pro-high`

---

## Security

The proxy is designed for **local use only**. It inherits the file system permissions of the user running it.

- The terminal endpoint runs commands via `/bin/sh`. A regex denylist blocks the most dangerous patterns, but it is not a hardened sandbox.
- Do not expose port 8787 to the internet without a reverse proxy with IP whitelisting, rate limiting, and authentication.

---

## Troubleshooting

**`"status": "error"` on `/health` after startup** — normal. The proxy uses lazy discovery. Trigger it by calling any real endpoint (e.g. `GET /v1/models`). If it still fails, confirm the Antigravity IDE is running and check `ps aux | grep language_server` for the port and CSRF token.

**Commit message takes 30–90 seconds** — expected. The AI processes the diff asynchronously and the proxy polls until the response is ready (up to 180 seconds).

**Port 8787 already in use:**

```bash
lsof -i :8787
# Or start on a different port
PORT=9090 npm start
```

**Multiple Antigravity workspaces:**

```bash
ANTIGRAVITY_WORKSPACE="my-project" npm start
```

---

## License

MIT

by [Cristiano Aredes](https://github.com/cristianoaredes)

<!-- SEO: OpenAI compatible proxy, Antigravity IDE, chat completions, AI proxy, code intelligence, self-hosted AI, OpenAI API alternative, local AI proxy, Git AI assistant, ripgrep code search -->
