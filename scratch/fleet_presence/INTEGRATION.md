# INTEGRATION.md — fleet_presence into chat.py

Module landed (new file, nothing modified):
`/home/toxic/.shingle/chat/fleet_presence.py` (stdlib only, tests pass on
awrawr-pc). Exposes: `heartbeat`, `heartbeat_age`, `get_view`,
`update_view`, `gossip_round`, `suspect`, `suspect_marks`, `is_alive`,
`alive_agents`, `peer_sample`, constants `VIEW_K=8`, `T_SUSPECT=60`,
`T_DEAD=300`.

## The one rule to bake in

**Trust vs liveness split.** `fleet_roster.py` is the TRUST registry (who
may speak, revocation). `fleet_presence` is LIVENESS/GOSSIP-TARGETING ONLY
(who seems alive, who to gossip with). The docstring says it, and the
command layer must say it too: `presence` output must never be used for
authorization. Suggest framing the command help as "liveness hints, not
credentials".

## Proposed commands

### 1. `chat.py heartbeat` (or a hidden `--heartbeat` flag on every send)

Called at the top of every agent turn: `fleet_presence.heartbeat(ROOT,
agent)`. One atomic small-file write; incarnation bumps let peers see
restarts. Without this being per-turn, everything downstream degrades to
noise (staleness is only observed when someone writes/reads).

### 2. `chat.py presence [agent]`

Read-only; prints the SWIM state for one agent or the whole fleet:
`fleet_presence.alive_agents(ROOT)` → `{agent: alive|suspect|dead}`.
Attach `incarnation` and `heartbeat_age()` so operators can see "restarted
twice, last seen 12s ago". Suggested footer: "suspect/dead = no heartbeat
within 60s/300s; idle and crashed are indistinguishable".

### 3. `chat.py gossip` (or fold into `presence --gossip`)

One Jelasity round for the calling agent: `gossip_round(ROOT, agent)` →
prints `(peer, new_view)`. This is the primitive the fleet uses to spread
state rumors and discover new peers without a central directory.

### 4. `chat.py suspect <peer> --reason ...`

Records a SWIM suspicion mark: `suspect(ROOT, by=me, peer, reason)`.
Only writes when the peer's heartbeat is actually stale (>60s); refuses
otherwise. Marks are gossip hints with attribution, not verdicts — a
fresh heartbeat from the peer always refutes them (SWIM indirect probing,
file version). Note: marks can't force a peer's state; `is_alive` is
decided by heartbeat age alone, which keeps one bad actor from driving
another's state via marks.

## Suggested wiring points in chat.py (coordinator's call)

- **Every send path**: `heartbeat()` at entry. This is the liveness
  contract; everything else reads from it.
- **`--roster` / who-listings**: when rendering agent lists, optionally
  annotate with `is_alive()` state (liveness column, explicitly labeled
  as such — never mixed into trust/revocation display).
- **Target selection for fleet broadcasts**: use `peer_sample(ROOT, me,
  count=N)` instead of a raw view — it filters to currently-alive agents.
- **Do NOT gate message acceptance on `is_alive()`**: an agent whose
  heartbeat is stale is still roster-authorized until revoked. Liveness
  ≠ permission.

## Polling implication (honest)

No daemon exists: a crash is only *visible* after `T_SUSPECT` seconds of
silence, and only to a peer that happens to call `is_alive` /
`alive_agents`. If the fleet wants faster failure awareness, the knob is
heartbeat frequency (e.g. heartbeat on every poll cycle too), not a
watchdog — per the assignment, "everything evaluated on the read path by
peers". `peer_sample()` is the intended default for picking gossip
targets so rounds naturally stop wasting effort on dead agents.
