# keep

**keep is the single home for secrets.** Nothing secret ever lives in chat,
env files, or repo history again — every service, agent, and daemon references
secrets *by name* through keep's API, and keep holds the only encrypted copy.

## Why

Tokens keep leaking into GitHub repos and chat logs (see the 2026-09-17
credential incidents). The fix is structural, not procedural: there is exactly
one place secrets are allowed to exist — keep. Everything else stores a name.

- Values are **age-encrypted** (X25519) before touching SQLite; only
  ciphertext is persisted.
- Plaintext lives only inside `zeroize::Zeroizing` wrappers in memory.
- The API never logs a secret value — log lines carry the secret *name* only.
- `GET /secrets` returns metadata (name, purpose, rotation dates), never values.

## Layout

```
tools/keep/
  Cargo.toml
  src/
    main.rs    — startup, env config, axum + rustls serve
    api.rs     — HTTP routes + bearer auth middleware
    crypto.rs  — age encrypt/decrypt, identity loading
    store.rs   — SQLite persistence (ciphertext only)
```

## Build

```bash
cd tools/keep
cargo build --release
```

Requires Rust 1.70+ (2021 edition).

## Run

```bash
# one-time: generate an age identity
cargo run --bin genkey   # prints KEEP_AGE_IDENTITY=... — store it in your vault
# (or use age-keygen from the rage package)

export KEEP_API_TOKEN="$(head -c 48 /dev/urandom | base64)"  # >= 32 chars
export KEEP_AGE_KEY_FILE=/secure/path/keep-age.key
export KEEP_DB_PATH=/var/lib/keep/keep.db
# optional: bind + TLS
export KEEP_BIND=127.0.0.1:25900
export KEEP_TLS_CERT=/path/to/cert.pem
export KEEP_TLS_KEY=/path/to/key.pem

./target/release/keep
```

Without `KEEP_TLS_CERT`/`KEEP_TLS_KEY` it serves plaintext HTTP on localhost
with a loud warning — fine for local dev, not for production.

## API

All routes except `/health` require `Authorization: Bearer $KEEP_API_TOKEN`.

| Method | Path                   | Body                  | Returns                          |
|--------|------------------------|-----------------------|----------------------------------|
| GET    | /health                | —                     | `ok`                             |
| PUT    | /secrets/:name         | `{value, purpose?}`   | secret metadata                   |
| GET    | /secrets/:name         | —                     | `{value}` (authenticated only)    |
| GET    | /secrets               | —                     | metadata list — **never values**  |
| POST   | /secrets/:name/rotate  | `{value}`             | secret metadata (version bumped)  |

Example:

```bash
curl -H "Authorization: Bearer $KEEP_API_TOKEN" -X PUT \
  -d '{"value":"gsk_live_...","purpose":"groq key for herd lane"}' \
  http://127.0.0.1:25900/secrets/groq-main

curl -H "Authorization: Bearer $KEEP_API_TOKEN" \
  http://127.0.0.1:25900/secrets   # metadata only
```

## Roadmap (not this scaffold)

- mTLS / SPIFFE for service-to-service auth instead of a shared bearer token
- Audit log of every read (who, when, which name — never values)
- Rotation webhooks and TTL/expiry enforcement
- Backup/restore of the encrypted DB + identity escrow
