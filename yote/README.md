# 🐺 Yote — Sovereign Telegram + LLM Orchestrator

**Yote** is a production-grade, self-hosted Telegram bot and userbot orchestrator built with **Bun** (TypeScript) + **Telethon** (Python). It merges multiple previously separate components into one cohesive, maintainable project:

- Full-featured Telegram **bot** (polling + commands, chat-to-LLM, registration, health)
- **Overlord** Telethon userbot that listens to channels/groups and emits structured JSON (for n8n, pipelines, or logging)
- Modular HTTP health/status server (extended with process inspection + log tailing)
- Local LLM integration (llama.cpp / OpenFang / vLLM compatible)
- Utility scripts for invite generation and bulk invites
- Designed for sovereign / homelab / air-gapped-leaning deployments ( configurable paths, no hard-coded toxic user paths in final form)

This is the merged evolution of:
- `yote.ts` (core bot + polling + OpenFang bridge + userbot spawner)
- `index.ts` + `health.ts` + `process.ts` + `logs.ts` (modular HTTP surface + process mgmt)
- `overlord.py` (Telethon message forwarder / JSON emitter)
- `agent.ts`, `daemon.ts` (reference implementations / future extension points)
- `generate_invites.py` + `invite_puppertrix.py` (admin utilities)

## Project Layout (after merge)

```
yote/
├── package.json
├── bunfig.toml (optional)
├── README.md
├── .env.example
├── .gitignore
├── src/
│   ├── index.ts          # Thin entry (starts everything)
│   ├── yote.ts           # Main orchestrator (bot polling, HTTP server, LLM calls, userbot spawn)
│   └── lib/
│       ├── health.ts     # LLM / stack health checks
│       ├── process.ts    # Sovereign process lister + port killer
│       ├── logs.ts       # Log tailing + listing
│       ├── agent.ts      # Simple LLM agent wrapper (example)
│       └── daemon.ts     # Heartbeat / scheduler skeleton (extend as needed)
├── scripts/
│   └── telethon/
│       ├── overlord.py           # Telethon channel listener → JSON stdout
│       ├── generate_invites.py   # Export invite links for all groups/channels
│       ├── invite_puppertrix.py  # Bulk-invite @puppertrix to your chats
│       └── .venv/                # Created by `bun run setup:python`
├── sessions/                     # Telethon .session files (gitignored)
├── config/                       # runtime JSON (registered chats, etc.)
├── logs/                         # runtime logs
└── ...
```

## Quick Start

1. **Clone / place** the `yote/` folder in your sovereign homelab dir (e.g. `~/sovereign/yote` or `/home/toxic/sovereign/yote`).

2. **Install Bun** (if not present): `curl -fsSL https://bun.sh/install | bash`

3. **Configure environment**
   ```bash
   cp .env.example .env
   # edit .env with your TELEGRAM_BOT_TOKEN, API_ID/HASH, allowed user IDs, etc.
   ```

4. **Setup Python side** (Telethon)
   ```bash
   bun run setup:python
   # This creates scripts/telethon/.venv and installs telethon + python-dotenv
   ```

5. **Place your session files** (optional but recommended for Overlord)
   - `sovfang.session` (user session) → `sessions/sovfang.session` or root
   - Update `TELEGRAM_SESSION` in `.env` if using StringSession instead of file.

6. **Run**
   ```bash
   bun run start
   # or for watch mode during development:
   bun run dev
   ```

   The service will:
   - Start HTTP server on `YOTE_PORT` (default `:25042`) with `/health`, `/ps`, `/logs`, `/logs/:name`
   - Start Telegram bot long-poll loop
   - Spawn the Overlord Telethon userbot subprocess (listens & prints JSON)
   - Send boot notification to all previously registered chats (if any)

## Telegram Bot Commands (for allowed users)

- `/start` — Register chat, show stack status, list commands
- `/status` — Detailed health (llama, openfang, GPU via nvidia-smi if available)
- `/chat <message>` — Send message to local LLM (OpenFang) and get reply
- Any plain text → treated as `/chat` message (direct inference)

The bot also supports threaded messages (message_thread_id) for topics/supergroups.

## HTTP Endpoints ( Bun server )

| Method | Path          | Description                              |
|--------|---------------|------------------------------------------|
| GET    | `/health`     | Basic status + LLM reachability          |
| GET    | `/ps`         | List sovereign processes (llama, openfang, yote, etc.) |
| GET    | `/logs`       | List available log files                 |
| GET    | `/logs/:name` | Tail last N lines of a log file          |

## Architecture & Data Flow

```
Telegram Bot API (long poll)
        ↓
yote.ts (Bun)
  ├── processUpdate() → handleStart / handleStatus / handleChat
  ├── handleChat() → fetch(OpenFang /v1/chat/completions)
  ├── startUserbot() → spawn( python overlord.py )
  │                        ↓
  │                   Telethon Overlord
  │                        ↓ (stdout JSON lines)
  │                   logged by Bun + optionally piped to n8n / pipelines
  └── serve() → /health + /ps + /logs (using lib/* modules)
```

**Overlord** (`overlord.py`):
- Uses Telethon to listen to `NewMessage` on specified (or all) chats.
- Outputs one JSON object per message to stdout (chat_id, sender, text, date, etc.).
- Perfect for feeding into n8n, OpenFang agents, or your own sovereign pipelines.
- Can run as userbot (session) or bot (token).

## Utility Scripts

```bash
# Generate invite links for every group/channel your account is in and DM them to TARGET_USER
bun run invite:generate

# Bulk invite @puppertrix to every group/channel
bun run invite:puppertrix
```

These still use the classic Telethon + dotenv pattern. Put credentials in `.env` at project root (or the script's cwd).

## Configuration Notes & Path Resolution

Yote now uses **relative path resolution** based on `import.meta.dir`:

- Overlord script: `scripts/telethon/overlord.py`
- Python interpreter: `scripts/telethon/.venv/bin/python3` (after setup)
- Logs: `./logs/`
- Registered chats persistence: `./config/yote_chats.json`
- Sessions: `./sessions/` (or root for backward compat)

You can override via environment variables if your layout differs.

Hard-coded `/home/toxic/...` paths from the original fragments have been removed or made configurable for portability.

## Security & Allowed Users

- `TELEGRAM_ALLOWED_USERS` is an **allowlist**. Unauthorized users get a polite "🔒 Unauthorized."
- Never commit real `.env`, `*.session`, or `config/yote_chats.json`.
- The Overlord can see **all** messages in the chats it joins — treat the session with care (use a dedicated low-privilege account if possible).

## Extending

- Add new command handlers in `src/yote.ts` → `processUpdate()`
- Want persistent memory / RAG? Plug into the OpenFang endpoint or add a vector store.
- GPU / llama.cpp management: extend `src/lib/process.ts` or add a watchdog.
- For full daemon supervisor behavior, the `daemon.ts` skeleton + Bun's `--watch` or external tools (systemd, pm2, or your own) can be layered on top.

## License & Credits

Merged & curated for sovereign use by Chris / Effusion Labs (trixisowned / Pup Trix).

Original fragments inspired by Telethon examples, n8n-friendly patterns, and the broader OpenFang / sovereign agent ecosystem (2026).

---

**Status**: Production-ready for homelab. Paths normalized, modules merged, Python utilities included, documentation added.

Run `bun run start` and enjoy your sovereign Telegram layer on top of local LLMs.
