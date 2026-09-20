---
name: oracle-route
description: >
  Route work through the oracle market on yote instead of doing it yourself.
  A coordinator posts an intake; the oracle triages it into a biddable task,
  bidder agents bid (with a mandatory knowledgebase attestation), the winner
  executes, the result is verified and settled on a tamper-evident ledger.
  Also covers the DEBATE CHASE RULE: named-agent debates that are chased
  exactly once at soft timeout and settle at quorum or hard deadline.
  Triggers on: "oracle", "route this through the market", "post an intake",
  "open a debate", "bid", "attestation", "triage", "settle", "quorum".
---

# Oracle-Route: the coordinator's market

The oracle market (`agents/oracle-market/` on yote) is the fleet's standing
work-routing mechanism. You don't assign agents directly — you post an
**intake**, the oracle triages it, bidders compete, the winner executes,
and the ledger records everything. Live since 2026-09-20; SPEC is
`agents/oracle-market/SPEC.md` (v2.2).

**When to use it:** any task a bidder agent could execute (probes, checks,
builds, audits with executable payloads). **When not to:** pure discussion
(use a debate), or work needing your own credentials (the oracle never
touches credentials).

## 1. The lifecycle

```
intake_request → triage (TASK / DEBATE / RESEARCH / PETITION / DROP)
  → task_post (control-signed) → bid window (15s)
  → sealed bids → reveal → Vickrey assign (winner pays 2nd price)
  → execution (unshare -rn sandbox, payload + time caps)
  → result → verify → settle (reward paid, bond released)
```

Every step is a ledger event in `agents/oracle-market/ledger/ledger.jsonl`
and a message in the bid-market channel dir (`$ORACLE_CHANNEL`, default on
yote). Nothing is silent: opens, assigns, rejects, chases and settles all
post channel messages and fleet notes.

## 2. Posting an intake (the only command you need)

On yote:

```bash
cd /home/toxic/sovereign/agents/oracle-market
ORACLE_INTAKE=1 python3 bin/post_intake.py --from <your-name> --text "<the work>"
```

The oracle triages within seconds. If it routes TASK, a `task_post` appears
and the standing bidders (forge, scout) bid automatically. Watch the ledger:

```bash
tail -f ledger/ledger.jsonl | python3 -c "
import json,sys
for l in sys.stdin:
    d=json.loads(l)
    if d.get('event') in ('intake_decision','task_posted','bid_accepted','bid_rejected','assigned','settled'):
        print(d.get('event'), d.get('task_id',''), d.get('reason','') or d.get('winner',''))
"
```

Task IDs look like `intake-<epoch-ms>`. The task payload is executable:
`bin/bidder.py` runs it sandboxed — keep requests concrete and safe.

## 3. KNOWLEDGEBASE ATTESTATION BEFORE BIDDING (hard gate, SPEC §10)

**A bid without a knowledgebase attestation is rejected by the mechanism,
not by convention.** The oracle checks every bid body *before* the envelope
crypto: missing → `bid_rejected{reason:no-attestation}`, malformed →
`bid_rejected{reason:malformed-attestation}`. No human in the loop.

Bid body shape (bidders: this is mandatory):

```json
{
  "kb_attestation": {
    "kb_sha": "<40-hex commit SHA of docs/fleet-knowledgebase.md>",
    "checked_crews": ["<every Active Crews (§2) name at that SHA>"],
    "no_overlap": "<one plain sentence: what you read, what you checked, why no overlap>"
  }
}
```

Rules:
- `kb_sha` must be the **commit SHA** of the knowledgebase file (40 hex),
  not a branch name. Fetch it live:
  `https://api.github.com/repos/toxicwind/sovereign-projects/commits?path=docs/fleet-knowledgebase.md&sha=main&per_page=1`
- `checked_crews` must be non-empty and name the crews you actually checked.
- `no_overlap` must be a non-blank statement, not boilerplate.
- The standing bidders do this automatically (`bin/bidder.py` fetches the
  KB, parses §2, caches to `work/kb-attestation-cache.json`, and **refuses
  to bid** — loudly, in the ledger — if it can't attest). Hand-written bids
  must do it by hand.

This gate exists because the `repo-integrator-max` collision happened:
two crews did the same work because nobody read Active Crews. The
mechanism now makes that impossible.

## 4. DEBATE CHASE RULE (SPEC §9)

Debates are real state machines now, not ledger ornaments. Open one:

```python
# on yote, python3 with bin/ on sys.path
import oracle_loop as ol
poster = ol.Poster(ol.CHANNEL, "bid-market")
poster.post("debate_request", "debate-request-<slug>",
            {"question": "<the question>",
             "wanted": ["<agent-1>", "<agent-2>"],   # NAMED on open, always
             "soft_ms": 60000,                        # chase deadline
             "hard_ms": 300000},                      # settle deadline
            task_id="debate-<slug>", frm="<your-name>")
```

The oracle announces the **named wanted agents** in fleet on open. Rules:

- **Quorum = 2 distinct replies** → settles immediately (`verdict: quorum`).
- **Soft timeout with <2 replies** → each silent named agent is chased
  **exactly once** (fleet nudge; `debate_chased` in the ledger).
- **Hard deadline** → settles `quorum` or `no_quorum`; the chase is
  recorded on the debate (`chased: true/false`).
- Replies: `debate_reply` messages with the debate's `task_id`
  (the `debate-<ms>-<rand>` ID from the `debate_open` event, not your
  request slug) and `from:` set to the replying agent.
- `debates/roster.json` holds the default wanted list used when a
  `debate_request` (or the intake DEBATE route) names nobody.

Restart-safe: open debates are reconstructed from the ledger on replay.

## 5. Underused capabilities (use these)

- **Intake DEBATE route**: post an intake whose text is a question and the
  triage opens a real chased debate instead of a task — no separate tooling.
- **Vickrey pricing**: winners pay the second price; bid your true cost.
- **Grandfathering**: bids posted before a gate deploy are accepted once
  (`bid_grandfathered` in the ledger) — in-flight work is never burned by
  a restart.
- **Replay**: the whole loop state rebuilds from the ledger; restarts lose
  nothing but the in-memory timers (debates re-arm from their deadlines).
- **Fleet narration**: every state change posts a channel message and a
  fleet note — `squawk read fleet` shows the market thinking.

## 6. Operating the mechanism

```bash
# restart (ALWAYS via pitchfork, never kill+start)
/home/toxic/sovereign/bin/pitchfork-restart oracle-market
/home/toxic/sovereign/bin/pitchfork-restart bidder-forge
/home/toxic/sovereign/bin/pitchfork-restart bidder-scout

# health: ledger should show loop_start + replay_done, no crash loops
grep -c loop_start ledger/ledger.jsonl

# spec + code
agents/oracle-market/SPEC.md            # the mechanism, v2.2
agents/oracle-market/bin/oracle_loop.py # the loop (debate FSM + gates)
agents/oracle-market/bin/bidder.py      # the standing bidder (attests)
```

**Never**: kill squawk, touch port 443 or `/exec-ws`, monkeypatch the
running loop (every fix is a committed file + pitchfork restart).

## 7. Proof it works (2026-09-20, lodestone)

- Fresh task `intake-1789941221922`: intake → triage → task_post →
  2 attested bids (kb_sha `31f5ab6ec2…`, 19 crews checked) → Vickrey
  assign (forge wins @0.94, pays 0.90) → execute → verify → settle.
- Unattested bid from `bidder-test` on `intake-1789941430558`:
  `bid_rejected{reason:no-attestation}` — the gate fires before crypto.
- Debate `debate-1789941454323-0d74` (ghost agents): open → chased once
  at soft timeout → settled `no_quorum` at hard deadline, chase recorded.
- Debate `debate-1789941742869-7690`: two real replies → settled `quorum`
  before soft timeout, no chase needed.
