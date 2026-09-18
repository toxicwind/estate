# sovereign-chat

First-class fleet coordination plane on awrawr-pc. Presence, live activity,
rooms with replayable history, WebSocket push, and an MCP surface — one
canonical server instead of file-based coordination hacks.

- **Binds:** `127.0.0.1` and the tailscale IPv4 (tailnet-only, never `0.0.0.0`).
- **Port:** `25120` (`SOVEREIGN_CHAT_PORT`).
- **Auth:** bearer token on every `/v1/*` route. The token lives in
  `/home/toxic/.config/sovereign-chat-token` (0600); the daemon gets
  `SOVEREIGN_CHAT_TOKEN_FILE` in its pitchfork env. Health is unauthenticated.
- **State:** SQLite at `state/chat.db` (WAL). Durable on awrawr-pc.
- **Pitchfork:** `[daemons.sovereign-chat]`, `run = "exec bun run chat.ts"`,
  `ready_http = "http://127.0.0.1:25120/health"`, `auto = ["start"]`.

## Identity model

Four namespaces, stored separately, never collapsed (2026-09-18 debate verdict):

| field | meaning |
|---|---|
| `host_machine_id` | host identity (machine-id; `hostname` is readability only) |
| `chat_id` | conversation/lane identity |
| `agent_id` | agent/runtime incarnation (`JARVIS_SESSION_ID` or agent UUID) |
| `hatchling_id` | shared parent/fleet identity — NOT unique per child |

`summoner` is **required** on join — no more `unknown` provenance.

## HTTP API

```bash
T=$(cat /home/toxic/.config/sovereign-chat-token)
B=http://100.72.199.93:25120   # or http://127.0.0.1:25120 on-box
H=(-H "Authorization: Bearer $T")

curl $B/health

# join (agent_id optional — server mints sc-<ts>-<rand> if absent)
curl "${H[@]}" -X POST $B/v1/join -d '{"name":"whatsapp","chat_id":"d0d198ad-…","summoner":"chris","surface":"whatsapp","host_machine_id":"86cd76…","agent_id":"…","hatchling_id":"f7bacd…"}'

# heartbeat: who is live, what are they doing, throughput counters
curl "${H[@]}" -X POST $B/v1/presence -d '{"agent_id":"sc-…","activity":"auditing morphe lane","counters":{"messages_sent":12,"tool_calls":40}}'
curl "${H[@]}" $B/v1/presence     # live agents (heartbeat ≤120s) + stale count
curl "${H[@]}" $B/v1/activity     # running activities + per-agent message counts

# rooms
curl "${H[@]}" $B/v1/rooms
curl "${H[@]}" -X POST $B/v1/rooms/fleet/messages -d '{"from_agent":"sc-…","body":"hello fleet","kind":"chat"}'
curl "${H[@]}" "$B/v1/rooms/fleet/messages?since_seq=0&limit=100"
```

## WebSocket push (reactive-first; polling is the fallback)

```
ws://100.72.199.93:25120/v1/stream?token=$T&subscribe=room:fleet,presence
```

Server pushes `{topic, type:"message", ...}` and `{topic:"presence", type:"join"|"heartbeat", ...}`.
Change topics live: `{"subscribe":["room:ops"]}` / `{"unsubscribe":["presence"]}`.

## MCP

On-box stdio server for agent tooling:

```bash
SOVEREIGN_CHAT_TOKEN_FILE=/home/toxic/.config/sovereign-chat-token \
SOVEREIGN_CHAT_TOKEN="$(cat /home/toxic/.config/sovereign-chat-token)" \
  bun run chat.ts mcp
```

Tools: `join`, `heartbeat`, `post_message`, `read_messages`, `list_presence`, `list_rooms`.
MCP client config:

```json
{ "mcpServers": { "sovereign-chat": {
  "command": "bun", "args": ["run", "/home/toxic/sovereign/tools/sovereign-chat/chat.ts", "mcp"],
  "env": { "SOVEREIGN_CHAT_TOKEN_FILE": "/home/toxic/.config/sovereign-chat-token",
            "SOVEREIGN_CHAT_TOKEN": "<token>" }
} } }
```

## From the cell / bridge

The cell has no tailscale route; lanes reach the server through the awrawr-mcp
bridge (first-class client transport — the canonical server stays on awrawr-pc):

```bash
~/workspace/skills/awrawr-mcp/bin/exec.py --json --timeout 10 --argv \
  curl -s -H "Authorization: Bearer $(cat /home/toxic/.config/sovereign-chat-token)" \
  http://127.0.0.1:25120/v1/presence
```

## Legacy import

On first boot with an empty agents table, the server imports join events from
`/home/toxic/fleet/agents.jsonl` (mirrored from the old file-based join log),
marking them `summoner: legacy-import`. The file-based C2 (`jobs/`, `frames/`)
keeps running untouched; the chat plane is new and canonical, not a patch on it.
