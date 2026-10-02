#!/usr/bin/env python3
"""Corrections ledger: the reachable writer for ask->complete repairs.

Ask/completed, canned/completed, empty/completed, and skip/succeeded records
cannot be rewritten in the platform stores from here (read-only). This ledger
is the writable overlay: repair lanes append corrected verdicts here, and
downstream consumers (forensics, reconciliation, future guards) read it as
the corrected truth. Append-only; never edit or delete rows (additive rule).

Schema: ts, lane, source, record_id, field, old_value, new_value, reason,
        digest_ref, reversible, rollback_action
"""
import argparse
import json
import os
import sys
import time

import pyarrow as pa
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
LEDGER = os.path.join(BASE, "ledger", "corrections.parquet")

COLUMNS = ["ts", "lane", "source", "record_id", "field", "old_value",
           "new_value", "reason", "digest_ref", "reversible", "rollback_action"]


def _empty_table():
    return pa.table({c: pa.array([], type=pa.large_string()) for c in COLUMNS})


def read():
    if not os.path.exists(LEDGER):
        return _empty_table()
    return pq.read_table(LEDGER)


def has(lane, source, record_id):
    t = read()
    if t.num_rows == 0:
        return False
    lane_c = t.column("lane").to_pylist()
    src_c = t.column("source").to_pylist()
    rid_c = t.column("record_id").to_pylist()
    return any(l == lane and s == source and r == record_id
               for l, s, r in zip(lane_c, src_c, rid_c))


def append(row):
    """Append one correction row (dict). Dedupes on (lane, source, record_id)."""
    rec = {c: str(row.get(c, "")) for c in COLUMNS}
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if has(rec["lane"], rec["source"], rec["record_id"]):
        return {"appended": False, "reason": "duplicate", "record_id": rec["record_id"]}
    t = read()
    new = pa.table({c: pa.array([rec[c]], type=pa.large_string()) for c in COLUMNS})
    if t.num_rows:
        new = new.cast(t.schema)  # tolerate schema drift across writers
    out = pa.concat_tables([t, new]) if t.num_rows else new
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    pq.write_table(out, LEDGER, compression="zstd")
    return {"appended": True, "record_id": rec["record_id"], "rows": out.num_rows}


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("append")
    a.add_argument("--json", required=True, help="JSON object for one correction row")
    h = sub.add_parser("has")
    h.add_argument("--lane", required=True)
    h.add_argument("--source", required=True)
    h.add_argument("--record-id", required=True)
    c = sub.add_parser("count")
    b = sub.add_parser("batch")
    b.add_argument("--jsonl", required=True,
                   help="path to JSONL file: one correction object per line")
    args = ap.parse_args(argv)
    if args.cmd == "append":
        print(json.dumps(append(json.loads(args.json))))
    elif args.cmd == "batch":
        # Bounded idempotent batch: every row still flows through append(),
        # so dedupe on (lane, source, record_id) holds per row. Malformed
        # lines are counted, never fatal — the batch is fail-soft per row.
        appended = 0
        duplicates = 0
        errors = 0
        with open(args.jsonl) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    res = append(json.loads(line))
                except (json.JSONDecodeError, TypeError, ValueError):
                    errors += 1
                    continue
                if res["appended"]:
                    appended += 1
                else:
                    duplicates += 1
        print(json.dumps({"appended": appended, "duplicates": duplicates,
                          "errors": errors, "jsonl": args.jsonl}))
    elif args.cmd == "has":
        found = has(args.lane, args.source, args.record_id)
        print(json.dumps({"found": found}))
        sys.exit(0 if found else 1)
    elif args.cmd == "count":
        print(json.dumps({"rows": read().num_rows, "path": LEDGER}))


if __name__ == "__main__":
    main()
