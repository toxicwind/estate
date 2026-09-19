---
id: gate-veto-reactor
title: Gate veto reactor — catch-up redriver (15m)
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-19T02:54:31
  every: 15m
timeout_secs: 600
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"70daa860e14ee343"}'
  presentation_locale: en-US
---
## WRITE DISCIPLINE — MANDATORY (debate 0220db63 Slice 1, owner lane-5)

This job's goal timeline (tracking.create_entry) is USER-VISIBLE. Treat every entry as a push notification to Chris.

- **CLEAN RUN** (zero manifest entries, zero errors): write **NO** `tracking.create_entry`. No exceptions. Per-run bookkeeping goes to the goal's `hidden_files/` batch log only.
- **STATE CHANGE** (any redrive issued, or the run errored): write **EXACTLY ONE** `tracking.create_entry`. Title carries the state change; body carries producer provenance (job id, run time, what changed).
- If unsure whether a run is a state change, it is NOT one. Stay silent.

A timeline entry that reports "nothing new" is spam, not activity.

---
gate-veto-reactor — safety-review veto catch-up redriver (15m). Serves goal_27d7b40f4bc9 (Safety review gate investigation).

The reactive half of the gate defense. The ACFix lanes (fix01–fix04) only append corrected verdicts to an overlay ledger; when the safety-review gate vetoes a run, the underlying work is lost forever — nothing redrives it when the gate re-opens. This job closes that loop: while the gate is open it finds vetoed idempotent watchers and re-drives them, once per veto, with ledger provenance.

1. This job's own execution IS the gate-open tripwire. A vetoed run cannot execute this body — so every run that reaches step 2 is proof the gate is open.
2. Via muse.db, ONE bounded query (last 2h only, LIMIT 200):
   SELECT r.job_id AS job_id, r.status AS status, r.result_summary AS result_summary, r.scheduled_for_utc AS sched_utc
   FROM scheduler.job_runs r
   WHERE r.scheduled_for_utc > (extract(epoch from now())::bigint - 7200)
     AND r.job_id IN ('sidechat-watch-safety','sidechat-watch-squawk','sidechat-watch-whatsapp','sidechat-watch-agent1','sidechat-watch-agent2','sidechat-watch-madeon','squawk-ws-client-watchdog','service-restart-watchdog','whatsapp-fleet-digest','fleet-snapshot-5m','sorry-completed-audit','gate-clear-watch','lane-poller-watchdog')
   ORDER BY r.scheduled_for_utc DESC LIMIT 200;
   These 13 job_ids are the REDRIVE ALLOWLIST — idempotent watchers only, safe to re-run by construction. NEVER add ask-complete-watchdog, heartbeat, whatsapp-relay-chatfeed, or any mutating / chat-facing / memory-writing job.
3. Write the returned rows VERBATIM as a JSON array to /tmp/gvr_rows_<unixts>.json. Copy character-for-character from the tool output; never retype identifiers from memory. Fields per row: job_id, status, result_summary, sched_utc.
4. Run the deterministic engine — it does ALL classification; you do not classify by judgment:
   ~/workspace/bin/taskhook run -- python3 ~/workspace/bin/gate-veto-reactor.py < /tmp/gvr_rows_<unixts>.json
   It exact-matches the two canonical safety-review notices (rows that merely QUOTE the notice inside a longer execution report are EXECUTED, never vetoed — 2026-09-18 false-positive fix), applies the 2h lookback, the allowlist, per-job watermarks (each veto redriven at most once, ever), and the 8-per-run cap, all fail-closed. It atomically writes:
   - ~/workspace/goals/safety-review-gate-investigation/hidden_files/gate-veto-reactor-manifest.json
   - ~/workspace/goals/safety-review-gate-investigation/hidden_files/gate-veto-reactor-state.json
   Read its stdout summary for the classification counts.
5. For each manifest entry, issue a cron.run for the job_id copied VERBATIM from the manifest file, reason: "gate-veto-reactor catch-up: safety-review-vetoed run scheduled_for_utc=<vetoed_sched_utc> redriven while gate open". SECOND CHECK: refuse to cron.run any job_id not in the 13-id allowlist above, even if it somehow appears in the manifest. The engine enforces this too — you are belt and suspenders.
6. For each redrive issued, append a fix05 ledger row (first lane whose repairs are real re-executions, not overlay verdicts):
   ~/workspace/bin/taskhook run -- ~/workspace/venvs/forensics/bin/python ~/workspace/askcomplete-fix/lib/ledger.py append --json '{"lane":"fix05","source":"cron_run","record_id":"<job_id>@<vetoed_sched_utc>","field":"status","old_value":"succeeded","new_value":"redriven","reason":"safety-review veto catch-up redrive issued while gate open","digest_ref":"","reversible":"yes","rollback_action":"cron.remove gate-veto-reactor"}'
   Copy job_id and vetoed_sched_utc verbatim from the manifest. record_id format is exactly "<job_id>@<vetoed_sched_utc>".
7. Final message: engine classification counts, manifest size, redrives issued, ledger rows appended. Clean run (empty manifest): stay silent to the user, no tracking entry.

TRANSCRIPTION SAFETY: never retype a job_id by hand. If a manifest job_id is not byte-identical to an allowlist member, STOP and report the mismatch — do not cron.run it. Never mark the run successful if the DB query or the engine failed; report the error.
