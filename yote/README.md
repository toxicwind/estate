# 🐺 Yote — Sovereign Telegram + LLM Orchestrator

**Yote** is a production-grade, self-hosted Telegram bot and userbot orchestrator built with **Bun** (TypeScript) + **GramJS** (Telegram MTProto). It merges multiple previously separate components into one cohesive, maintainable project:

- Full-featured Telegram **bot** (polling + commands, chat-to-LLM, registration, health)
- **Overlord** GramJS userbot that listens to channels/groups and emits structured JSON
- Modular HTTP health/status server with Prometheus metrics
- Local LLM integration (llama.cpp / OpenFang / vLLM compatible)
- Utility scripts for invite generation and bulk invites
- Designed for sovereign / homelab / air-gapped-leaning deployments

## Quick Start

1. **Clone / place** the `yote/` folder in your sovereign homelab dir.

2. **Install Bun** (if not present): `curl -fsSL https://bun.sh/install | bash`

3. **Configure environment**
   ```bash
   cp .env.example .env
   # edit .env with your TELEGRAM_BOT_TOKEN, API_ID/HASH, allowed user IDs, etc.
   ```

4. **Install dependencies**
   ```bash
   bun install
   ```

5. **Generate GramJS session** (one-time)
   ```bash
   bun run overlord:login
   ```

6. **Run**
   ```bash
   bun run start
   # or for watch mode during development:
   bun run dev
   ```

## Telegram Bot Commands (for allowed users)

- `/start` — Register chat, show stack status, list commands
- `/status` — Detailed health (llama, openfang, GPU via nvidia-smi if available)
- `/chat <message>` — Send message to local LLM and get reply
- Any plain text → treated as `/chat` message (direct inference)

## HTTP Endpoints (Bun server)

| Method | Path          | Description                              |
|--------|---------------|------------------------------------------|
| GET    | `/health`     | Basic status + LLM reachability          |
| GET    | `/ps`         | List sovereign processes                 |
| GET    | `/logs`       | List available log files                 |
| GET    | `/logs/:name` | Tail last 50 lines of a log file         |
| GET    | `/metrics`    | Prometheus-compatible metrics            |
| POST   | `/restart`    | Remote restart (requires admin token)    |

## Architecture & Data Flow

```
Telegram Bot API (long poll)
        ↓
yote.ts (Bun)
  ├─ processUpdate() → handleStart / handleStatus / handleChat
  ├─ handleChat() → fetch(OpenFang /v1/chat/completions)
  ├─ startUserbot() → GramJS Overlord (in-process)
  │                        ↓
  │                   logged by Bun + optionally piped to n8n
  └─ serve() → /health + /ps + /logs + /metrics
```

## v0.5.0 Changes

- **Graceful shutdown**: SIGTERM/SIGINT properly stop HTTP server, Overlord, and daemon
- **Port conflict auto-kill**: Automatically kills processes on the configured port
- **Exponential backoff**: getUpdates errors back off up to 30s instead of spamming
- **Persistent update ID**: Survives crashes without re-processing old messages
- **StoreSession**: Overlord uses file-based sessions (more reliable than StringSession)
- **Auto-reconnect**: Overlord reconnects automatically on disconnect
- **Gzip log rotation**: Rotated logs are compressed automatically
- **Prometheus metrics**: `/metrics` endpoint for monitoring
- **CORS**: All HTTP responses include proper CORS headers
- **X-Request-ID tracing**: OpenFang proxy forwards request IDs

## License & Credits

Merged & curated for sovereign use by Chris / Effusion Labs (trixisowned / Pup Trix).

Original fragments inspired by Telethon examples, n8n-friendly patterns, and the broader OpenFang / sovereign agent ecosystem (2026).

---

**Status**: Production-ready for homelab. v0.5.0 hardened with graceful shutdown, auto-reconnect, and Prometheus metrics.

Run `bun run start` and enjoy your sovereign Telegram layer on top of local LLMs.
