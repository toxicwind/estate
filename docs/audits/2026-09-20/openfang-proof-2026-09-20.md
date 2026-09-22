# OpenFang execution + persistence proof (2026-09-20, ~21:50–22:00 MDT)

Worker: **openfang-prover** (Ember's pack). Live evidence collected on yote via
`yote-conn exec`. No host/bridge/hatch restarts; only the OpenFang pitchfork
service was stopped/started (with liveness checks between).

## 1. What OpenFang is here

- Kernel binary: `/home/toxic/projects/rig-work/target/debug/openfang` (Rig fork, v0.6.9)
- Supervised as pitchfork daemon `sovereign/openfang` via `/home/toxic/sovereign/ops/openfang-run.sh`
- Config: `/home/toxic/sovereign/config/openfang-25196.toml` → `api_listen = "127.0.0.1:25196"`
- HOME=/home/toxic; agent definitions in `/home/toxic/sovereign/agents/*/agent.toml`
  (`/home/toxic/.openfang/agents` symlinks there)
- State on disk: `/home/toxic/.openfang/data/openfang.db` (sqlite, WAL mode)

## 2. Execution proof (all live, observed — no inference from error strings)

| Step | Evidence |
|---|---|
| Kernel serving | `GET /api/agents` → 8 agents, all `state: "Running"`, `ready: true` |
| Registry | squawk-relay, kimiclaw-1/2, rig-toolcall-verify, rig-toolcall-e2e, coyote, assistant, oracle-market (created_at 2026-09-14 → 2026-09-20) |
| Inference (chat) | `POST /v1/chat/completions {"model":"openfang:kimiclaw-1", ...}` → `{"content":"fang-probe-ok", "usage":{"completion_tokens":8,"prompt_tokens":4275}}` — full LLM loop through herd `:25100` (nex-agi/nex-n2.5-mini:free) |
| Tool execution | Agent used its `file_write` tool: wrote `PROOF123` to `/home/toxic/.openfang/workspaces/kimiclaw-1/probe-proof.txt`, replied `DONE`; file verified on disk. (Sandbox correctly refused `/tmp`.) |

**Incident found and fixed live during proof:** 5 of the 8 agents had stale model routes
(`openrouter-free/nex-agi/nex-n2.5-mini:free`, `toolcall-local/qwen3.5-9b-tool`) that
llama-swap `:25100` no longer serves (`no router for requested model`). Fixed at the
durable source of truth — the `agents/*/agent.toml` manifests (the kernel re-seeds
its registry from these TOMLs on every boot; a DB-only edit is overwritten at boot).
Fixed (5 on yote): `nex-agi/nex-n2.5-mini:free` (coyote, kimiclaw-1/2),
`qwen3.5-9b-tool` (rig-toolcall-verify, rig-toolcall-e2e).
Pushed to canonical main (4 files): kimiclaw-1/2, rig-toolcall-verify, rig-toolcall-e2e.
coyote's main copy NOT touched — its committed model (`kimi-auto`) is still served by
herd `:25100`; the yote tree has local drift on coyote, left for the owning lane.
NOT touched: `assistant` (anthropic/claude — no key path here), `squawk-relay`
(nvidia/gpt-oss-20b — model not currently served), `oracle-market` (direct Google
base_url; gemini-2.0-flash may be EOL — needs Chris's call).

## 3. Persistence proof (stop → liveness check → start cycle)

Pre-restart snapshot (21:54 MDT): 8 agents, 16 sessions, kimiclaw-1 latest session
`2026-09-21T03:54:53` (9537 bytes of message history), audit head seq 1110
hash `749d994e80b8`, 2 triggers.

Restart: `pitchfork stop sovereign/openfang` → verified PID gone + port 25196 closed →
`pitchfork start sovereign/openfang` → `/api/status` 200.

Post-restart verification — all state survived:

| Check | Before | After |
|---|---|---|
| agents | 8 (created_at 09-14→09-20) | 8, **identical created_at** |
| sessions | 16 | 16, kimiclaw-1 history 9537 bytes intact (ts `03:54:53`, pre-restart) |
| audit chain | head seq 1110 `749d994e80b8` | head seq 1119 (boot ConfigChange entries appended; hash chain continuous) |
| triggers | 2 (squawk-relay patterns) | 2, re-registered by `openfang-run.sh` on boot (kernel-memory-only upstream) |
| workspace file | `probe-proof.txt` = PROOF123 | still on disk, content intact |
| inference | `fang-probe-ok` | `POST /v1/chat/completions` post-restart → `"post-restart-ok"` |

**Reboot:** deliberately NOT tested — the reboot ban covers the physical host.
Persistence across a full host reboot is therefore unproven for the kernel process,
but all durable state (registry, sessions, audit chain, triggers-via-run.sh,
workspaces) lives on disk in `/home/toxic/.openfang` + `sovereign/agents`, and the
pitchfork supervisor restarts the daemon from that state — this is exactly what the
service-restart cycle above exercised.

## 4. Files changed in this proof

- `agents/kimiclaw-1/agent.toml`, `agents/kimiclaw-2/agent.toml`,
  `agents/rig-toolcall-e2e/agent.toml`, `agents/rig-toolcall-verify/agent.toml` — model route fixes
- `docs/openfang-proof-2026-09-20.md` — this file

Backup of the pre-proof DB kept at `/tmp/openfang-preproof-20260920.db` (yote, ephemeral).
