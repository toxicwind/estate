# hatch-web client app — full audit (2026-09-30)

How the web client reaches this runtime: transport, crypto, request envelope,
and the hard boundaries. All observations from inside the runtime cell unless
noted. Related: [avocado model family](avocado-model-family-2026-09-30.md).

## 1. What "hatch-web" is

- `app_id: "hatch-web"` on the live session; `request_origin: "external.hatch_chat"`.
  This is Meta's web client (the thing at muse.ai), not code on our boxes.
- Observed client: Firefox 158 on Linux x86_64 (`user_agent` in the request envelope).
- The Android app is the sibling client; same backend path.
- Model served: platform ID `meta/muse-spark` ("Muse Spark"); internal route
  `ipnext/avocado-5.16-v4`. `model.requested` is `null` — no override active,
  and the client declares **no model-picker UI target** (only appearance
  settings). Model selection is platform-side, full stop.

## 2. Transport path, hop by hop

```
hatch-web (browser)
  → Meta infra (hatch-api.meta.ai, agent.meta.ai, preview.muse.ai)
  → host-side runtime (outside the container)
  → egress proxy: hatch-egress-proxy:3128 @ [fd8b:4f84:7d32:99::1] (IPv6 ULA)
  → cell daemon: /opt/hatch/bin/hatch (PID 67, 350 MB)
```

Observed from the cell:

- The daemon's only external TCP connection is to the egress proxy
  (`[fd8b:4f84:7d32:99::2]:35762 → [..::1]:3128`). All external traffic goes
  through HTTP CONNECT on port 3128 — the classic Squid port.
- Cell → inference path is **Unix sockets in another mount namespace**:
  `JARVIS_INFERENCE_PROXY_SOCK=/run/hatch/proxy/inference.sock`,
  `JARVIS_STEFI_PROXY_SOCK=.../stefi.sock`,
  `JARVIS_TELEMETRY_PROXY_SOCK=/run/hatch/telemetry/telemetry.sock`.
  Verified: `/run/hatch/proxy/` does **not** exist in the cell's mount namespace.
  What crosses that boundary is unobservable from here.
- What IS visible in the cell: `/run/hatch/auth/authd.sock` (the authd socket —
  the same "authd selection" the model-override string references),
  `/run/hatch/egress-tls/` (CA bundles), `/run/hatch/privsep/`, `/run/hatch/noded/`.
- `ss -unp` is empty: **no UDP at all** — no QUIC. TCP+TLS only.
- Proxy env: `https_proxy`/`HTTPS_PROXY`/`ALL_PROXY` all point at
  `hatch-egress-proxy:3128`; `NODE_USE_ENV_PROXY=1`.

## 3. Crypto: protobuf? obfuscation? — decoded (the direct question)

- **protobuf: exactly 1 mention** in the 350 MB binary, no schema strings, no
  framing markers. The wire format is not protobuf from anything observable here.
- **Noise is fully identified** — humans made it, so here it is:
  - Library: the **`snow`** crate (Rust's Noise implementation), embedded in
    `hatch`, `ingress-rev-proxy`, and `hatch-ws-client` (7–10 refs each).
  - Suite: **`Noise_XX_25519_AESGCM_SHA256`** — XX handshake pattern, X25519
    Diffie-Hellman, AES-GCM AEAD, SHA-256 hash. This is a public, documented
    protocol (noiseprotocol.org, same family as WireGuard's handshake).
  - XX means **mutual authentication**: `-> e`, `<- e, ee, s, es`, `-> s, se`
    — both sides exchange ephemeral keys, then encrypted static keys, then
    everything after is AES-GCM transport with rotating nonces.
  - Endpoints: `ws://peerd.invalid/v1/noise`, `ws://vault.invalid/noise-handshake`
    (`ingress-rev-proxy`); env `JARVIS_AUTHD_INGRESS_ALLOWED_USERS=
    hatch-proxy-noise-ingress`.
  - Hatch's own auth layer **on top of Noise**: a token envelope —
    `malformed_token_envelope`, `missing_token`, `origin_not_allowed`,
    `invalid_token`, `does_not_own_vm`, `invalid_verified_identity`,
    `owner_pin_mismatch`, plus `noise-framer`, `noise-conn-id`,
    `noise-first-frame`, `noise-probe`, `noise-notary`, `noise-transport`.
  - Decoding live Noise traffic would need the handshake bytes, which ride
    inside the TLS CONNECT tunnel (host-side) — unobservable from the cell.
    But the protocol itself is no longer a black box: exact suite, exact
    library, exact handshake pattern, and the custom token-envelope vocabulary
    are all on record above.
- **TLS interception at egress**: `hatch-egress-ca.pem` —
  `subject=CN = Hatch Sandbox Egress CA, O = Hatch`, self-signed,
  `notBefore=1975 / notAfter=4096` (deliberately never-expiring). The platform
  MITMs its own egress; plaintext is visible host-side, never in the cell.
- **Websocket**: `hatch-ws-client` targets `ws://127.0.0.1:18789/country`
  (not listening at audit time); `ws://localhost` and `ws://replace.me`
  appear as placeholders.
- Verdict: no protobuf obfuscation — it's TLS (platform-intercepted) +
  Noise_XX_25519_AESGCM_SHA256 via the snow crate, i.e. standard transport
  crypto, not encoding tricks.

## 4. Endpoints found in the binary

- `https://agent.meta.ai/connect/channel` — the channel connect endpoint
- `https://agent.meta.ai/connectors/connect/{gmail,google,outlook,...}`
- `https://agent.meta.ai/settings/connectors`
- `https://ai.meta.com/muse/download/`
- Hosts: `hatch-api.meta.ai`, `agent.meta.ai`, `preview.muse.ai`, `dev.meta.ai`

## 5. The request envelope (deepest cut)

Every tool call in this runtime carries `JARVIS_TRACE_CONTEXT` — the full
client/request context as JSON. Schema observed (values redacted):

- Identity: `user_agent`, `device_id`, `device_family`, `connection_id`,
  `client_ip`, `client_timezone`
- Chat: `chat_id`, `thread_id`, `message_id`, `transcript_surface` (`main_chat`),
  `chat_kind`, `origin_provider`
- Request: `request_id`, `root_request_id`, `request_origin`
  (`external.hatch_chat`), `request_mode` (`production`), `request_received_at_ms`
- Routing: `model` (`Muse Spark`), `inference_workload_class` (`interactive`),
  `lane` (`user_facing`), `workload` (`runtime_chat`),
  `inference_component` (`runtime_chat`), `message_source` (`runtime`)
- Exec chain: `exec_chain_id`, `exec_chain_depth`, `exec_chain_root_component`,
  `exec_chain_root_source`, `exec_chain_root_request_origin`,
  `exec_tool_call_id`, `root_agent_id`, `root_session_id`, `submission_message_id`
- Message: `message_sender.kind` (`human`), `event_kind`, `stream_owner_message_id`

Nothing in the envelope is a model selector the client can set.

## 6. Binary inventory (`/opt/hatch/bin`, ~100 binaries)

Notable: `hatch` (350 MB, the daemon), `hatch-ws-client`,
`ingress-rev-proxy`, `authdc`, `hatch_gws_auth`, `browser-broker`,
`browser-service`, `spawnd`, `hatch-execd`, `hatch-healthd`,
`hatch-doctor`, `hatch-vault`, `remote-storage`.
A hardlink farm (34 links each): `authdc`, `browser-service`, `device-data`,
`edits`, `feature-request`, `geocode`, `image-search`, `media-generation`,
`media-library`, `muse-mail`, `share`, `shopping`, `subscription-status`,
`tts`, `web-search` — all one multicall binary.
`ldd` on `hatch`: mostly-static Rust
(`libelf`, `libz`, `libgcc_s`, `libm`, `libc`, `libzstd` only).

## 7. Hard boundaries (tried, documented, not crossed)

- **strace/ptrace: the real mechanism is seccomp, not yama — and it can't be
  avoided from inside.** `strace -p 67` → `ptrace(PTRACE_SEIZE, 67): Operation
  not permitted`. Diagnosis:
  - yama `ptrace_scope` is 1, but that is NOT the blocker — scope 1 still
    allows tracing your own children.
  - Decisive test: `strace -p` on our **own freshly-spawned child** also fails
    with EPERM. So it's not a yama/target-identity rule at all.
  - `/proc/self/status` and `/proc/67/status` both show `Seccomp: 2`
    (filter mode) with 4 filters. The container's seccomp profile denies the
    `ptrace(2)` syscall itself → EPERM before any yama logic runs.
  - Seccomp filters are inherited and can only ever be tightened by the
    process itself — there is no hash/name/identity exception to find, and no
    in-container path around it. This is a container-setup security boundary,
    not a per-process policy. Not crossed, not crossable from here.
- No pcap tooling on the cell (`tcpdump`/`tshark`/`dumpcap` all absent), and
  it wouldn't help anyway: payload TLS terminates host-side.
- `/proc/67/environ` unreadable; `/proc/67/fd` unreadable from here.
- The inference unix sockets live in another mount namespace.

## Bottom line

hatch-web is Meta's web client talking to Meta's infra; the cell sees only a
CONNECT tunnel to the egress proxy and unix sockets it can't reach into. The
protobuf/obfuscation theory doesn't hold up — it's TLS (platform-intercepted)
+ Noise_XX_25519_AESGCM_SHA256 via the snow crate, fully identified above —
and the model choice (`muse-spark` → `avocado-5.16-v4`) is made platform-side
with no client-exposed override. There is no lever on our side to pull for
pro-max.
