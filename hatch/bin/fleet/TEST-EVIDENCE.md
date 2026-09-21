# TEST EVIDENCE — ordered fleet delivery

Run on **yote** (the box that hosts the squawk-root), 2026-09-20 ~21:55 MDT,
against the deployed engine `/home/toxic/squawk-fleet/fleet.py`
(sha256-verified byte-exact from the repo copy). Python 3.14.7.

```
$ cd /home/toxic/squawk-fleet && python3 test_fleet.py
--- test_concurrent_publish_no_dup_no_loss
PASS concurrent: 800 unique seqs
PASS concurrent: exactly 1..800, no gaps/loss
PASS concurrent: gaps() empty
--- test_dedup_collapses_retries
PASS dedup: single seq across 16 racing retries
PASS dedup: 15 collapsed as deduped
PASS dedup: exactly one message file
PASS dedup: sequential re-send collapses
--- test_gap_detect_and_replay
PASS gap setup removed 2 files
PASS gaps: detects exactly [5, 8]
PASS replay: fetch --after 4 returns survivors in order
PASS replay: bodies intact
PASS replay: missing set disjoint from replayed
--- test_acks_per_consumer
PASS acks: tracked per consumer
PASS lag: max 12, watcher lag 2, archiver lag 5
PASS ack-get single consumer
--- test_chat_isolation
PASS chat-new: scopes
PASS isolation: chat A seqs 1..80
PASS isolation: chat B seqs 1..80
PASS isolation: main seqs 1..80
PASS isolation: A sees only A bodies
PASS isolation: B sees only B bodies
PASS isolation: main sees no chat traffic
PASS isolation: no gaps anywhere
--- test_msg_id_cannot_escape
PASS sanitize: evil msg_id publishes inside scope
PASS sanitize: id file has no path separators
PASS sanitize: nothing escaped to /etc
PASS sanitize: nothing escaped to root parent
--- test_new_scope_inside_lock
PASS new scope: first publish gets seq 1
PASS new scope: file exists
--- test_cli_roundtrip
PASS cli: publish returns seq 1
PASS cli: republish same id dedupes
PASS cli: fetch sees it
PASS cli: no gaps
PASS cli: ack
PASS cli: lag 0
PASS cli: chat-new

36 passed, 0 failed
```

The same suite passes identically on the hatch cell (portable stdlib-only
code): 36 passed, 0 failed.

## End-to-end via the cell CLI (live squawk-root, scratch channel)

`~/workspace/bin/squawk-fleet` -> yote-conn bridge -> fleet.py, channel
`fleet-e2e-1758495150` in the real squawk-root (removed afterwards):

- `send --id e2e-1` -> `{"seq": 1, "deduped": false, ...}` (0.4 ms engine)
- re-`send --id e2e-1` -> `{"seq": 1, "deduped": true, ...}` — retry collapsed
- `send --id e2e-2` -> seq 2
- `chat-new --name "E2E Relay"` -> scope `fleet-e2e-1758495150/chats/e2e-relay`
- `send --chat "E2E Relay"` -> chat-local seq 1 (independent seq space)
- `gaps` -> `max_seq=2 missing=none`
- `fetch --after 0 --full` on main -> msgs 1,2 with bodies intact
- `fetch --chat "E2E Relay"` -> only the relay message, main untouched
- `ack --consumer e2e-watcher --seq 2` -> acked=2; `lag` -> lag=0

Note: `/home/toxic/.shingle` resolves (realpath) to
`/home/toxic/sovereign/hatch/agents/ember/squawk-root` on yote — the engine
canonicalizes via realpath, so symlinked and real paths agree. Scratch
channel removed after the run (`ls | grep -c e2e` -> 0).
