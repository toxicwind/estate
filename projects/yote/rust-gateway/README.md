# Yote — Unified Messaging Gateway

> Extracted from [OpenFang](https://github.com/toxicwind/openfang) `crates/openfang-channels`.  
> Telegram + Discord gateway unified into a single service.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Telegram   │────→│             │     │                 │
│   Bot API   │     │   Yote      │────→│  LLM (llama-    │
└─────────────┘     │  Gateway    │     │   swap :25100)  │
┌─────────────┐     │             │     │                 │
│   Discord   │────→│             │     │                 │
│  Gateway    │     │             │     │                 │
└─────────────┘     └─────────────┘     └─────────────────┘
```

## Quick Start

```bash
git clone https://github.com/toxicwind/yote.git
cd yote
cargo build --release

# Configure
export TELEGRAM_BOT_TOKEN=your_token
export DISCORD_BOT_TOKEN=your_token
export LLM_ENDPOINT=http://127.0.0.1:25100/v1

# Run
./target/release/yote
```

## Ports (Sovereign SSOT)

| Service | Port | Env Var |
|---------|------|---------|
| Yote HTTP API | 25102 | `YOTE_PORT` |

## License

Apache-2.0 OR MIT (same as OpenFang)
