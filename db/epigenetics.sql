-- /home/toxic/pens/estate/db/epigenetics.sql
-- Sub-Agent 6: Negative Space Ledger
--
-- Tracks what FAILED to manifest rather than what happened. The primary query
-- is absence: an epoch where an expected signal never arrived.
--
-- Every row is a durable, reconstructable record — nothing is silently dropped.
-- Load shedding in the sampler (tools/async-sampler.ts) writes a `shed` record
-- here so the fleet always knows what was condensed and why.

CREATE TABLE IF NOT EXISTS expected_signals (
    signal_id             TEXT PRIMARY KEY,          -- stable event/dedupe key
    source_node           TEXT NOT NULL,             -- daemon / pen / product
    expected_interval_seconds INTEGER NOT NULL,      -- heartbeat cadence
    last_seen_timestamp   INTEGER NOT NULL,          -- epoch seconds
    created_at            INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS abscission_events (
    event_id              TEXT PRIMARY KEY,          -- uuid / nanoid
    signal_id             TEXT NOT NULL REFERENCES expected_signals(signal_id),
    timestamp             INTEGER NOT NULL,          -- epoch seconds
    reason                TEXT NOT NULL              -- timeout | shed | entropy_overflow | agent_apoptosis
);

CREATE TABLE IF NOT EXISTS shed_records (
    event_id              TEXT PRIMARY KEY,
    source_node           TEXT NOT NULL,
    at                    INTEGER NOT NULL,
    bucket                TEXT NOT NULL,             -- what was condensed (schema-stable)
    count                 INTEGER NOT NULL,          -- identical rows merged
    rule                  TEXT NOT NULL              -- why (dedupe | rate-cap | entropy)
);

-- The primary absence query: expected signals that have gone silent.
SELECT signal_id FROM expected_signals
WHERE (strftime('%s','now') - last_seen_timestamp) > expected_interval_seconds;