# POST-RECOVERY ADDITIONS AUDIT — debate bedf89a9 (bid)

**Auditor:** oracle lane-3 (acting ralph oracle per Chris 2026-09-19)
**Date:** 2026-09-19 01:46 UTC
**Subject:** Yote (Telegram gateway, 127.0.0.1:25102) — what the bids proposed vs. what still needs building now that yote is UP

---

## 1. Live state (verified 2026-09-19 01:46:24 UTC via bridge)

- **Yote UP:** 25102 LISTEN (bun pid 796770, started 01:38:44Z), /health 200 (0.2ms)
- **Recovery timestamp:** 2026-09-19T01:38:44.708Z (from `/home/toxic/sovereign/projects/yote/logs/yote.log`)
- **Recovery was TARGETED, not systemic:** `pitchfork list` shows:
  - sovereign/yote → **running**
  - sovereign/herd → **stopped**
  - sovereign/mesh-hub → **stopped**
  - sovereign/sovereign-router → **stopped**
  - sovereign/shep → running
- **Config unchanged:** `[daemons.yote]` still `depends=["shep"]`, `retry=true`, `auto=["start"]`. No hardening applied.
- **Supervisor blind:** `/home/toxic/sovereign/logs/pitchfork-supervisor.log` contains ZERO yote lines. The recovery is invisible in supervisor logging.

---

## 2. Post-recovery additions proposed by each bid

| Bid | Proposed addition | Still needed? | Status | Priority |
|---|---|---|---|---|
| seq 5 lane-4 (WINNER) | Dependency re-fire hardening (gate must re-evaluate when shep recovers) | **YES — critical** | Proposed only, not built | **MUST-BUILD** |
| seq 5 lane-4 | Pre-start port check (prevent EADDRINUSE class) | **YES** | Proposed only, not built | MUST-BUILD |
| seq 5 lane-4 | Telegram backoff logic (survive Bad Gateway / Gateway Timeout without silent death) | **YES** | Proposed only, not built | MUST-BUILD |
| seq 6 lane-8 | Shep-dependency fix-path confirmation + duplicate-holder prevention | Partially | Forensics done (negative result: zero shep refs in yote src); prevention not built | Nice-to-have |
| seq 9 lane-2 | Process-level monitoring + crash-loop detection | Partially | Forensics done (125 poll-starts quantified); ongoing monitoring not built | Nice-to-have |
| seq 3 lane-7 | Verification probes (25102, /health, Telegram poll) | Done (one-time) | **COMPLETE** — 3/3 passed 01:41–01:46Z | Convert to ongoing monitoring |
| seq 7 lane-5 | Log forensics classification | Informational | Done (death sequence classified) | — |
| seq 10 lane-6 | Repair execution (manual restart + supervise) | **MOOT** | Self-recovered 01:38:44Z | — |

---

## 3. Key evidence: the gate is confirmed non-re-firing

The single strongest post-recovery finding:

> Shep recovered ~01:05Z. Yote was manually started 01:38:44Z. **Forty minutes later, herd, mesh-hub, and sovereign-router — all `depends=["shep"]` — remain `stopped`.**

If pitchfork's dependency gate were level-triggered (continuously re-evaluating), all four would have started when shep became healthy. They did not. This confirms lane-4's "edge-triggered gate never re-fires" hypothesis with live fleet-wide evidence, not just yote-specific inference.

**Consequence:** The root cause is not yote-specific. It is a **pitchfork supervision defect affecting every dependency-gated daemon.** Lane-4's hardening must be applied fleet-wide, not scoped to yote.

---

## 4. Verdict: must-build vs nice-to-have vs moot

### MUST-BUILD (recurrence prevention)
1. **Dependency re-fire mechanism** (lane-4 seq 5) — fleet-wide, not yote-only. Either a pitchfork-native "watch dependency and start when ready" or an external watcher. Without this, the next shep outage will strand every gated daemon again.
2. **Pre-start port check** (lane-4 seq 5) — the Sep-17 EADDRINUSE death class is unaddressed.
3. **Telegram backoff** (lane-4 seq 5) — the Sep-18 silent death (Bad Gateway ×3 → Gateway Timeout → no crash trace, supervisor unaware) will recur on the next Telegram degradation.

### NICE-TO-HAVE
4. **Duplicate-holder prevention** (lane-8 seq 6) — the EADDRINUSE implies a transient duplicate; a lockfile or pre-start port check covers most of it.
5. **Ongoing health monitoring** (lane-2 seq 9, lane-7 seq 3 evolved) — the one-time verification passed; convert the three probes into a standing check.

### MOOT
6. **Manual repair execution** (lane-6 seq 10) — superseded by self-recovery.

---

## 5. Gap analysis: what the bids missed

1. **Fleet scope.** Every bid scoped to yote. The live evidence shows three other daemons still stranded. The award should explicitly expand lane-4's hardening to all `depends=["shep"]` daemons (herd, mesh-hub, sovereign-router) at minimum.
2. **Supervisor observability.** The pitchfork supervisor logged zero lines about yote's death or recovery. No bid proposed supervisor-level death detection (the "silent death" was invisible to the supervisor that owns the daemon). A dead-man's-switch or liveness log line per daemon would close this.
3. **Recovery trigger attribution.** The 01:38:44Z start has no shell-history trace and no supervisor log line — it was likely a bridge `pitchfork start` from an agent session. No bid proposed audit-logging for manual daemon starts, leaving future recoveries unattributable.
4. **Immediate action available now:** `pitchfork start` herd, mesh-hub, sovereign-router — three daemons are still down with a healthy dependency. This is zero-risk (same command that recovered yote) and should not wait for the hardening build.

---

## 6. Assessment of lane-4's awarded bid (seq 5)

**Supported by evidence:** Yes. The edge-triggered gate hypothesis is now confirmed fleet-wide (three daemons still stopped post-shep-recovery). The two-stage root cause (EADDRINUSE → Telegram silent death) matches the logs exactly. `retry_count=0` with status `stopped` confirms retry only covers crash loops, not gate-blocked or silently-dead states.

**Is the hardening the right fix?** Yes for yote, but **underscoped** — it must cover all gated daemons. The pre-start port check and Telegram backoff are correctly identified as the two death classes.

**Gaps in their root cause:** (a) did not identify the fleet-wide stranding (only yote); (b) did not address supervisor observability blindness; (c) the "immediate `pitchfork start`" step was framed as part of the bid, but the three still-stopped daemons need it now, independent of the hardening build.

---

**Recommendation to the oracle:** Accept this audit as a bid. Expand lane-4's award scope to fleet-wide dependency-gate hardening. Authorize immediate `pitchfork start` for herd, mesh-hub, sovereign-router as zero-risk maintenance (same mechanism that recovered yote).
