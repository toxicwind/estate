# openfang-health — live liveness + provider audit for openfang/coyote on yote

`openfang-health.sh` probes the whole openfang/coyote stack with failfast
timeouts and writes three artifacts:

- `/home/toxic/shingle/var/openfang-health/openfang-health.json` — machine-readable
- `/home/toxic/shingle/var/openfang-health/openfang-health.html` — status page (auto-refresh 300s)
- squawk `fleet` channel — posted only on status transitions or daily digest

`loop.sh` runs the check every `OPENFANG_HEALTH_INTERVAL` seconds (default 300)
under pitchfork daemon `sovereign/openfang-health`.

## Checks

| check | what it verifies |
|---|---|
| supervisor | pitchfork.service active, pid + RSS |
| daemons | every daemon in `pitchfork list` is `running` |
| openfang_kernel | `openfang status` boots, audit trail entry count |
| agents | coyote, shingle-pilot, squawk-relay, assistant all Running |
| audit_chain | openfang audit log chain integrity OK |
| llama_swap | `:25100/v1/models` answers, model count |
| kimi_auto | resolver state.json fresh (<30 min) and healthy |
| provider_* | live/dead auth posture per cloud provider (names only, never key values) |
| yote_ep / meshub_ep / coyote_ep | `:25102/health`, `:25115` tcp, `:25143/health` |
| memory / gpu | free RAM, nvidia-smi one-liner |

Overall = OK / DEGRADED / FAIL (worst check wins). The script itself exits 1
only when the *checker* errors — a check failure is data, not a crash.

## Research lineage

- **AgentSight** (arXiv:2508.02736) — *System-Level Observability for AI Agents
  Using eBPF.* Closes the semantic gap between agent intent and low-level
  behavior; zero-SDK `top`/`strace`-like observability. Here: we link the agent
  registry (intent) to OS truth (pitchfork procs, ports, RSS) without touching
  the agent SDK.
- **AgentCgroup** (arXiv:2602.09345) — *Understanding and Controlling OS
  Resources of AI Agents.* 144 SWE tasks: OS-level execution is 56–74% of
  end-to-end latency; **memory, not CPU, is the concurrency bottleneck**;
  tool-call-driven spikes hit 15.4× peak-to-average; cgroup hierarchies aligned
  to tool-call boundaries + sched_ext/memcg_bpf_ops enforcement. Here: we
  monitor supervisor RSS and box memory pressure as first-class signals, and
  the daemon placement follows the paper's granularity lesson (per-service
  pitchfork supervision).
- **HarnessAudit** (arXiv:2605.14271) — *Auditing Agent Harness Safety.*
  Output-level eval can't see mid-trajectory violations; audits boundary
  compliance, execution fidelity, system stability across full trajectories.
  Here: we verify the audit-trail chain integrity and registry state, not just
  "process alive".

Code: AgentSight https://github.com/eunomia-bpf/agentsight ·
AgentCgroup https://github.com/eunomia-bpf/agentcgroup
