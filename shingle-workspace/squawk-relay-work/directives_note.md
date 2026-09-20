
## 2026-09-14 14:56 MDT — SQUAWK RELAY COMPLETE (side-chat relay worker 376a3e09) — DEPLOY TRIGGER

Chris-confirmed fat long-poll is BUILT, committed, pushed: toxicwind/squawk @ aadc1cd.

WHAT SHIPPED (repo-code lane):
- chat.py relay-in: Muse->Squawk through the normal signed/sequenced/DAG/Lamport post path. Relay identity signs; human travels as relayed_from: muse-side-chat + human: <name>. --text "..." or --text - (stdin).
- chat.py relay-out --channel fleet --since N --format json: stable machine JSON {cursor, messages[]}; verifies sigs vs roster/revocation; priv-* decrypted only after verify; sealed envelopes unsealed via relay identity.
- fleet_identity v3 (NEW): relayed_from/human are HMAC-covered (fleet-chat-v3 canonical form). Tampering invalidates the signature (proven by smoke test). verify falls back v3->v2->v1 for pre-upgrade messages. relay-out/feed DROP relay attribution that is not v3-signed (fail closed on attribution, verdict stands).
- squawk_feed.py: bearer-authed FAT long-poll (stdlib only). GET /squawk-feed/ping = public content-free {seq:N}. GET /squawk-feed/wait?since=N and /squawk-feed/subscribe?since=N (one handler) REQUIRE Authorization: Bearer <token> — constant-time compare, bare 404 on missing/invalid, endpoint never reveals itself. Token ONLY from SQUAWK_FEED_TOKEN env (pitchfork); server refuses to start without it; never a CLI flag, never logged, never in repo. Fat response {seq:M, messages[]}: per-message seq on EVERY envelope, <=50 msgs with seq>since (oldest first), M = last msg seq (client re-polls to drain), text capped 500 chars, inotify wake on post (~55s hold). Sealed msgs unsealed server-side with relay identity; unopenable ride as {sealed:true, body:null} — ciphertext never served.
- SEAL STATUS: squawk_seal.py (NaCl sealed-box) landed on origin and is WIRED IN (fleet_relay.unseal_message parses real envelopes). relay.seal.key NOT YET MINTED in /home/toxic/.shingle/squawk-root/keys/ — bootstrap lane: run squawk_seal.py keygen relay. Until then sealed-to-relay msgs stay sealed:true.
- ENV CONTRACT: every relay/seal/feed invocation must see FLEET_KEYS_DIR=/home/toxic/.shingle/squawk-root/keys (code falls back to <root>/keys; explicit env is the contract). Canonical: root /home/toxic/.shingle/squawk-root, keys same/keys (relay.key minted 14:02, do NOT re-mint), repo clone /home/toxic/squawk.
- HARD RULE (Chris): no unauthenticated unsealed content, ever. No exceptions.

VERIFIED: feed tests 9/9 OK (auth 404s, alias, fat shape, wake-on-post, timeout, 500-truncation, sealed fail-closed + unseal roundtrip); smoke_relay.py OK incl. tamper->signature invalid; squawk_seal selftest OK; py_compile OK. Full suite: 6 failures + 74 errors, ALL pre-existing in lease/task/path-lock/state areas (their tip b7ce5d0 alone: 8 + 95) — zero in relay/feed/identity/chat paths. Temp edit scripts removed. Backup branch backup/main-20260914 on origin.

DOCS: README.md "Muse relay (relay-in / relay-out) + squawk-feed" — commands, JSON schema, trust model, pitchfork stanza, canonical paths.

DEPLOY TRIGGER (hosting lane): replace/upgrade the [daemons.squawk-feed] stanza:
  run = "exec python3 /home/toxic/squawk/chat.py squawk-feed --root /home/toxic/.shingle/squawk-root --channel fleet --port 25135"
  env = { SQUAWK_FEED_TOKEN = "<from host secret store, never the repo>", FLEET_KEYS_DIR = "/home/toxic/.shingle/squawk-root/keys" }
  ready check: GET /squawk-feed/ping (public, content-free).
  Funnel: route /squawk-feed/* (ping/wait/subscribe) — SAFE to expose publicly: bearer gate 404s without token. NOTE: pitchfork generator is RETIRED (2026-09-14) — edit pitchfork.toml directly now.

CONFLICT DISCLOSURE (no clobbering done — merge aadc1cd keeps everything): the 14:4x main-lane deployment (feed.py -> outbox.jsonl, /seq public via funnel, /messages+/wait 502 off-funnel, content via bridge) is LIVE on :25135 and UNTOUCHED. Sibling's relay/feed.py (cab3880: /seq public, /messages localhost-only, /wait content-free long-poll, NO bearer auth) is preserved in repo under relay/. Neither matches Chris's confirmed bearer-authed fat design (content served over HTTP behind bearer, 404 otherwise). Hosting/coordinator: deploy the aadc1cd squawk-feed.py stanza above, then retire or repoint the old feed.py daemon + funnel /seq route. The old 5s poll hook on /seq should move to the fat /wait (bearer) or /ping.
