# MetaClaw Runtime

[![Bun Version](https://img.shields.io/badge/bun-1.4.2-black?style=for-the-badge&logo=bun)](https://bun.sh)
[![Engine](https://img.shields.io/badge/runtime-Node_22_%7C_Bun_1.4+-green?style=for-the-badge)](https://nodejs.org)
[![Protocol](https://img.shields.io/badge/protocol-Noise__XX__25519__AESGCM-blue?style=for-the-badge)](https://noiseprotocol.org)
[![Security Control](https://img.shields.io/badge/sentinel-auto__approval_engine-orange?style=for-the-badge)](https://research.meta.ai)
[![License](https://img.shields.io/badge/license-MIT-purple?style=for-the-badge)](LICENSE)

> **Zero-Browser Noise_XX WebSocket Client, Sentinel Auto-Approval Engine, and Direct VM Agent Dispatcher for Meta AI (`metaaivm.com` / Muse & Avocado).**

---

## Table of Contents

- [Overview](#overview)
- [Microarchitectural Dissection](#microarchitectural-dissection)
- [Direct Connection & Model Invocability Matrix](#direct-connection--model-invocability-matrix)
- [Sentinel Auto-Approval & Egress Engine](#sentinel-auto-approval--egress-engine)
- [Quick Start](#quick-start)
- [Wire Protocol & Handshake](#wire-protocol--handshake)
- [Gateway Method Reference (258 Routes)](#gateway-method-reference-258-routes)
- [Verification Suite](#verification-suite)
- [Configuration Reference](#configuration-reference)

---

## Overview

**MetaClaw Runtime** is a clean-room, zero-browser client and autonomous daemon for Meta's personal AI agent infrastructure (`metaaivm.com` / Muse / project "Hatch"). It bypasses web browser overhead, connects directly over encrypted Noise_XX WebSockets into your personal container VM, automates human-in-the-loop (HITL) Sentinel egress approvals, and drives the Avocado / Muse Spark 1.3 agentic loop from the terminal.

### Key Capabilities

1. **Zero-Browser Direct Connection**: Connects to `wss://hatch.metaaivm.com/v1/noise` using native Curve25519 Diffie-Hellman and AES-256-GCM encryption with notary token attestation.
2. **Sentinel Auto-Approval Engine**: Intercepts `egress.approvals` requests from the VM, automatically promoting outbound developer domains to durable `allow_always` rules in on-VM Postgres.
3. **Avocado / Agent Dispatcher**: Streams conversation turns, executes tools, queries remote workspace files (`fs.stat`, `fs.reads`), and monitors subagent transcripts without browser DOM rendering.
4. **Resilient Self-Healing**: Automated token rolling touch (every 5 min), session recovery, and retry backoff.

---

## Microarchitectural Dissection

Meta AI allocates each user a persistent, dedicated virtual machine operating under a hybrid **Cloud Hypervisor + systemd-nspawn** topology:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 Cloud Hypervisor microVM ("The Hatchling")                  │
│                                                                             │
│  Host Services (VM Mount Namespace):                                        │
│  - ingress-rev-proxy (:443 infra, :4431 data plane)                         │
│  - spawnd & hatch-execd                                                     │
│  - Sentinel egress proxy (:3128 MITM + eBPF cgroup filter)                  │
│  - PostgreSQL server (/opt/metasql on /var/lib/hatch/postgres, 194 tables)  │
│  - Local Models: all-MiniLM-L6-v2 (embeddings), jina-reranker, whisper-tiny │
│  - JARVIS_INFERENCE_PROXY_SOCK -> Meta Internal Edge (ipnext / Avocado)     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │        systemd-nspawn Runtime Cell (Tenant Container: htch-runtime)    │  │
│  │                                                                       │  │
│  │  - User: root (uid 131072 on host, unshare user/mount namespaces)    │  │
│  │  - /home/hatch (LUKS2 encrypted Reliable Volume on /dev/vdd, 100GB)   │  │
│  │  - /opt/hatch (dm-verity measured squashfs tools & skills image)      │  │
│  │  - Workspace: /home/hatch/workspace/                                  │  │
│  │  - Memory: /home/hatch/memory/ (Markdown indexed into pgvector)       │  │
│  │  - Network: veth /30 gateway -> 198.19.0.1 (Sentinel proxy)           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ Noise_XX WebSocket (:4431)
                                  │ wss://hatch.metaaivm.com
                                  │
                       [ MetaClaw Runtime Engine ]
```

---

## Direct Connection & Model Invocability Matrix

A central inquiry in agent research is whether external clients can connect directly to the VM and invoke models like **Avocado**:

| Connection Channel | Feasibility | Protocol Layer | Capabilities & Access Limits |
| :--- | :--- | :--- | :--- |
| **Noise Gateway WebSocket** (`wss://hatch.metaaivm.com/v1/noise`) | **Supported** | `Noise_XX_25519_AESGCM` | **Full Agent Loop**: Dispatches turns to Hatch daemon, queries Avocado/Muse Spark, executes workspace tools, streams NDJSON deltas. Requires valid `noiseNotaryToken`. |
| **Raw VM Ingress TCP** (`<vm_id>.metaaivm.com:4431`) | **Restricted** | TCP / Raw Noise | Edge router (`edge-metaclaw.c10r.facebook.com`) requires pre-authenticated handshake parameters. Direct TLS to 443 resets. |
| **Host-Side Inference Socket** (`JARVIS_INFERENCE_PROXY_SOCK`) | **Isolated** | Unix Domain Socket | **Inaccessible from Tenant Cell**: Socket is isolated in VM mount namespace. Tenant shell runs under unshare namespaces with filtered syscalls (`io_uring_setup`, `sys_ptrace` dropped). |
| **Sentinel Control Plane** (`/run/hatch/sentinel/...`) | **Controlled** | Unix Domain Socket / RPC | Reached via Service 1. Only Sentinel evaluates permission grants (`allow`, `deny`, `ask`). |

**Conclusion**: External clients cannot bypass the Hatch daemon to access raw model weights directly, but through MetaClaw's Noise gateway implementation, clients have unrestricted access to drive the full agentic loop, trigger Avocado tool executions, and manage container workspace files programmatically.

---

## Sentinel Auto-Approval & Egress Engine

When an agent executing inside the container triggers outbound network traffic (e.g. `npm install`, `curl`, `pip`), Sentinel halts execution if the domain is not in the managed allowlist (`managed-internal-network-policies.yaml`).

```
[ Agent in Cell: curl api.custom.io ]
                  │
                  ▼
[ Sentinel MITM Proxy :3128 ] ──> Evaluates Policy (Host not in allowlist)
                  │
                  ▼
[ Status: ASK (Creates Pending Approval) ]
                  │
                  ▼ (Noise RPC: egress.approvals)
[ MetaClaw Auto-Approve Engine ]
                  │
                  ▼
[ Decides: allow_always + destination_domain ]
                  │
                  ▼ (Noise RPC: egress.approval.decide)
[ Sentinel writes durable rule to Postgres ]
                  │
                  ▼
[ Traffic Unblocked & Persisted Permanently ]
```

---

## Quick Start

### 1. Requirements

- **Bun 1.4.2+** (recommended) or **Node.js 18+**
- Active `hatch_sess` cookie from `muse.ai`

### 2. Installation

```bash
git clone https://github.com/toxicwind/metaclaw-runtime.git
cd metaclaw-runtime
bun install
```

### 3. Configure Credentials

Export your session cookie:

```bash
export MUSE_COOKIE="your_hatch_sess_cookie_here"
```

### 4. Run the Daemon

```bash
# Verify connection and VM assignment
bun run start status

# Launch the Sentinel auto-approval daemon
bun run start daemon
```

---

## Wire Protocol & Handshake

The connection executes a formal **Noise_XX** 3-message mutual authentication sequence:

1. **Msg A (Client -> Server)**: `-> e` (Ephemeral public key, 32 bytes)
2. **Msg B (Server -> Client)**: `<- e, ee, s, es` (Ephemeral key, DH exchange, encrypted server static key)
3. **Msg C (Client -> Server)**: `-> s, se` (Encrypted client static key, authenticated payload)
4. **Transport Split**: Derives separate `SendCipher` and `RecvCipher` states with zero-nonce initialization.

Every application message is encapsulated in a Protobuf transport frame:

```protobuf
message NoiseTransportFrame {
  int64 chunk_id = 1;
  uint32 chunk_index = 2;
  uint32 total_chunks = 3;
  bytes payload = 4;
}
```

---

## Gateway Method Reference (258 Routes)

The gateway daemon multiplexes requests across 4 distinct service identifiers:

- **Service 0 (`Daemon`)**: Chat turns (`chat.stream`), session lifecycle (`sessions.list`), file operations (`fs.reads`, `fs.stat`), background cron jobs (`tasks.list`), and subagent orchestration (`subagents.list`).
- **Service 1 (`Sentinel`)**: Security governance, pending approval polling (`egress.approvals`), and permission decisions (`egress.approval.decide`).
- **Service 2 (`Vault`)**: Cryptographic storage verification (`vault.luks_status`).
- **Service 3 (`Authd`)**: Node health and attestation probes (`vm.health`, `vm.enrollment_health`).

To inspect the complete route dictionary:

```bash
bun run src/cli/index.ts routes
```

---

## Verification Suite

MetaClaw includes an automated unit and integration test suite verifying the cryptographic handshake, wire framing, Sentinel policy engine, and token decoding:

```bash
npm test
```

Expected output:
```
=== MetaClaw Runtime Test Suite ===

[Protocol: Noise_XX Cryptography]
  [PASS] generates valid X25519 keys and performs Diffie-Hellman
  [PASS] executes complete 3-message Noise_XX handshake and transport split

[Protocol: Wire Framing & Protobuf Codec]
  [PASS] encodes and decodes varints correctly
  [PASS] packs and unpacks NoiseTransportFrame binary frames
  [PASS] serializes ServiceRequest structure into protobuf bytes

[Sentinel: Auto-Approval & Policy Engine]
  [PASS] whitelists developer registry domains to allow_always
  [PASS] auto-approves unknown outbound domains with durable promotion
  [PASS] deduplicates approvals and handles scope fallback

[Auth & Session: JWT & Notary Decoding]
  [PASS] decodes notary token payload from wtf.txt

Results: 9 passed, 0 failed.
```

---

## Configuration Reference

| Environment Variable | Default Value | Description |
| :--- | :--- | :--- |
| `MUSE_COOKIE` | `""` | `hatch_sess` cookie for authentication |
| `MUSE_GATEWAY_HOST` | `hatch.metaaivm.com` | Meta AI VM gateway hostname |
| `MUSE_VM_ID` | `""` | Optional explicit VM UUID override |
| `METACLAW_APPROVAL_SCOPE` | `destination_domain` | Default Sentinel approval scope (`destination_domain` or `session`) |
| `METACLAW_POLL_INTERVAL_MS`| `10000` | Sentinel approval polling frequency in milliseconds |

---

## License

MIT © Toxic Wind.
