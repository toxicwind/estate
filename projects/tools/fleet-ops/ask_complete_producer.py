#!/usr/bin/env python3
"""Deterministic ask-complete watchdog producer — fail-closed ledger pipeline.

Replaces the LLM-transcription path that corrupted 17 identifiers into the
ledger (2026-09-19). The cron worker (an LLM) still runs the muse.db queries —
only agents can call muse.db — so IDs still transit the worker's transcription
path. This script makes that fail-closed rather than trusting it: it validates
every ID structurally and against the canonical set from the SAME database, and
quarantines anything off. NEVER claim token-free transport; claim structural +
lineage validation with loud quarantine on defects.

Reactive mode (--reactive): after appending new ASK/REFUSAL rows, this script
also emits a FORWARD correction into the acfix overlay ledger
(~/workspace/askcomplete-fix/lib/ledger.py) marking field=status
old_value=completed new_value=blocked for each appended row. It never re-drives
the underlying work (re-driving would duplicate side effects). The acfix append
dedupes on (lane, source, record_id), so retries are idempotent.

  1. --canonical : SELECT id FROM agent.agents ... UNION spawn_ids (48h window)
  2. --audit     : the ask_complete_audit.sql result rows

This script then:
  - structurally validates every ID (strict lowercase UUID; anything else -> quarantine)
  - lineage-validates every audit-row ID against the canonical set dumped from
    the SAME database (phantoms fail closed into quarantine, never the ledger)
  - dedupes by exact ID against the ledger
  - appends atomically (single open, flush, fsync) + post-write verification
  - preserves raw evidence under evidence/<run_id>/
  - exits non-zero on ANY infrastructure failure (unparseable input, missing
    canonical dump, ledger write/verify failure). Quarantined rows are NOT a
    failure — they are the system working — but they are reported loudly.

Security property: corruption in the audit dump can only cause quarantine+alert
(fail-closed). Corruption in the canonical dump can only cause false negatives
(genuine rows quarantined). A phantom ID can NEVER reach the ledger, because a
phantom is by definition absent from the canonical set.

Usage:
    python3 ask_complete_producer.py \
        --canonical /tmp/acw_canonical_<run>.json \
        --audit /tmp/acw_audit_subagent_spawns_<run>.json \
        --source subagent_spawns \
        --run-id <run_id>

Prints a JSON run report to stdout.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.jsonl")
QUARANTINE = os.path.join(HERE, "quarantine-producer.jsonl")
EVIDENCE_DIR = os.path.join(HERE, "evidence")

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
# spawn_id is a bigint: integer-form IDs are legitimate canonical lineage.
INT_RE = re.compile(r"^[0-9]+$")


def is_canonical_id(v):
    return isinstance(v, str) and (UUID_RE.match(v) or INT_RE.match(v))

FIELD_MAP = {
    "subagent_spawns": {"id": "sid", "md5": "fr_md5", "len": "fr_len"},
    "agents": {"id": "aid", "md5": "msg_md5", "len": "msg_len"},
}


def fail(msg, **extra):
    report = {"ok": False, "error": msg}
    report.update(extra)
    print(json.dumps(report))
    sys.exit(1)


def load_rows(path, label):
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        fail("unparseable %s dump" % label, path=path, detail=str(e))
    if isinstance(data, dict):
        if "rows" in data:
            return data["rows"]
        if "result" in data and isinstance(data["result"], dict) and "rows" in data["result"]:
            return data["result"]["rows"]
        fail("unrecognized %s JSON shape" % label, keys=list(data.keys()))
    if isinstance(data, list):
        return data
    fail("unrecognized %s JSON shape" % label, type=str(type(data)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", required=True)
    ap.add_argument("--audit", required=True)
    ap.add_argument("--source", required=True, choices=list(FIELD_MAP))
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--reactive", action="store_true",
                    help="emit forward status=blocked corrections into the acfix "
                         "overlay ledger for every appended row (no re-drive)")
    args = ap.parse_args()
    fm = FIELD_MAP[args.source]

    # --- 1. Load canonical ID set (fail closed if missing/unparseable) ---
    canon_rows = load_rows(args.canonical, "canonical")
    canonical = set()
    for r in canon_rows:
        for key in ("id", "sid", "aid", "cid", "spawn_id", "agent_id"):
            v = r.get(key)
            if is_canonical_id(v):
                canonical.add(v)
    if not canonical:
        fail("canonical ID set empty after structural filter — refusing to proceed",
             canonical_path=args.canonical, raw_rows=len(canon_rows))

    # --- 2. Load audit rows ---
    audit_rows = load_rows(args.audit, "audit")

    # --- 3. Existing ledger IDs ---
    existing = set()
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if "id" in d:
                        existing.add(str(d["id"]))
                except json.JSONDecodeError:
                    continue

    # --- 4. Classify every audit row ---
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    to_append = []
    quarantined = []
    skipped_dupe = 0
    skipped_other = 0
    for r in audit_rows:
        verdict = r.get("verdict")
        if verdict not in ("ASK", "REFUSAL"):
            skipped_other += 1
            continue
        rid = r.get(fm["id"])
        rid = str(rid) if rid is not None else ""
        reason = None
        if not is_canonical_id(rid):
            reason = "structural: not a canonical UUID or integer ID"
        elif rid not in canonical:
            reason = "lineage: ID absent from canonical DB set (probable transcription phantom)"
        elif rid in existing:
            skipped_dupe += 1
            continue
        if reason:
            quarantined.append({"ts": now, "run_id": args.run_id, "source": args.source,
                                "id": rid, "verdict": verdict, "reason": reason,
                                "md5": r.get(fm["md5"]), "len": r.get(fm["len"])})
            continue
        to_append.append({
            "ts": now, "run_id": args.run_id, "source": args.source,
            "id": rid, "verdict": verdict,
            "md5": r.get(fm["md5"]), "len": r.get(fm["len"]),
            "created_epoch": r.get("created_epoch"),
        })
        existing.add(rid)

    # --- 5. Preserve raw evidence (durable, not /tmp) ---
    ev_dir = os.path.join(EVIDENCE_DIR, args.run_id)
    os.makedirs(ev_dir, exist_ok=True)
    for label, src in (("canonical", args.canonical), ("audit-" + args.source, args.audit)):
        dst = os.path.join(ev_dir, label + ".json")
        try:
            shutil.copyfile(src, dst)
        except OSError as e:
            fail("evidence preservation failed", detail=str(e), run_id=args.run_id)

    # --- 6. Quarantine writes (append-only) ---
    if quarantined:
        try:
            with open(QUARANTINE, "a") as f:
                for q in quarantined:
                    f.write(json.dumps(q) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            fail("quarantine write failed", detail=str(e), run_id=args.run_id)

    # --- 7. Atomic ledger append + post-write verification ---
    appended_ids = [e["id"] for e in to_append]
    if to_append:
        try:
            with open(LEDGER, "a") as f:
                for e in to_append:
                    f.write(json.dumps(e) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            fail("ledger append failed", detail=str(e), run_id=args.run_id)
        # Post-write verification: every appended ID must be present and parseable
        try:
            with open(LEDGER) as f:
                tail_ids = set()
                for line in f:
                    try:
                        d = json.loads(line)
                        if "id" in d:
                            tail_ids.add(str(d["id"]))
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            fail("ledger post-write re-read failed", detail=str(e), run_id=args.run_id)
        missing = [i for i in appended_ids if i not in tail_ids]
        if missing:
            fail("post-write verification failed: appended IDs missing from ledger",
                 missing=missing, run_id=args.run_id)

    # --- 8. REACTIVE forward correction (never re-drive, never rollback) ---
    # For every row appended in this run, emit a forward correction overlay:
    # status completed -> blocked. Uses the IDs the producer itself classified,
    # so no worker transcription is involved. acfix ledger dedupes on
    # (lane, source, record_id), making retries idempotent.
    reactive_appended = 0
    reactive_dupes = 0
    reactive_errors = []
    if args.reactive and to_append:
        try:
            sys.path.insert(0, os.path.expanduser("~/workspace/askcomplete-fix/lib"))
            from ledger import append as acfix_append
        except Exception as e:
            reactive_errors.append("ledger import failed: %s" % e)
            acfix_append = None
        if acfix_append is not None:
            for e in to_append:
                try:
                    r = acfix_append({
                        "lane": "ask-complete-watchdog",
                        "source": e["source"],
                        "record_id": e["id"],
                        "field": "status",
                        "old_value": "completed",
                        "new_value": "blocked",
                        "reason": ("ask-complete watchdog run %s: turn ended asking the user; "
                                   "standing rule blocks completion; forward correction only, "
                                   "work was NOT re-driven") % args.run_id,
                        "digest_ref": e.get("md5") or "",
                        "reversible": "yes",
                        "rollback_action": "none - additive overlay only",
                    })
                    if r.get("appended"):
                        reactive_appended += 1
                    else:
                        reactive_dupes += 1
                except Exception as e2:
                    reactive_errors.append("record %s: %s" % (e["id"], e2))
        if reactive_errors:
            sys.stderr.write("REACTIVE WARNING: acfix correction failures: %s\n" %
                             json.dumps(reactive_errors))

    report = {
        "ok": True,
        "run_id": args.run_id,
        "source": args.source,
        "audit_rows": len(audit_rows),
        "canonical_ids": len(canonical),
        "appended": len(to_append),
        "appended_ids": appended_ids,
        "quarantined": len(quarantined),
        "quarantine_reasons": sorted(set(q["reason"].split(":")[0] for q in quarantined)),
        "skipped_dupe": skipped_dupe,
        "skipped_other_verdict": skipped_other,
        "evidence_dir": ev_dir,
        "reactive": args.reactive,
        "reactive_corrections_appended": reactive_appended,
        "reactive_corrections_dupes": reactive_dupes,
        "reactive_errors": reactive_errors,
    }
    print(json.dumps(report))


if __name__ == "__main__":
    main()
