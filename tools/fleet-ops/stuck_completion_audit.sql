-- Stuck-completion subagent audit (the "looks running, actually done" bug).
-- Pattern: agent.subagent_spawns.status = 'running' BUT terminal evidence
-- already exists. Two tiers:
--
--   TIER 1 (airtight): the agent row itself is already terminal
--     (agents.status IN ('completed','shutdown','errored','interrupted'))
--     while the spawn row still says 'running'. No live process exists;
--     the bookkeeping flip just never happened. Safe for the owning lane
--     to close/reap.
--
--   TIER 2 (needs owner-lane eyes): agent row still 'running' but the spawn
--     carries terminal evidence (completed_at / final_response /
--     deferred_terminal_status) AND running_kids = 0 AND stale. Often a
--     coordinator that already delivered its report (check fr_head).
--
--   COORDINATOR_LIVE: running_kids > 0, or fr_head reads as progress
--     ("initializing", "waiting on", "interim"). DO NOT TOUCH.
--     NOTE: deferred_terminal_status='completed' is NOT reliable on its
--     own -- observed set spuriously on live coordinators (2026-09-19:
--     sids 1150/1166/1171 all had dts='completed' while actively working).
--
-- Never close another lane's agent yourself: flag TIER 1/2 finds on the
-- fleet channel (visible interrupt), the owning lane reaps.
-- Timestamps are epoch BIGINT (UTC); MDT = UTC-6.
WITH hatch_cte_kids AS (
  SELECT parent_agent_id AS pid, count(*) AS running_kids
  FROM agent.subagent_spawns WHERE status = 'running' GROUP BY parent_agent_id
)
SELECT s.spawn_id AS sid,
       s.child_agent_id AS child,
       s.parent_agent_id AS parent,
       a.status AS agent_status,
       a.updated_at AS agent_updated,
       s.deferred_terminal_status AS dts,
       s.completed_at AS done_at,
       s.created_at AS created,
       length(s.final_response) AS fr_len,
       substr(s.final_response, 1, 200) AS fr_head,
       coalesce(k.running_kids, 0) AS running_kids,
       CASE WHEN a.status IN ('completed','shutdown','errored','interrupted')
            THEN 'TIER1_ZOMBIE'
            WHEN coalesce(k.running_kids, 0) > 0 THEN 'COORDINATOR_LIVE'
            WHEN s.completed_at IS NOT NULL OR s.final_response IS NOT NULL
              OR s.deferred_terminal_status IS NOT NULL THEN 'TIER2_SUSPECT'
            ELSE 'RUNNING_CLEAN' END AS verdict
FROM agent.subagent_spawns s
LEFT JOIN agent.agents a ON a.agent_id = s.child_agent_id
LEFT JOIN hatch_cte_kids k ON k.pid = s.child_agent_id
WHERE s.status = 'running'
ORDER BY s.created_at DESC
LIMIT 200;
