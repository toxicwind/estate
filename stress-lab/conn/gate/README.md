# hatch-gate — hatch-aware zero-trust inbound origin gate

**Admit known-hatch, quarantine unknown.** This is a trusted-list authorization layer,
NOT a blind allow-queue. We DO control the `hatch` identity (muse-1 cell `100.94.78.109`
+ the yote-conn/doorbell client-credentials path), so cross that with the connecting
origin and only admit when origin is a trusted hatch/internal identity; everything else
is **quarantined and logged**, never auto-admitted.

- Pattern-informed: forge-borrow raced **Agent Identity Protocol (AIP)** for MCP/A2A
  identity verification + **Zero-Trust Runtime Verification** — separate authority check
  before admitting to a privileged sink. The gate is that authority boundary.
- `hatch_gate.py --peer <ip>` — exit 0 = admit (trusted hatch), exit 2 = quarantine.
- `gate_workflow.sh <ip>` — workflow wrapper printing ADMIT/QUARANTINE.
- Env: `HATCH_TRUSTED_PEERS` (default `100.94.78.109`), `HATCH_BEARER`/`--bearer-file`
  (doorbell client_credentials), quarantine log `/tmp/hatch-gate-quarantine.jsonl`.
