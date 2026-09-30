# omp-kafka

![omp-kafka](https://img.shields.io/badge/omp--kafka-D35400?style=for-the-badge) ![typescript](https://img.shields.io/badge/typescript-3178C6?style=for-the-badge&logo=typescript&logoColor=white) ![bun](https://img.shields.io/badge/bun-000000?style=for-the-badge&logo=bun&logoColor=white) ![MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

> Give your agent ears: stream Apache Kafka topics straight into the session — pushed live as messages, or buffered for on-demand pulls.

Part of [`toxicwind/tau-extensions`](https://github.com/toxicwind/tau-extensions). An [oh-my-pi (`omp`)](https://github.com/can1357/oh-my-pi) extension that lets an `omp` (or `pi`) instance subscribe to Apache Kafka topics and surface messages two ways:

- **auto (push) mode** — every consumed message is delivered into the running session as a user message (`sendUserMessage`) plus a `ctx.ui.notify`, so the LLM reacts without being asked.
- **pull mode** — messages buffer silently; the user (or the LLM, via the `kafka_consume` tool) pulls them on demand with `/kafka-tail`, `/kafka`, and `/kafka-reload`.

One `kafka.yml` configures the wiring per instance — one repo, many instances, each with its own client ID, topic set, and group ID.

```mermaid
flowchart LR
    Kafka[Kafka] -->|consume| ext[omp-kafka extension]
    ext -->|auto: sendUserMessage| s1[omp #1]
    ext -->|pull: tool / slash cmd| s2[omp #2]
    ext -->|pull: tool / slash cmd| s3[omp #3]
```

## Quick Start

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/toxicwind/tau-extensions ~/.tau/agent/extensions/tau-extensions
cd ~/.tau/agent/extensions/tau-extensions/packages/omp-kafka && bun install && omp plugin link .
```

Requires `omp >= 17.0.0`. Then create `kafka.yml` (see [Configure](#configure)) and start `omp`.

## Configure

Create `kafka.yml` next to your project (or pass `--kafka-config <path>` via `KAFKA_CONFIG` env). The file is a list of consumer profiles, each with its own brokers, topics, group ID, and mode:

```yaml
# ~/.tau/agent/kafka.yml
consumers:
  - name: events
    mode: auto               # "auto" (push) or "pull"
    brokers:
      - localhost:9092
    clientId: omp-events
    groupId: omp-events
    topics:
      - user.signup
      - billing.invoice
    fromBeginning: false
    notify: true             # also flash a UI notification on each message
    maxQueue: 500
    auto:
      deliverAs: steer       # "steer" or "followUp" (only meaningful in auto mode)
      prefix: "[kafka:events] "

  - name: ops-pull
    mode: pull
    brokers:
      - kafka.internal:9092
    topics:
      - ops.alerts
    # Everything else falls back to sensible defaults.
```

### Field reference

| Field | Default | Notes |
|---|---|---|
| `name` | required | Unique per `kafka.yml`. Used in `/kafka-*` commands and `ctx.ui.setStatus`. |
| `mode` | required | `auto` = push to session; `pull` = buffer only. |
| `brokers` | required | Non-empty array of `"host:port"` strings. |
| `topics` | required | Non-empty array of topic names. |
| `clientId` | `"omp-kafka"` | KafkaJS client ID. |
| `groupId` | `"omp-kafka-<name>"` | Consumer group. Set explicitly to share with another consumer. |
| `fromBeginning` | `false` | `false` = latest offset on first connect (good for live tails). |
| `notify` | `true` | Flash a UI notification per message (both modes). |
| `maxQueue` | `200` | Ring-buffer size for the in-memory tail. Older records drop off. |
| `auto.deliverAs` | `"steer"` | How `sendUserMessage` injects: `steer` (current turn) or `followUp` (queued). |
| `auto.prefix` | `"[kafka:<name>] "` | Prepended to the formatted record body. |
| `sasl` | unset | `{ mechanism, username, password }` for SASL auth. |
| `ssl` | `false` | Enable TLS. |
| `clientConfig` | `{}` | Extra KafkaJS `KafkaConfig` fields. |

### Resolution order

`loadConfig` looks for the config in this order (first hit wins):

1. `$KAFKA_CONFIG` (absolute path wins, otherwise resolved against `cwd`)
2. `<cwd>/kafka.yml`
3. `<cwd>/.tau/kafka.yml`
4. `~/.tau/agent/kafka.yml`

## Slash commands

| Command | Effect |
|---|---|
| `/kafka` | List every consumer and its current status. |
| `/kafka-tail <name> [limit]` | Print the last `limit` records (default 20) from `<name>`'s ring buffer. |
| `/kafka-drop <name>` | Clear `<name>`'s ring buffer. |
| `/kafka-reload` | Disconnect every consumer and reconnect (re-reads `kafka.yml`). |
| `/kafka-pause <name>` | Stop fetching new records (keep the buffer). |
| `/kafka-resume <name>` | Resume fetching for a paused consumer. |

The status line at the bottom of the TUI mirrors the same info: `kafka: events[auto]=running (12)  ops-pull[pull]=idle`.

## LLM-callable tool

`kafka_consume` is registered automatically — the LLM can peek at the ring buffer without a slash command:

```json
{
  "name": "kafka_consume",
  "parameters": {
    "consumer": "string? — name from kafka.yml",
    "limit":    "integer 1..500? — default 20",
    "since":    "ISO 8601 timestamp? — only records after this"
  }
}
```

## Environment overrides

| Variable | Effect |
|---|---|
| `KAFKA_DISABLED=1` | Skip connect on startup (config still loads). |
| `KAFKA_DEBUG=1` | Log lifecycle and connect events to stderr. |
| `KAFKA_CONFIG=<path>` | Force a specific config file. |

## Architecture

The extension registers one KafkaJS consumer per profile in `kafka.yml`. In **auto** mode each record is formatted (with the `auto.prefix`) and injected via `sendUserMessage` with the configured `deliverAs` strategy; in **pull** mode records accumulate in a per-consumer ring buffer (`maxQueue`) that the slash commands and the `kafka_consume` tool read from. The TUI status line reflects each consumer's state. Verification: the package typechecks cleanly, and a symlink at `~/.tau/agent/extensions/tau-extensions/packages/omp-kafka` makes omp auto-discover the factory at load.

## License and security

MIT — see [LICENSE](./LICENSE).

Security notes:

- SASL credentials live in `kafka.yml` — keep it at 0600 and never commit a populated one.
- In auto mode, Kafka messages become user messages in the session: only subscribe to topics you trust, since message content can steer the LLM.
- `ssl: true` + SASL for anything crossing a network boundary.
