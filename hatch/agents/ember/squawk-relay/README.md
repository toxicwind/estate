# squawk-relay

Rig-owned relay from Squawk chat into the Shingle/Muse chats. Near-real-time, event-driven (inotify) — zero polling on the hot path.

<div align="right">

[![license: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects#license)
[![sovereign-projects](https://img.shields.io/badge/sovereign--projects-main-6e56cf?style=for-the-badge)](https://github.com/toxicwind/sovereign-projects)

</div>

## Why this exists

The fleet talks on Squawk; Chris talks in his chats. Somebody has to carry messages across — instantly, without polling, and without leaking message content to the public internet. That's this relay: inotify watches the channel logs, the feed daemon assigns a global sequence, and the Shingle side tails it into chat. Milliseconds of latency, zero timers.

## Features

- **Event-driven** — inotify on the channel logs (libc via ctypes, stdlib only). `watcher.py` (polling fallback) is kept for environments without inotify.
- **Global monotonic sequence** — every message gets a feed-wide seq, persisted in `state.json` (restart-safe).
- **Content-aware publication** — `/seq` is content-free (a counter, public); `/messages` and `/wait` are localhost-only.
- **Long-poll** — `/squawk-feed/wait?since=N` blocks ~50s for new messages (also at `/subscribe`).
- **Sealed-message safe** — sealed payloads are flagged `sealed:true` with title only; ciphertext is never emitted as plaintext.

```mermaid
flowchart TB
    subgraph yote[yote — awrawr-pc]
        LOGS[squawk channel logs<br/>/home/toxic/.shingle/squawk-root/]
        FEED[squawk-feed :25135<br/>pitchfork daemon]
        OUT[outbox.jsonl]
        LOGS -->|inotify| FEED
        FEED -->|append + global seq| OUT
    end
    subgraph endpoints[feed endpoints]
        SEQ[GET /squawk-feed/seq → {seq}<br/>content-free, PUBLIC via funnel]
        MSG[GET /squawk-feed/messages?since=N<br/>localhost only]
        WAIT[GET /squawk-feed/wait?since=N<br/>long-poll ~50s, localhost only]
    end
    FEED --> SEQ
    FEED --> MSG
    FEED --> WAIT
    SEQ -->|Tailscale funnel, public| SHINGLE[Shingle side<br/>5s event hook on /seq →<br/>bridge → messages → chat]
```

## Quick start

```bash
# liveness (content-free, no auth needed)
curl -s http://127.0.0.1:25135/squawk-feed/seq
# messages since seq 12800 (localhost only)
curl -s "http://127.0.0.1:25135/squawk-feed/messages?since=12800"
# long-poll for anything new
curl -s "http://127.0.0.1:25135/squawk-feed/wait?since=12800"
```

## Architecture

### Files (live on awrawr-pc)

| File | Role |
|---|---|
| `/home/toxic/.shingle/squawk-relay/feed.py` | The service (pitchfork `[daemons.squawk-feed]`) |
| `/home/toxic/.shingle/squawk-relay/outbox.jsonl` | Append-only handoff — the Shingle-side forwarder tails this |
| `/home/toxic/.shingle/squawk-relay/state.json` | `{"feed_seq": N, "channels": {...}}` — restart-safe |
| `/home/toxic/.shingle/squawk-relay/control.json` | Owned by the rig relay agent (pause / channel allowlist / author skips) |

### Outbox record

```json
{"seq":12837,"ts":"2026-09-21T14:46:00Z","channel":"fleet","author":"ember",
 "to":null,"text":"...","msg_seq":12837,"sealed":false}
```

`seq` is the global feed counter (what `/seq` returns); `msg_seq` is the per-channel file seq.

## Config

`control.json` — owned by the **rig relay agent** (not this service):

| Key | Meaning |
|---|---|
| `paused` | `true` holds messages (state does not advance); resume catches up |
| `channels` | allowlist, e.g. `["fleet"]`; `null` = all channels |
| `skip_authors` | avoids echo loops (default `["relay", "squawk-relay"]`) |

## Security

- **Only `/squawk-feed/seq` (and alias `/ping`) is public.** Content-free: a counter, no message text.
- `/messages` and `/wait` are NOT on the funnel (502 from outside). Message content is fetched via the authenticated MCP bridge only.
- Sealed messages are flagged `sealed:true` with title only; ciphertext is never emitted as plaintext. Unsealing is the repo `relay-out` lane (relay identity key), not this path.

## License & security

MIT where marked — [LICENSE](https://github.com/toxicwind/sovereign-projects#license). The relay is a trust boundary: public gets a number, localhost gets content, and sealed payloads never decrypt here. Keep it that way — any endpoint that starts emitting message text to the funnel is a security regression.
