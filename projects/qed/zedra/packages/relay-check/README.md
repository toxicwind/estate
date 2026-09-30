# relay-check

<div align="right">

![sovereign](https://img.shields.io/badge/sovereign--projects-blue?style=for-the-badge)
![bun](https://img.shields.io/badge/bun-000000?style=for-the-badge)
![typescript](https://img.shields.io/badge/typescript-3178C6?style=for-the-badge)
![ssh](https://img.shields.io/badge/ssh-2D2D2D?style=for-the-badge)

</div>

**Run on your machine — SSH to the relay VMs and print live metrics or history.** The relay fleet lives on cloud instances; this is the laptop-side CLI that reaches into each one over SSH and shows you what's happening right now (or the last 24h from the metrics log). History is written by the [`relay-monitor`](../relay-monitor/README.md) sidecar.

## Architecture

```mermaid
flowchart LR
    CLI["bun cli.ts\nthis package"] -->|SSH| AP1["zedra-relay-ap1"]
    CLI -->|SSH| US1["zedra-relay-us1"]
    CLI -->|SSH| EU1["zedra-relay-eu1"]
    AP1 --> M1["metrics.jsonl\n(written by relay-monitor)"]
    US1 --> M2["metrics.jsonl"]
    EU1 --> M3["metrics.jsonl"]
```

Each instance must resolve as SSH host `zedra-relay-<instance>` in `~/.ssh/config` (see [`deploy/relay/README.md`](../../deploy/relay/README.md) for the alias setup).

## Quick Start

```bash
INSTANCES=sg1,us1,eu1 bun cli.ts
INSTANCES=sg1,us1,eu1 bun cli.ts ap1
INSTANCES=sg1,us1,eu1 bun cli.ts --history
```

## Usage

```bash
INSTANCES=sg1,us1,eu1 bun cli.ts          # live metrics, all instances
INSTANCES=sg1,us1,eu1 bun cli.ts ap1      # live metrics, one instance
INSTANCES=sg1,us1,eu1 bun cli.ts --history       # last 24h from metrics.jsonl
INSTANCES=sg1,us1,eu1 bun cli.ts ap1 --history 6 # last 6h, one instance
```

## Config

| Env / arg | Purpose |
|---|---|
| `INSTANCES` | Comma-separated instance list (`sg1,us1,eu1`); each becomes SSH host `zedra-relay-<instance>` |
| `<instance>` positional | Check a single instance |
| `--history [hours]` | Read `metrics.jsonl` history instead of live metrics (default 24h) |

## Dev / Contributing

- Bun + TypeScript (`cli.ts`, `package.json`, `tsconfig.json` in this package).
- Keep this package laptop-only — it must never end up in the deploy bundle (see `deploy/relay/README.md` directory structure).

## License + Security

MIT (see [`LICENSE`](../../LICENSE)).

**Security posture:** this tool only *reads* — SSH in, print metrics, leave. It uses your existing `~/.ssh/config` identities and never stores credentials. The instances it touches are the same ones `deploy/relay/deploy.sh` manages.
