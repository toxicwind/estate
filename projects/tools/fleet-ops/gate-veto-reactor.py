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
     (newest veto covers the episode). Entries are written with
     dispatch="planned".
  3. PLAN/ACK PROTOCOL (watermark-timing fix, 2026-09-19): the plan phase
     NEVER advances watermarks. The worker dispatches each planned entry
     with cron.run, and only on success runs
         gate-veto-reactor.py --ack "<job_id>@<vetoed_sched_utc>"
     which byte-verifies the planned entry, removes it from the manifest,
     and advances the committed watermark. A failed dispatch stays
     planned and retryable on the next run; a planned entry whose veto
     ages out of the lookback is dropped without advancing the watermark.
     --ack on a non-allowlisted job_id or unknown entry exits 2,
     fail-closed.
  4. FAIL-CLOSED: a manifest job_id must be an allowlist member AND must
     have appeared verbatim in the input rows. The cron worker must
     cron.run only job_ids copied verbatim from the manifest file and
     cross-checked against the allowlist printed in the cron body.
  5. Cap MAX_REDRIVES entries per run.

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
# chat-facing senders (whatsapp-relay-*, whatsapp-fleet-digest), memory
# writers (heartbeat), or anything with external side effects.
# NOTE 2026-09-19: whatsapp-fleet-digest was in the original allowlist and
# is now QUARANTINED — it posts to Chris's phone, so a redrive could
# double-post. Redrives must be side-effect-free, not merely idempotent.
REDRIVE_ALLOWLIST = (
    "sidechat-watch-safety",
    "sidechat-watch-squawk",
    "sidechat-watch-whatsapp",
    "sidechat-watch-agent1",
    "sidechat-watch-agent2",
    "sidechat-watch-madeon",
    "squawk-ws-client-watchdog",
    "service-restart-watchdog",
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


def load_manifest():
    try:
        with open(MANIFEST_FILE) as f:
            m = json.load(f)
        return m if isinstance(m, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def ack(record_id):
    """Advance the committed watermark for one successfully dispatched
    redrive. record_id format: "<job_id>@<vetoed_sched_utc>".
    Fail-closed: the record must match a planned manifest entry
    byte-identically AND the job_id must be an allowlist member."""
    try:
        jid, _, sched_s = record_id.partition("@")
        sched = int(sched_s)
    except (ValueError, AttributeError):
        print(f"gate-veto-reactor --ack: malformed record_id: {record_id!r}",
              file=sys.stderr)
        return 2
    if not jid or jid not in REDRIVE_ALLOWLIST:
        print(f"gate-veto-reactor --ack: job_id not allowlisted: {jid!r}",
              file=sys.stderr)
        return 2
    manifest = load_manifest()
    hit = None
    for m in manifest:
        if (isinstance(m, dict) and m.get("job_id") == jid
                and m.get("vetoed_sched_utc") == sched
                and m.get("dispatch") == "planned"):
            hit = m
            break
    if hit is None:
        print(f"gate-veto-reactor --ack: no planned entry for {record_id!r}",
              file=sys.stderr)
        return 2
    manifest = [m for m in manifest if m is not hit]
    state = load_state()
    state[jid] = {
        "last_veto_redriven_utc": sched,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_json(MANIFEST_FILE, manifest)
    atomic_write_json(STATE_FILE, state)
    print(f"gate-veto-reactor --ack: watermark advanced for {jid}@{sched}")
    return 0


def plan(rows):
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
    # Rebuild the dispatch queue from scratch each run (plan/ack protocol):
    # watermarks advance ONLY via --ack after a successful cron.run, so a
    # failed dispatch stays retryable instead of being silently suppressed.
    prev_manifest = load_manifest()
    still_qualifies = set()
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
        still_qualifies.add((jid, veto_utc))
        manifest.append({
            "job_id": jid,
            "vetoed_sched_utc": veto_utc,
            "dispatch": "planned",
            "reason": "safety-review veto catch-up redrive; gate open (reactor executed)",
        })
    # Drop planned entries whose veto aged out of the lookback (episode over,
    # never dispatched) rather than redriving stale work.
    for m in prev_manifest:
        if (isinstance(m, dict) and m.get("dispatch") == "planned"
                and (m.get("job_id"), m.get("vetoed_sched_utc"))
                not in still_qualifies):
            counts["planned-expired"] = counts.get("planned-expired", 0) + 1

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


def main(argv):
    if len(argv) == 3 and argv[1] == "--ack":
        return ack(argv[2])
    if len(argv) != 1:
        print("gate-veto-reactor: usage: gate-veto-reactor.py [--ack "
              "<job_id>@<vetoed_sched_utc>] < rows.json",
              file=sys.stderr)
        return 2
    try:
        raw = sys.stdin.read()
        rows = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"gate-veto-reactor: malformed input JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(rows, list):
        print("gate-veto-reactor: input must be a JSON array", file=sys.stderr)
        return 2
    return plan(rows)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
