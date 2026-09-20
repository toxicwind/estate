# Canary Migration Plan — `kimi-auto-resolver` (pitchfork daemon `sovereign/kimi-auto-resolver`)

**Status:** DESIGN ONLY — drafted 2026-09-19, **not executed**. Ready-to-execute: an operator
runs the pre-flight checklist, then Phase 0.
**Track:** 5 (canary migration plan) · **Owner:** Ember worker · **Coordinator:** parent orchestrator
**Host:** yote (awrawr-pc) · **Daemon:** `sovereign/kimi-auto-resolver` → `/home/toxic/kimi-auto/loop.sh`
**Related todos:** `[kimi-auto] done` (systemd→pitchfork migration, the precedent this plan generalizes),
`[kimi-auto] in-progress` (herd surface), `[Agent2-openfang] pending` (canary migration plan — this doc satisfies it)

**Hard limits honored (non-negotiable):** never kill squawk processes · never touch port 443
(tailscaled) · never break `/exec-ws` (awrawr-ws-exec excluded from candidacy) ·
never trust a credential-shaped value (canary = honeytoken discipline applies to any secret-adjacent field).

---

## 1. Why this worker — blast-radius analysis

### 1.1 Candidates considered

| Worker type | Critical? | Blast radius if broken | Rollback ease | Verdict |
|---|---|---|---|---|
| `awrawr-ws-exec` (exec bridge) | **Critical infra** | Total: hatch↔yote control plane dead | Hard (token re-mint dance) | **EXCLUDED** — hard limit: never break the bridge |
| `squawk-ws` / `squawk-feed` / `squawk-ws-client` | Comms infra | Fleet chat + relay dead | Medium | **EXCLUDED** — never kill squawk |
| `tailscaled` / port 443 serve map | **Critical infra** | All tailnet ingress dead | Hard | **EXCLUDED** — never touch 443 |
| `herd` (model herd :25100) | High | All local inference dead | Medium | Rejected — too central; every agent route depends on it |
| `paper-poller` | Low | Research feed stalls; has its own watchdog | Easy | Deferred — valid second candidate, but serves Chris's live research loop |
| **`kimi-auto-resolver`** | **Low** | **Only `model=kimi-auto` alias resolution** | **Easy (file restore + `pitchfork restart`)** | **SELECTED** |

### 1.2 Why kimi-auto-resolver is the safest first canary

1. **Blast radius is a named alias, not a substrate.** The resolver's only output is
   `~/.local/share/kimi-auto/state.json` ("which Kimi model is fastest-healthy right now").
   Verified 2026-09-19: `shim.py` (herd sidecar) and the Tau extension (`packages/tau-kimi-auto`)
   are the only consumers. If resolution breaks, **only requests explicitly addressed to
   `model=kimi-auto` fail (fail-loud 503 by design)** — pinned models, the herd default,
   direct NIM routes, and every other daemon are untouched.
2. **Migration precedent exists.** It was converted raw-systemd → pitchfork daemon
   `[daemons.kimi-auto-resolver]` on 2026-09-20 with zero consumer changes. The rollback
   primitive (restore files + supervisor restart) is already proven by that migration.
3. **Atomic, observable state.** `resolver.py:write_state_atomic` uses `mkstemp` + `os.replace`
   — every state flip is atomic, so a writer swap can never tear a read. Each cycle emits a
   self-describing health record (`healthy`, `updated_at`, per-candidate `latency_ms`/`note`).
   The worker is its own telemetry source (eBeeMetrics lineage: QoS made observable without
   extra instrumentation — §9).
4. **Fast signal.** 15-minute audit cadence (env `KIMI_AUTO_INTERVAL=900`) → 8 bake cycles ≈ 2h.
   A canary that needs a week to judge is a paper canary; this one judges in an afternoon.
5. **Per-attempt deadlines already exist.** `resolver.py:PROBE_TIMEOUT = 60` — failfast is
   first-class in the worker, matching the yote AGENTS.md rule. The canary inherits it.

### 1.3 What "migration" means here

Future changes to this worker (new resolver logic, new candidate sources, new probe cadence,
herd endpoint changes) are the migration payload. This plan is the reusable template:
**every future kimi-auto-resolver change ships via this canary first**, then the pattern
extends to `paper-poller` and other non-critical workers.

---

## 2. Canary pattern: shadow sidecar ("dark launch")

A request-traffic canary (Argo/Flagger weighted routing) does not apply: the resolver has no
request traffic. The unit of "traffic" is **audit cycles**. The plan therefore uses a
**shadow deployment**:

```
Phase 0          Phase 1 (shadow)              Phase 2 (flip)                 Phase 3 (promote)
stable ──►       stable ──► state.json          canary ──► state.json          canary ──► state.json
state.json       canary ──► state.json.canary   stable ──► state.json.stable   (pitchfork-managed,
                 (no consumers read it)        (hot fallback)                 stable archived)
```

- **Phase 1:** vNext resolver runs as a sidecar loop writing `state.json.canary`. Zero consumer
  impact. The automated judge (§4) compares canary vs stable every cycle.
- **Phase 2:** writers swap. Canary writes the live `state.json`; the stable loop keeps running,
  writing `state.json.stable` as a hot fallback. Consumer impact begins here — hence the
  tightened gates.
- **Phase 3:** `pitchfork.toml`'s daemon block points at the vNext files; stable artifacts
  archived; 24h soak; close-out.

**Traffic-shaping lineage** ("Unfair by design", arXiv:2605.02377): the canary deliberately
gets *unfair* scheduling — `nice +19`, `ionice -c3`, and a cycle offset of `INTERVAL/2`
(450s) from stable — so it reaches statistical confidence on spare capacity **without**
perturbing the stable worker or doubling instantaneous external probe load (see RT2, §8).

---

## 3. Phased rollout — percentages, bake times, promotion gates

"Percentages" here = share of *writes to the live state file* (the resolver's traffic).

| Phase | Canary share of live writes | Bake | Promotion gate (ALL must hold) |
|---|---|---|---|
| 0 — Baseline | 0% (shadow infra only) | 2 stable cycles (~30 min) | Baseline snapshot captured: 2 consecutive `healthy:true` states, probe-latency distribution recorded, `.canary-baseline-<ts>/` snapshot + sha256 manifest written |
| 1 — Shadow | 0% (writes `state.json.canary` only) | **min 8 cycles (~2h); recommended 24h** (see RT4) | G1 freshness · G2 self-health ≥7/8 · G3 judge score ≥0.90 · G4 novelty review clear · G5 consumer dry-run 8/8 · G6 resource cap held |
| 2 — Writer flip | **100%** (stable demoted to `state.json.stable`) | 2 cycles (~30 min) | G1 (≤1.5×interval) · G2 `healthy:true` 2/2 · G5 live consumer probes 2/2 · zero `healthy:false` |
| 3 — Promote + soak | 100% (pitchfork-managed vNext) | 24h soak | No rollback trigger fires for 24h; close-out checklist done |

**Anti-paper-canary rule** (each gate needs all four: named metric, numeric threshold, bounded
window, automated trigger — §9): the table above names the metric and threshold; §4 binds the
window and the automated trigger.

**Progress deadline** (Argo `progressDeadlineSeconds` lineage): if any phase fails to advance
within 2× its bake time, the rollout auto-aborts to rollback (stuck ≠ safe).

---

## 4. Automated health gates — the judge

Lineage: Netflix/Google **Kayenta** — data validation (NODATA) → data cleaning → pairwise
statistical comparison (Mann-Whitney U; Pass/High/Low) → score = passes/total. Our analyzer
(`/home/toxic/kimi-auto/canary/analyze.py`, spec below) implements the same pipeline over
audit cycles instead of request metrics.

### 4.1 Gate definitions (exact thresholds)

- **G1 — Freshness (liveness, failfast):** `now - updated_at ≤ 1.5 × KIMI_AUTO_INTERVAL`
  (≤22.5 min at default). Breach = the loop is dead regardless of what it last wrote.
- **G2 — Self-health:** `healthy == true`. Phase 1: ≥7 of 8 cycles. Phase 2/3: every cycle.
- **G3 — Judge score (canary vs baseline):** per cycle, for each candidate probed by *both*
  versions, compare `latency_ms` and `ok`: classify **Pass** (|Δ| within 2× baseline IQR and
  same ok-ness), **High** (canary worse), **Low** (canary better). Score =
  `Pass / (Pass + High + Low)` over the bake window; **promote iff score ≥ 0.90**.
  *Kayenta NODATA rule:* a cycle with no canary sample is NODATA (not a pass); 2 consecutive
  NODATA = gate failure. *Cleaning rule:* HTTP 429 (rate-limit) samples are excluded with a
  note, capped at 2 per bake (RT2); the 3rd 429 counts as High.
- **G4 — Novelty review:** if the canary's selected `model` differs from stable's for ≥3
  consecutive cycles AND the model was never selected in the Phase-0 baseline → **manual
  review required** (HOLD, not auto-fail — avoids false rollback on a genuinely better pick).
- **G5 — Consumer contract:** every cycle, run the consumers read-only against the canary
  state: start `shim.py --port <throwaway> --state state.json.canary`, `GET /health`, assert
  HTTP 200 with `healthy == true`, `model` a non-empty string, and `model != "kimi-auto"`
  (the shim's self-reference guard), all within 5s, then stop the probe instance. JSON schema
  keys of the canary state must equal the baseline key set (no additive drift without a
  consumer bump). Any failure = gate failure.
- **G6 — Resource cap (spare-capacity rule):** canary sidecar runs `nice -n 19 ionice -c3`;
  per-cycle wall time ≤ 300s; external probes ≤ 2 concurrent. Breach = HOLD + investigate.

### 4.2 Analyzer contract

`analyze.py --stable state.json --canary state.json.canary --baseline <dir> --phase N`
→ prints a JSON verdict to stdout and exits:
`0` = PROMOTE/HOLD-OK (gates pass), `1` = HOLD (bake incomplete or manual review),
`2` = ROLLBACK (a rollback trigger fired). It is run by a 5-minute cron (the existing
`bridge-watchdog`/`squawk-monitor` pattern) during Phases 1–3, and **exit 2 pages the
operator and auto-invokes `rollback.sh`** (automated trigger = the fourth paper-canary
requirement). Full source is materialized by the executor at Phase-0; the spec above is
normative.

---

## 5. Rollback triggers + the EXACT rollback sequence

### 5.1 Trigger table

| # | Trigger (automated unless noted) | Applies | Action |
|---|---|---|---|
| R1 | 3 consecutive cycles `healthy:false` (canary) | P1–P3 | Auto-rollback |
| R2 | G1 freshness breach: canary state older than `2 × INTERVAL` | P1–P3 | Auto-rollback (dead loop) |
| R3 | G3 judge score < 0.90 at end of bake | P1 | Auto-rollback |
| R4 | G5 consumer dry-run failure (any cycle) | P1–P3 | Auto-rollback |
| R5 | Canary process crash-loop: 3 restarts in 10 min | P1–P3 | Auto-rollback |
| R6 | G4 novelty HOLD unresolved after 2 extra cycles | P1 | Manual: promote or rollback (operator decides; default = rollback) |
| R7 | Operator judgment / deconfliction ping from another track | Any | Manual rollback, no questions asked |

### 5.2 The one-command rollback (staged, idempotent, fail-loud)

The executor materializes this as `/home/toxic/kimi-auto/canary/rollback.sh` at Phase 0.
Execution is a single command:

```bash
bash /home/toxic/kimi-auto/canary/rollback.sh --reason "R3 judge score 0.83 < 0.90"
```

Script (normative; `set -euo pipefail` — fail loud per yote AGENTS.md):

```bash
#!/usr/bin/env bash
# canary rollback for kimi-auto-resolver — idempotent, fail-loud, phase-aware.
set -euo pipefail
REASON="${1#--reason=}"; REASON="${REASON:-manual}"
PFX=""; command -v pitchfork >/dev/null || PFX="PATH=/home/toxic/.local/share/mise/shims:$PATH"
export PATH="/home/toxic/.local/share/mise/shims:$PATH"
DAEMON="sovereign/kimi-auto-resolver"   # QUALIFIED id — bare 'kimi-auto-resolver' is ambiguous (RT1)
WORK=/home/toxic/kimi-auto
BASELINE="$(ls -dt $WORK/.canary-baseline-*/ 2>/dev/null | head -1)"
[ -n "$BASELINE" ] || { echo "FATAL: no baseline snapshot"; exit 3; }
PHASE="$(cat $WORK/canary/phase 2>/dev/null || echo 0)"

log(){ echo "[rollback $(date -Is)] $*"; }
log "reason=$REASON phase=$PHASE baseline=$BASELINE"

# 1. stop whatever the canary phase started (phase-aware, never touches other daemons)
case "$PHASE" in
  1) pkill -f "resolver.py --state .*state.json.canary" || true ;;  # shadow sidecar only
  2|3) pitchfork stop "$DAEMON" ;;
esac

# 2. restore pinned baseline files, verify integrity
sha256sum -c "$BASELINE/sha256sums" || { echo "FATAL: baseline integrity failed"; exit 3; }
cp -a "$BASELINE/loop.sh" "$BASELINE/resolver.py" "$BASELINE/shim.py" "$WORK/"

# 3. restart stable under the supervisor (qualified id), wait for one fresh cycle
pitchfork start "$DAEMON"
for i in $(seq 1 20); do
  AGE=$(python3 -c "import json,time;print(int(time.time()-__import__('datetime').datetime.fromisoformat(json.load(open('$HOME/.local/share/kimi-auto/state.json'))['updated_at']).timestamp()))" 2>/dev/null || echo 999999)
  [ "$AGE" -lt 1350 ] && break; sleep 60
done
[ "$AGE" -lt 1350 ] || { echo "FATAL: stable did not produce fresh state"; exit 3; }

# 4. record
echo 0 > "$WORK/canary/phase"
log "ROLLBACK COMPLETE reason=$REASON — stable healthy, state age ${AGE}s"
```

**Recovery-time objective (honest):** ≤ 1 audit cycle + 60s supervisor restart ≈ **16 minutes
worst case** in Phase 2/3; **0 minutes consumer impact** in Phase 1 (shadow never served).
The plan states this plainly because a canary whose rollback time is unknown is a paper canary.

### 5.3 What rollback never does

- Never `pitchfork stop` an unqualified/ambiguous daemon id (RT1).
- Never touches `squawk-*`, `awrawr-ws-exec`, `tailscaled`, or port 443 (hard limits).
- Never deletes the canary artifacts — they move to `.canary-archive-<ts>/` for post-mortem.

---

## 6. What "green" looks like — verification commands

Run as `toxic` on yote after each phase. Green = all pass.

```bash
export PATH="/home/toxic/.local/share/mise/shims:$PATH"
# 1. supervisor view (qualified id)
pitchfork status sovereign/kimi-auto-resolver
# 2. freshness + self-health of the LIVE state
python3 -c "
import json, time, datetime
s = json.load(open('/home/toxic/.local/share/kimi-auto/state.json'))
age = time.time() - datetime.datetime.fromisoformat(s['updated_at']).timestamp()
print('model:', s['model'], '| healthy:', s['healthy'], '| age_s:', int(age))
assert s['healthy'] is True and age < 1350, 'NOT GREEN'"
# 3. last analyzer verdict
cat /home/toxic/kimi-auto/canary/last-verdict.json
# 4. consumer contract, live (throwaway probe instance; the shim has no --dry-run flag —
#    its /health endpoint is the read-only contract surface)
P=25991; python3 /home/toxic/kimi-auto/shim.py --port $P --state /home/toxic/.local/share/kimi-auto/state.json & SHIM=$!
sleep 2; curl -sf --max-time 5 http://127.0.0.1:$P/health | python3 -c "import json,sys; h=json.load(sys.stdin); print(h); assert h['healthy'] and h['model'] and h['model']!='kimi-auto', 'CONTRACT FAIL'"; kill $SHIM
# 5. phase marker + no stray canary writers
cat /home/toxic/kimi-auto/canary/phase; pgrep -af "state.json.canary" || echo "no shadow writers (expected outside P1)"
```

Phase-3 close-out additionally requires: 24h without any R-trigger, `last-verdict.json`
score ≥ 0.90, and a close-out line appended to `/home/toxic/shingle/todos.md`.

---

## 7. Pre-flight checklist

- [ ] Deconfliction: no other track editing `/home/toxic/kimi-auto/` or `pitchfork.toml`
  (check todos.md + squawk fleet channel). kimi-auto herd-surface work is adjacent — confirm.
- [ ] Read current `PROBE_TIMEOUT` (60s as of 2026-09-19) and `KIMI_AUTO_INTERVAL`; record in run log.
- [ ] Verify qualified daemon id: `pitchfork status sovereign/kimi-auto-resolver` returns exactly one match.
- [ ] Disk: `df -h /home` ≥ 5 GB free (snapshots are small; this is hygiene).
- [ ] Secrets: `/home/toxic/.secrets` present (names only; values never handled — honeytoken discipline).
- [ ] Baseline snapshot: `mkdir /home/toxic/kimi-auto/.canary-baseline-$(date +%Y%m%d-%H%M%S)`,
  copy `loop.sh resolver.py shim.py`, write `sha256sums`, record git SHAs of sovereign-projects
  if the vNext source lives there.
- [ ] Materialize `/home/toxic/kimi-auto/canary/` with `analyze.py`, `rollback.sh` (from §4–5),
  `phase` file (= `0`), and the 5-min analyzer cron (disabled until Phase 1).
- [ ] Announce in todos.md (`[canary-plan]`) and squawk `fleet`: canary window open, phases, RTO.
- [ ] Confirm consumer fallback story is understood: kimi-auto alias 503s fail-loud by design;
  pinned-model traffic is unaffected (§1.2).

---

## 8. Red-team — three ways this could go wrong, and the hardening

**RT1 — Silent crash loop + ambiguous supervisor id.** `loop.sh` runs
`resolver.py || true`: a vNext resolver that crashes every cycle would loop forever while
`state.json` goes stale — and G1 would be the *only* thing that notices. Worse,
`pitchfork restart kimi-auto-resolver` is **ambiguous** (verified 2026-09-19: matches
`sovereign-phase3-rename/kimi-auto-resolver` AND `sovereign/kimi-auto-resolver`) — a naive
rollback restarts the wrong namespace or errors out.
*Hardening (in plan):* rollback.sh uses the fully-qualified `sovereign/kimi-auto-resolver`
exclusively (§5.2); the analyzer treats freshness breach as auto-rollback (R2) so
`|| true` can never hide a dead canary; Phase-2/3 additionally require a consecutive-failure
counter (executor adds `|| echo "$(( $(cat fails 2>/dev/null || echo 0) + 1 ))" > fails`
semantics to the vNext loop — spec'd, not assumed).

**RT2 — Correlated probe load poisons the comparison.** Canary + stable both probe the same
external providers (OpenRouter/NVIDIA). Doubled load can 429 both, making the judge compare
two sick patients and bless a bad canary (or condemn a good one).
*Hardening (in plan):* canary cycle offset by `INTERVAL/2` (450s) so probes never coincide;
≤2 concurrent probes; 429 samples excluded as NODATA-with-note, capped at 2 per bake, 3rd
counts as High (§4.1 G3); canary runs `nice -n 19 ionice -c3` (spare-capacity rule from
arXiv:2605.02377 — the canary must not perturb what it measures).

**RT3 — Consumer contract drift turns a resolver bug into a fleet-wide 503.** `shim.py`
fails *loudly* (503) when no Kimi candidate is healthy — there is no silent static fallback.
A canary that emits a schema the old shim can't parse, or that persistently selects a dead
model, breaks every `model=kimi-auto` consumer at Phase 2.
*Hardening (in plan):* G5 consumer dry-run gate runs every cycle in every phase against the
canary state (read-only); schema key-set must equal baseline (additive fields require a
consumer bump first); any G5 failure is auto-rollback (R4); Phase 2 keeps the stable loop
hot-writing `state.json.stable` so RTO is a file copy, not a debugging session.

**RT4 (bonus) — Diurnal provider behavior.** A 2h bake at 02:00 sees different provider
latency than 14:00. *Hardening:* minimum bake is 8 cycles but **recommended 24h shadow**;
the judge records per-cycle scores so a time-of-day effect is visible, not averaged away.

---

## 9. Research lineage

1. **Kayenta — Automated Canary Analysis at Netflix** (Netflix TechBlog; Google/Netflix OSS,
   Spinnaker). The judge pipeline this plan ports: data validation → NODATA, data cleaning,
   Mann-Whitney U metric comparison → Pass/High/Low, score = pass ratio driving
   promote/rollback. https://netflixtechblog.com/automated-canary-analysis-at-netflix-with-kayenta-3260bc7acc69
2. **Argo Rollouts / Flagger AnalysisTemplates** — `successCondition`, `failureLimit`,
   `count × interval`, `progressDeadlineSeconds`, automated abort → traffic reverts to stable.
   The gate grammar of §4 and the progress deadline of §3.
3. **"Unfair by design: eBPF-based scheduling of mixed database workloads"** —
   arXiv:2605.02377. Deliberate unfairness as isolation: background work on spare capacity
   only. Lineage for the canary's `nice/ionice` + staggered-offset scheduling (§2, G6, RT2).
4. **"eBeeMetrics: An eBPF-based Library Framework for Feedback-free Observability of QoS
   Metrics"** — arXiv:2603.25067. Tail latency/throughput are invisible to counters; QoS must
   be made observable. Lineage for gating on the resolver's own `latency_ms` distributions
   rather than a boolean (§1.2, §4).
5. **The paper-canary rule** (arc-ready progressive-delivery reference): a canary without a
   named metric + numeric threshold + bounded window + automated rollback trigger is not a
   canary. Enforced in §3–§5.

---

## 10. Non-goals, deconfliction, close-out

- **Not executed by this plan.** No phase is started by the authoring track; the executor
  (operator or a later worker) runs §7 then Phase 0.
- **Does not change** `pitchfork.toml` daemon semantics, the herd, the bridge, squawk, or any
  secret handling. vNext payload arrives via the normal sovereign-projects flow.
- **Deconfliction:** the kimi-auto herd-surface track owns `herd.d/` + `shim.py` semantics;
  this plan only *reads* the consumer contract (G5). Coordinate via todos.md before Phase 2.
- **Close-out:** after Phase-3 soak, archive `.canary-baseline-*` and `.canary-archive-*`
  (keep 30d), append the green verification output to todos.md, and nominate the next
  candidate (`paper-poller`).

*End of plan — design only, not executed.*
