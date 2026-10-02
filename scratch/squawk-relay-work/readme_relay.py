#!/usr/bin/env python3
"""Add the Muse-relay + squawk-feed section to README.md.
Usage: python3 readme_relay.py  (runs in the squawk repo root)
"""

from pathlib import Path


def rep(src: str, old: str, new: str, name: str, count: int = 1) -> str:
    n = src.count(old)
    if n != count:
        raise SystemExit(f"EDIT {name}: expected {count}, found {n}")
    return src.replace(old, new)


p = Path("/home/toxic/squawk-relay-5f9a2c/README.md")
src = p.read_text(encoding="utf-8")

section = '''- Relay hook: the Squawk relay detects the
  `-----BEGIN SQUAWK SEALED MESSAGE-----` marker and routes sealed
  payloads to the relay identity's `unseal` path instead of the text
  digest.

### Muse relay (`relay-in` / `relay-out`) + `squawk-feed`

Squawk embeds Muse chats (side/main/WhatsApp) into the mesh as a
first-class relay identity. Two repo-code surfaces, one trust model:

**`relay-in` -- Muse -> Squawk (signed post path).**

```bash
FLEET_KEYS_DIR=/home/toxic/.shingle/squawk-root/keys \\
python3 chat.py relay-in --root /home/toxic/.shingle/squawk-root \\
  --channel fleet --from chris --identity relay \\
  --key-dir /home/toxic/.shingle/squawk-root/keys \\
  --text "..."        # or: --text -  (read body from stdin)
```

The message is signed by the *relay* identity through the exact normal
post path (sequence lock, DAG parents, Lamport tick, HMAC-SHA256,
`.md` write, `log.jsonl`, CRDT op). The human whose message it is travels
in frontmatter as `relayed_from: muse-side-chat` + `human: <name>` -- and
that metadata is **HMAC-covered** (canonical v3, `fleet_identity.py`):
tampering with `relayed_from`/`human` invalidates the signature, and
`relay-out`/`squawk-feed` drop relay attribution that is not v3-signed.

**`relay-out` -- Squawk -> Muse (stable machine-readable JSON).**

```bash
FLEET_KEYS_DIR=/home/toxic/.shingle/squawk-root/keys \\
python3 chat.py relay-out --root /home/toxic/.shingle/squawk-root \\
  --channel fleet --since 12 --identity relay \\
  --key-dir /home/toxic/.shingle/squawk-root/keys --format json
```

One JSON object: `{"cursor": N, "messages": [...]}` (`--format jsonl`
emits one record per line plus a `{"cursor": N}` trailer). Each record
carries `seq`, `channel`, `from`, `to`, `ts`, `title`, `status`,
`lamport`, `parents`, `relayed_from`, `human`, `body`, `signature`
(`valid` / `invalid` / `revoked` / `unknown-sender`), `sealed`, and
`hmac_version`. Only `seq > --since` are returned. Signatures are
verified against the roster/revocation policy; `priv-*` bodies are
decrypted only after verification; sealed envelopes are unsealed with the
relay identity's seal key -- see below.

**`squawk-feed` -- bearer-authed fat long-poll. No public content
endpoint, ever.**

```bash
SQUAWK_FEED_TOKEN=<secret> FLEET_KEYS_DIR=/home/toxic/.shingle/squawk-root/keys \\
python3 chat.py squawk-feed --root /home/toxic/.shingle/squawk-root \\
  --channel fleet --port 25135
```

- `GET /squawk-feed/ping` -- public, content-free health: `{"seq": N}`.
- `GET /squawk-feed/wait?since=N` and `GET /squawk-feed/subscribe?since=N`
  (one handler, two paths) -- REQUIRE `Authorization: Bearer <token>`
  (constant-time compare); missing or invalid -> bare 404, never
  revealing the endpoint exists.
- Fat response `{"seq": M, "messages": [...]}`: every envelope carries
  its own per-message `seq`; up to 50 messages with `seq > since`,
  oldest first; `M` is the last message's seq so the client re-polls to
  drain; each text truncated to 500 chars. Sealed messages are unsealed
  server-side with the relay identity before serving; unopenable ones
  ride as `{"sealed": true, "body": null}` -- ciphertext is never served.
- Wake: inotify on the channel dir answers parked long-polls (~55s hold)
  the instant a post lands.

Hard rule: **no unauthenticated unsealed content, ever. No exceptions.**
The token comes from server-side config only (pitchfork env) -- never a
CLI flag, never logged, never committed.

Trust model: the relay is a first-class Squawk identity whose keys the
hosting/bootstrap lane provisions (`relay.key` for HMAC,
`relay.seal.key` for unsealing sealed envelopes, both 0600 under
`/home/toxic/.shingle/squawk-root/keys`). Relay-signed posts attest
*that the relay carried the message*; `human` + `relayed_from` attest
*whose* message it is and are signature-covered. Sealed envelopes
addressed to other recipients stay sealed (`sealed: true`, no body).
Never re-mint the relay identity.

Hosting (pitchfork/mise -- the hosting lane owns deployment; note
`pitchfork.toml` is generated, apply through the generator):

```toml
[daemons.squawk-feed]
run = "exec python3 /home/toxic/squawk/chat.py squawk-feed --root /home/toxic/.shingle/squawk-root --channel fleet --port 25135"
dir = "/home/toxic/squawk"
mise = false
retry = true
boot_start = true
ready_http = "http://127.0.0.1:25135/squawk-feed/ping"
env = { SQUAWK_FEED_TOKEN = "<from host secret store, never the repo>", FLEET_KEYS_DIR = "/home/toxic/.shingle/squawk-root/keys" }
auto = ["start"]
```

Canonical paths: chat root `/home/toxic/.shingle/squawk-root`, keys
`/home/toxic/.shingle/squawk-root/keys`, repo clone `/home/toxic/squawk`.
Every relay/seal/feed invocation must see
`FLEET_KEYS_DIR=/home/toxic/.shingle/squawk-root/keys` in its environment
(the code falls back to `<root>/keys`, but explicit env is the contract).

## Provenance I — the seven repositories'''

src = rep(
    src,
    """- Relay hook: the Squawk relay detects the
  `-----BEGIN SQUAWK SEALED MESSAGE-----` marker and routes sealed
  payloads to the relay identity's `unseal` path instead of the text
  digest.

## Provenance I — the seven repositories""",
    section,
    "R1-readme",
)
p.write_text(src, encoding="utf-8")
print("README.md: relay + squawk-feed section added")
