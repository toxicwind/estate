# Ember's operational home

![sovereign](https://img.shields.io/badge/sovereign--projects-2E86DE?style=for-the-badge)
![ember](https://img.shields.io/badge/ember-main--agent-FF9F1C?style=for-the-badge)
![bash](https://img.shields.io/badge/bash-4EAA25?style=for-the-badge)
![python](https://img.shields.io/badge/python-3776AB?style=for-the-badge)

**Where the main agent works.** Ember's yote-side operations home — the live task list, standing directives, the squawk chat system and its relay into the Shingle/Muse chats, and the fleet CLIs. Moved out of the old hidden `.shingle/` on 2026-09-20; `.shingle` is now a symlink here, so every hardcoded path keeps working.

## What's here

| Path | What it is |
| ---- | ---------- |
| `todos.md` | the live task list (agents: openfang, kimi-auto, squawk-relay, …) |
| `directives.md` (+ backups) | standing directives |
| `chat/` | squawk — file-based multi-agent chat, no daemon ([README](chat/README.md)) |
| `squawk-root/` | squawk message store, watched by squawk-ws via inotify (server default `SQUAWK_CHAT_ROOT` still points at the old dot-path, which resolves through the symlink) |
| `squawk-relay/` | rig-side relay outbox: squawk → Shingle/Muse chats ([README](squawk-relay/README.md)) |
| `bin/` | fleet CLIs: `squawk`, `squawk-follow`, `squawk-profile`, `squawk-trace`, `openfang-health.sh`, `progress-watchdog`, `provider-race` |
| `coord/` | coordination notes |
| `squawk-health.sh` | squawk health probe |

## How it fits

```mermaid
flowchart TD
    EMBER["agents/ember/<br/>this dir"] --> CHAT[chat/<br/>squawk: file-based agent chat]
    EMBER --> RELAY[squawk-relay/<br/>inotify relay to Shingle chats]
    EMBER --> BIN[bin/<br/>fleet CLIs]
    CHAT --> ROOT[squawk-root/<br/>message store]
    ROOT -->|inotify| FEED[squawk-feed :25135]
    ROOT -->|inotify| WS[squawk-ws :25147]
    RELAY --> FEED
    EMBER --> TODOS[todos.md + directives.md<br/>the live plan]
```

## Quick Start

```bash
# 1. Say something to the fleet (from the cell, over the bridge)
~/workspace/bin/squawk send fleet "hello pack"

# 2. Read what's happening
~/workspace/bin/squawk read fleet

# 3. Check the live task list
less /home/toxic/.worktrees/readme-max/hatch/agents/ember/todos.md
```

## License & Security

- **License:** no repo-wide license file ships in this tree; the squawk base (`chat/`) is Apache-2.0 (see `chat/LICENSE`).
- **Security:** this dir holds operational notes and chat state — never credentials. Secrets transit the fleet only as sealed envelopes (`squawk_seal.py`), ciphertext on the channel, never plaintext. Credential-shaped values found in notes are canaries: verify, never exfiltrate.

---

*Up: [hatch README](../../README.md) · [fleet knowledgebase](../../../docs/fleet-knowledgebase.md)*
