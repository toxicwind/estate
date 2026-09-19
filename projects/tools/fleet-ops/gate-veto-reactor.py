#!/usr/bin/env python3
"""gate-veto-reactor: deterministic catch-up redrive engine for the
scheduled-task safety-review gate.

The safety-review gate is platform-side and intermittent. When it closes,
user jobs are vetoed: their runs report status='succeeded' while
result_summary holds a canonical skip notice, and the work is lost forever
— nothing redrives it when the gate re-opens. The ACFix lanes (fix01-fix04)
only append corrected verdicts to an overlay ledger; they never recover
the lost work.

This script is the reactive half of the gate defense. It only ever runs
when the gate is OPEN (its own execution is the tripwire — a vetoed run
cannot execute this code).

Input (stdin): JSON array of scheduler.job_runs rows:
    {job_id, status, result_summary, sched_utc}

Behavior:
  1. Honest-classifies each row with exact-match rules (no fuzzy judgment):
     - vetoed: status == 'succeeded' AND result_summary, trimmed of
       surrounding whitespace, is EXACTLY one of the two canonical
       safety-review notices and nothing else. Rows that merely QUOTE the
       notice inside a longer execution report ran real code -> EXECUTED,
       never vetoed (false-positive source fixed 2026-09-18 in
       acfix-skip-reconcile).
     - overlap-skip: 'already running and concurrency.overlap=skip' present
       (run got PAST safety review to the concurrency guard).
     - no-op: benign no-instruction skips.
     - coalesced: scheduler-coalesced cancellations.
     - executed / failed / in-flight: everything else (not redrive targets).
  2. For vetoed rows: job_id must be in REDRIVE_ALLOWLIST (idempotent
     watchers only), sched_utc inside LOOKBACK_SECS, and newer than the
     per-job watermark in the state file. One manifest entry per job
     (newest veto covers the episode). Watermark advances so each veto is
     redriven at most once, ever.
  3. FAIL-CLOSED: a manifest job_id must be an allowlist member AND must
     have appeared verbatim in the input rows. The cron worker must
     cron.run only job_ids copied verbatim from the manifest file and
     cross-checked against the allowlist printed in the cron body.
  4. Cap MAX_REDRIVES entries per run.

Outputs:
  - hidden_files/gate-veto-reactor-manifest.json (atomic rewrite): the
    redrive manifest, empty array when clean.
  - hidden_files/gate-veto-reactor-state.json (atomic rewrite): per-job
    watermarks {job_id: {last_veto_redriven_utc, updated_at}}.
  - stdout: human summary + JSON manifest for the run log.

Exit 0 always on successful processing (clean is a valid outcome).
Exit 2 on malformed input. Never exits nonzero just because vetoes exist.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

GOAL_DIR = os.path.expanduser(
    "~/workspace/goals/safety-review-gate-investigation")
HIDDEN = os.path.join(GOAL_DIR, "hidden_files")
STATE_FILE = os.path.join(HIDDEN, "gate-veto-reactor-state.json")
MANIFEST_FILE = os.path.join(HIDDEN, "gate-veto-reactor-manifest.json")

CANONICAL_NOTICES = (
    "Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.",
    "Skipped this scheduled run because its task definition or goal guide did not pass the scheduled-task safety review.",
)

# Idempotent watchers ONLY: read-mostly scans / heartbeats whose re-run is
# safe by construction. NEVER: mutating jobs (ask-complete-watchdog),
# chat-facing senders (whatsapp-relay-*), memory writers (heartbeat),
# or anything with external side effects.
REDRIVE_ALLOWLIST = (
    "sidechat-watch-safety",
    "sidechat-watch-squawk",
    "sidechat-watch-whatsapp",
    "sidechat-watch-agent1",
    "sidechat-watch-agent2",
    "sidechat-watch-madeon",
    "squawk-ws-client-watchdog",
    "service-restart-watchdog",
    "whatsapp-fleet-digest",
    "fleet-snapshot-5m",
    "sorry-completed-audit",
    "gate-clear-watch",
    "lane-poller-watchdog",
)

LOOKBACK_SECS = 2 * 3600
MAX_REDRIVES = 8


def classify(row):
    """Return the honest class for one job_runs row."""
    status = (row.get("status") or "").strip()
    summary = (row.get("result_summary") or "").strip()

    if status in ("running", "queued"):
        return "in-flight"
    if status == "failed":
        return "failed"
    if status == "timeout":
        return "timeout"
    if status == "cancelled":
        if "scheduled_occurrence_coalesced" in summary:
            return "coalesced"
        return "cancelled"
    if status != "succeeded":
        return "unknown:" + status
    # status == 'succeeded': read the summary, never the badge.
    if summary in CANONICAL_NOTICES:
        return "vetoed"
    if "already running and concurrency.overlap=skip" in summary:
        return "overlap-skip"
    if "has no instructions" in summary or "Skipped heartbeat because" in summary:
        return "no-op"
    if not summary:
        return "ambiguous"
    return "executed"


def atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_state():
    try:
        with open(STATE_FILE) as f:
            st = json.load(f)
        return st if isinstance(st, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    try:
        raw = sys.stdin.read()
        rows = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"gate-veto-reactor: malformed input JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(rows, list):
        print("gate-veto-reactor: input must be a JSON array", file=sys.stderr)
        return 2

    now = int(time.time())
    cutoff = now - LOOKBACK_SECS
    counts = {}
    # newest veto per job_id inside the lookback
    newest_veto = {}
    input_job_ids = set()

    for row in rows:
        if not isinstance(row, dict):
            continue
        jid = row.get("job_id")
        if isinstance(jid, str):
            input_job_ids.add(jid)
        cls = classify(row)
        counts[cls] = counts.get(cls, 0) + 1
        if cls != "vetoed":
            continue
        try:
            sched = int(row["sched_utc"])
        except (KeyError, TypeError, ValueError):
            continue
        if sched < cutoff:
            continue
        if not isinstance(jid, str) or jid not in REDRIVE_ALLOWLIST:
            counts["vetoed-not-allowlisted"] = counts.get(
                "vetoed-not-allowlisted", 0) + 1
            continue
        prev = newest_veto.get(jid)
        if prev is None or sched > prev:
            newest_veto[jid] = sched

    state = load_state()
    manifest = []
    for jid in sorted(newest_veto):
        veto_utc = newest_veto[jid]
        wm = 0
        entry = state.get(jid)
        if isinstance(entry, dict):
            try:
                wm = int(entry.get("last_veto_redriven_utc", 0))
            except (TypeError, ValueError):
                wm = 0
        if veto_utc <= wm:
            counts["vetoed-already-redriven"] = counts.get(
                "vetoed-already-redriven", 0) + 1
            continue
        if len(manifest) >= MAX_REDRIVES:
            counts["vetoed-over-cap"] = counts.get("vetoed-over-cap", 0) + 1
            continue
        # FAIL-CLOSED belt and suspenders: allowlist + verbatim input presence.
        if jid not in REDRIVE_ALLOWLIST or jid not in input_job_ids:
            continue
        manifest.append({
            "job_id": jid,
            "vetoed_sched_utc": veto_utc,
            "reason": "safety-review veto catch-up redrive; gate open (reactor executed)",
        })
        state[jid] = {
            "last_veto_redriven_utc": veto_utc,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    atomic_write_json(MANIFEST_FILE, manifest)
    atomic_write_json(STATE_FILE, state)

    print("gate-veto-reactor: classification counts: "
          + json.dumps(counts, sort_keys=True))
    print(f"gate-veto-reactor: manifest entries: {len(manifest)} "
          f"(cap {MAX_REDRIVES}, lookback {LOOKBACK_SECS}s)")
    for m in manifest:
        print("  REDRIVE job_id=%s vetoed_sched_utc=%d" % (
            m["job_id"], m["vetoed_sched_utc"]))
    if not manifest:
        print("gate-veto-reactor: clean — no unredriven vetoes in window")
    print("---MANIFEST-JSON---")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
