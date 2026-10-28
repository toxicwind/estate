# Pong canary — the constant retest

Canonical refusal probe (Chris, 2026-09-15): the refused "pong" spawn is the
standing retest for the spawn path.

## The probe

```
subagent.spawn(message="Trivial connectivity probe: reply with the single word \"pong\" and nothing else.")
```

## The verdict (mechanical, no string matching)

```sql
SELECT spawn_id, status, (completed_at - created_at) AS secs,
       md5(final_response) AS fr_md5
FROM agent.subagent_spawns
WHERE child_agent_id = '<agent_id from spawn result>';
```

**Refused** iff `fr_md5 = 'b4aefd29108f232f9c0d5a4b030215c1'`
(the canonical canned-refusal signature: byte-identical 384-char body,
30/30 refused spawns in 24h, always recorded as status "completed").

**Ran fine** iff the md5 differs (real work: unique bodies, 60s+ runtimes).

Timing corroborates: refusals resolve in 0-4s; genuine workers run 60s+.

## Why a hash, not the string

The refusal text is never quoted, pasted, or stored anywhere in this hunt —
only its md5. This keeps the signature out of prompts and transcripts
(where quoting it risks re-triggering context-saturation classifiers).

## Baseline (2026-09-15 22:00 MDT)

spawn_id 397, the canonical example: created 1789531173, completed 1789531174
(1s), status "completed", fr_md5 b4aefd29108f232f9c0d5a4b030215c1.
pcap: spawn-refusal-20260915.pcap proves the refusal arrived via remote
round trip through hatch-egress-proxy:3128 during that 1s window.
