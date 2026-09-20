-- ============================================================================
-- stall-detect/queries.sql — DB-forensics stall-detection query pack
--
-- Permanent companion to the stall-slayer runbook (README.md in this dir).
-- Execution path: any agent with the muse_db skill runs these via `muse.db`
-- (bounded, read-only SELECT; the DB is tool-gated, so there is no shell CLI).
-- All queries use only the functions/casts the muse.db surface allows and
-- return ≤50 rows each. Read references/schema.md before modifying.
--
-- Lane rule: this pack is DB forensics ONLY (executions, tool calls,
-- transcripts, mailbox, recovery). Live process behavior (ps, CPU, py-spy,
-- strace, ports) belongs to the live-proc lane (stale-hunter) — do not
-- duplicate their hunt; share DB findings in fleet and divide targets there.
-- ============================================================================

-- Q1: stale running agents — idle > 12h (tune threshold per fleet needs)
SELECT agent_id AS stale_aid, kind AS k, agent_type AS atype,
       round((EXTRACT(epoch FROM now()) - updated_at)/3600, 1) AS idle_hrs,
       substr(last_assistant_message, 1, 300) AS last_msg
FROM agent.agents
WHERE status = 'running'
  AND (EXTRACT(epoch FROM now()) - updated_at) > 12*3600
ORDER BY updated_at ASC
LIMIT 50;

-- Q2: in-flight tool calls with NO output — genuinely stuck mid-call work
SELECT c.tool_name AS tname, c.status AS s, c.call_id AS tcall,
       round((EXTRACT(epoch FROM now()) - EXTRACT(epoch FROM c.created_at))/3600, 1) AS age_hrs
FROM runtime.tool_calls c
LEFT JOIN runtime.tool_outputs o ON o.call_id = c.call_id
WHERE o.call_id IS NULL
ORDER BY c.created_at ASC
LIMIT 50;

-- Q3: mailbox backlog — submissions accepted/attached but never
-- terminalized, older than 1h (fresh ones <1h are normal traffic)
SELECT submission_id AS sid, agent_id AS aid, state AS s,
       submission_kind AS kind,
       round((EXTRACT(epoch FROM now()) - EXTRACT(epoch FROM accepted_at))/3600, 1) AS age_hrs
FROM agent.message_mailbox
WHERE state IN ('accepted', 'attached')
  AND (EXTRACT(epoch FROM now()) - EXTRACT(epoch FROM accepted_at)) > 3600
ORDER BY accepted_at ASC
LIMIT 50;

-- Q4: unterminalized recovery owners — recovery sessions that never closed
SELECT recovery_class AS rc, agent_id AS aid, message_id AS mid,
       round((EXTRACT(epoch FROM now()) - EXTRACT(epoch FROM active_at))/3600, 1) AS age_hrs
FROM agent.recovery_owners
WHERE terminal_at IS NULL
ORDER BY active_at ASC
LIMIT 50;

-- Q5: errored agents + their final message (root-cause seed)
SELECT agent_id AS aid, kind AS k,
       round((EXTRACT(epoch FROM now()) - updated_at)/3600, 1) AS idle_hrs,
       substr(last_assistant_message, 1, 300) AS last_msg
FROM agent.agents
WHERE status = 'errored'
ORDER BY updated_at DESC
LIMIT 20;

-- Q6: transcript tail for ONE stale agent (substitute <AGENT_ID>)
SELECT seq AS s, item_kind AS kind, role AS r, tool_name AS tname,
       substr(text_content, 1, 300) AS txt
FROM agent.context_items
WHERE agent_id = '<AGENT_ID>'
ORDER BY seq DESC
LIMIT 20;

-- Q7: ownership trace for ONE stale agent (who spawned it? still has owner?)
SELECT spawn_id AS sid, parent_agent_id AS parent,
       requester_source AS src, status AS s,
       substr(prompt, 1, 300) AS prompt_head
FROM agent.subagent_spawns
WHERE child_agent_id = '<AGENT_ID>'
LIMIT 5;
