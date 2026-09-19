#!/usr/bin/env python3
"""
sidechat-watch.py — deterministic side-chat watcher (workstream A spec).

The LLM worker is NOT in the read path: it runs 1-2 indexed queries via
muse.db and pipes rows through this script. This script computes the
verdict deterministically, maintains a per-watch watermark (forward scan,
O(new rows) — never the transcript tip), appends a run ledger, and prints
the mandatory one-line summary. Output is NEVER empty.

Watermarks live under <WATERMARK_DIR>/<watch-id>.json (default:
~/workspace/goals/fleet-chat-consolidation/hidden_files/sidechat-watch/).
Never in memory files.

Usage (run by the cron worker via `taskhook run --`):
  sidechat-watch.py --watch-id <id> --print-aid
  sidechat-watch.py --watch-id <id> --seed <aid> <last_seq>
  sidechat-watch.py --watch-id <id> --seed <aid> -1   (bootstrap_failed sentinel; never scanned)
  sidechat-watch.py --watch-id <id> --query          (legacy DB path; kept as fallback)
  sidechat-watch.py --watch-id <id> --read-jsonl     (preferred: local transcript forward read)
  sidechat-watch.py --aid <aid> --read-jsonl --tail-jsonl 20
  sidechat-watch.py --aid <aid> --tip-jsonl          (max seq of local transcript)
  sidechat-watch.py --watch-id <id> --rows <json-file>

Read-path note (2026-09-19, measured — supersedes the earlier blanket claim
that every agent_id-filtered read is a full table scan):
- Forward range scan (WHERE agent_id=X AND seq > watermark ORDER BY seq ASC
  LIMIT 100) is index-served on UNIQUE (agent_id, seq): O(new rows), immune
  to transcript growth. Live-verified on all five watches (watermarks
  advancing every tick; a direct probe returned in budget).
- The pathological query is the BACKWARD tip/tail scan (ORDER BY seq DESC
  LIMIT 1/20): on transcripts with long tool-call tails it dies on the 3s DB
  statement timeout (limits.statement_timeout_ms=3000, NOT 5s — agent2 logged
  39 statement timeouts in 3h; even count(*)/max(seq) died), and the
  fleet-wide DB pool itself intermittently exhausts ("pool timed out while
  waiting for an open connection"). Bootstrap therefore avoids the tip scan.
- The runtime mirrors every context item to
  /home/hatch/agents/agent-<aid>/sessions/*.jsonl with IDENTICAL seq
  numbering — verified 2026-09-19: --tip-jsonl equals the DB watermark for
  agent1/madeon/safety/whatsapp, and agent2's JSONL tip runs ahead of its DB
  watermark by exactly the rows written since its last tick (monotonic).
  Local reads take milliseconds with zero DB-pool load, so --read-jsonl /
  --tip-jsonl are the primary path; the DB --query path is the fallback.
Bootstrap sentinel: --seed <aid> -1 writes last_seq=-1 with status
"bootstrap_failed". A negative last_seq is NEVER scanned: --query,
--read-jsonl and --rows all refuse with WATCH-FAIL until the cold path
re-seeds successfully. Seeding 0 would replay the whole transcript as "new"
and page on ancient messages — never do it.

Rows JSON: [{"s": seq, "r": role, "txt": text<=400, "ca": created_at_epoch,
             "is_canned": bool}, ...]  or  {"error": "<verbatim error text>"}
"""

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import signal
import sys
import time

# Canned-refusal digests (classify by digest only — never quote bodies).
# md5(text_content) is computed in SQL over the bounded new-row set.
CANNED_DIGESTS = {
    "b4aefd29108f232f9c0d5a4b030215c1",  # 384-char storm body
    "582bcbd080daeb3f826c45ed4a83b265",  # 96-char storm body
}

AID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

DEFAULT_WM_DIR = os.path.expanduser(
    "~/workspace/goals/fleet-chat-consolidation/hidden_files/sidechat-watch")

# watch-id -> {sid, kind, mode}. kind=whatsapp uses the channel resolver.
WATCHES = {
    "agent1":   {"sid": "8a756bd0-3361-427f-8b30-2ec0860e91e5", "kind": "standard", "mode": "report"},
    "agent2":   {"sid": "0fcb5f23-25d7-44de-9a7d-76342c7b4dd8", "kind": "standard", "mode": "report"},
    "madeon":   {"sid": "cc3ea0e2-2fb8-45f3-846c-b86ef71210ac", "kind": "standard", "mode": "report"},
    "safety":   {"sid": "d5c06065-f0b5-4e0b-8026-44a2482806d7", "kind": "standard", "mode": "safety-nudge"},
    "whatsapp": {"sid": None, "kind": "whatsapp", "mode": "report"},
}

READ_SQL = """SELECT seq AS s, role AS r, left(text_content, 400) AS txt, extract(epoch from created_at)::bigint AS ca,
       (md5(text_content) IN ('b4aefd29108f232f9c0d5a4b030215c1','582bcbd080daeb3f826c45ed4a83b265')) AS is_canned
FROM agent.context_items
WHERE agent_id = '{aid}' AND seq > {last_seq} AND role IN ('user', 'assistant')
ORDER BY seq ASC LIMIT 100"""


def _wm_path(watch_id, wm_dir):
    return os.path.join(wm_dir, f"{watch_id}.json")


def load_watermark(watch_id, wm_dir):
    """Return (aid or None, last_seq or None, raw dict or None)."""
    p = _wm_path(watch_id, wm_dir)
    try:
        with open(p) as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None, None, None
    aid = d.get("aid")
    if not isinstance(aid, str) or not AID_RE.match(aid):
        return None, None, d
    try:
        last_seq = int(d.get("last_seq"))
    except (TypeError, ValueError):
        return None, None, d
    return aid, last_seq, d


def save_watermark(watch_id, wm_dir, aid, last_seq, last_status):
    os.makedirs(wm_dir, exist_ok=True)
    payload = {"aid": aid, "last_seq": int(last_seq),
               "last_run_utc": int(time.time()), "last_status": last_status}
    tmp = _wm_path(watch_id, wm_dir) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f)
    os.replace(tmp, _wm_path(watch_id, wm_dir))
    return payload


def append_ledger(wm_dir, entry):
    os.makedirs(wm_dir, exist_ok=True)
    with open(os.path.join(wm_dir, "run-ledger.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def utc_ts(v):
    """Format a timestamp robustly. Accepts epoch int/float, numeric
    strings, ISO-8601 strings, or None. Never raises: returns 'unknown'
    when the value is unparseable (a bad timestamp must not kill the run —
    2026-09-19 incident: created_at arrived as ISO text and TypeError'd)."""
    try:
        if isinstance(v, bool):
            return "unknown"
        if isinstance(v, (int, float)):
            e = float(v)
        elif isinstance(v, str):
            s = v.strip()
            try:
                e = float(s)
            except ValueError:
                import datetime
                dt = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                e = dt.timestamp()
        else:
            return "unknown"
        return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(e))
    except Exception:
        return "unknown"


def cmd_print_aid(watch_id, wm_dir):
    aid, last_seq, _ = load_watermark(watch_id, wm_dir)
    # Empty line = cold path needed: no cached aid, invalid aid, or the
    # bootstrap_failed sentinel (last_seq < 0). Never print anything else.
    if aid and last_seq is not None and last_seq >= 0:
        print(aid)
    else:
        print("")


def cmd_seed(watch_id, wm_dir, aid, last_seq):
    if watch_id not in WATCHES:
        print(f"WATCH-FAIL {watch_id} | seed | unknown watch id | wm=unchanged")
        return 2
    if not AID_RE.match(aid or ""):
        print(f"WATCH-FAIL {watch_id} | seed | aid failed UUID validation | wm=unchanged")
        return 2
    try:
        seq = int(last_seq)
    except (TypeError, ValueError):
        print(f"WATCH-FAIL {watch_id} | seed | last_seq not an int | wm=unchanged")
        return 2
    if seq < 0:
        # Bootstrap sentinel: the tip is unavailable from both the local
        # transcript and the DB. A negative last_seq is never scanned (see
        # the guards in cmd_query/cmd_read_jsonl/cmd_rows); the next cold
        # path retries the tip instead of replaying the transcript from 0.
        save_watermark(watch_id, wm_dir, aid, -1, "bootstrap_failed")
        print(f"WATCH-FAIL {watch_id} | bootstrap | tip unavailable (jsonl + 3x DB attempts) | wm=-1 bootstrap_failed")
        return 2
    save_watermark(watch_id, wm_dir, aid, seq, "seeded")
    print(f"WATCH-OK {watch_id} | wm={seq} | new=0 unhandled=0 | seeded")


def _sentinel_msg(watch_id):
    return (f"bootstrap_failed sentinel: the transcript tip was unavailable; "
            f"re-run the cold path for {watch_id} instead of scanning")


def cmd_query(watch_id, wm_dir):
    aid, last_seq, _ = load_watermark(watch_id, wm_dir)
    if not aid:
        print(f"WATCH-FAIL {watch_id} | query | no watermark: run --seed first | wm=unchanged")
        return 2
    if last_seq is not None and last_seq < 0:
        # Sentinel: refuse to scan. The worker writes stdout to the rows
        # file, so emit the error as JSON for cmd_rows to classify.
        print(json.dumps({"error": _sentinel_msg(watch_id)}))
        return 2
    print(READ_SQL.format(aid=aid, last_seq=last_seq))
    return 0


def _agent_sessions_dir(aid):
    return os.path.join(os.path.expanduser("~"), "agents",
                        "agent-%s" % aid, "sessions")


def _parse_epoch(ts):
    """created_at like '2026-09-15T09:42:19.209409093+00:00' -> int epoch."""
    if isinstance(ts, bool):
        return 0
    if isinstance(ts, (int, float)):
        return int(ts)
    if not isinstance(ts, str) or not ts:
        return 0
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?(.*)$",
                 ts.strip())
    if not m:
        return 0
    frac = (m.group(2) or "")
    frac = (frac + "000000")[:6]
    try:
        dt = datetime.datetime.fromisoformat(
            "%s.%s%s" % (m.group(1), frac, m.group(3)))
    except ValueError:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return int(dt.timestamp())


def _iter_jsonl_items(aid):
    """Yield (seq, outer_dict) for every {"type":"item"} line in the agent's
    local session transcript files, in file order."""
    d = _agent_sessions_dir(aid)
    if not os.path.isdir(d):
        raise FileNotFoundError("no sessions dir: %s" % d)
    files = sorted(glob.glob(os.path.join(d, "*.jsonl")))
    if not files:
        raise FileNotFoundError("no jsonl transcripts in %s" % d)
    for path in files:
        try:
            f = open(path, "r")
        except OSError:
            continue
        with f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(o, dict) or o.get("type") != "item":
                    continue
                try:
                    seq = int(o.get("seq", -1))
                except (TypeError, ValueError):
                    continue
                yield seq, o


def cmd_tip_jsonl(aid):
    """Print the max seq across the local transcript (for watermark seeding)."""
    try:
        mx = 0
        for seq, _ in _iter_jsonl_items(aid):
            if seq > mx:
                mx = seq
        print(mx)
        return 0
    except FileNotFoundError as e:
        print("ERROR: %s" % e)
        return 2
    except Exception as e:
        print("ERROR: jsonl tip failed: %s" % e)
        return 2


def cmd_read_jsonl(watch_id, wm_dir, aid=None, tail_n=None, limit=500):
    """Forward read of user/assistant message rows from the local transcript.

    Watermark mode (default): rows with seq > watermark's last_seq, seq ASC,
    capped at `limit`. Tail mode (tail_n set): last `tail_n` message rows.
    Prints a JSON array of {s, r, txt, ca, is_canned}, or {"error": ...}.
    """
    if aid is None:
        aid, last_seq, _ = load_watermark(watch_id, wm_dir)
        if not aid:
            print(json.dumps({"error": "no watermark: run --seed first"}))
            return 2
        if last_seq is not None and last_seq < 0:
            print(json.dumps({"error": _sentinel_msg(watch_id)}))
            return 2
    else:
        if not AID_RE.match(aid or ""):
            print(json.dumps({"error": "aid failed UUID validation"}))
            return 2
        last_seq = -1
    try:
        rows = []
        for seq, o in _iter_jsonl_items(aid):
            it = o.get("item") or {}
            if not isinstance(it, dict) or it.get("type") != "message":
                continue
            role = it.get("role")
            if role not in ("user", "assistant"):
                continue
            if tail_n is None and seq <= last_seq:
                continue
            text = it.get("text") or ""
            if not isinstance(text, str):
                text = str(text)
            rows.append((seq, role, text, _parse_epoch(o.get("created_at"))))
        rows.sort(key=lambda r: r[0])
        rows = rows[-tail_n:] if tail_n is not None else rows[:limit]
        out = [{
            "s": seq,
            "r": role,
            "txt": text[:400],
            "ca": ca,
            "is_canned": hashlib.md5(text.encode("utf-8", "replace")).hexdigest()
                       in CANNED_DIGESTS,
        } for seq, role, text, ca in rows]
        print(json.dumps(out))
        return 0
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}))
        return 2
    except Exception as e:
        print(json.dumps({"error": "jsonl read failed: %s" % e}))
        return 2


def cmd_rows(watch_id, wm_dir, rows_file):
    if watch_id not in WATCHES:
        print(f"WATCH-FAIL {watch_id} | rows | unknown watch id | wm=unchanged")
        return 2
    mode = WATCHES[watch_id]["mode"]
    aid, last_seq, _ = load_watermark(watch_id, wm_dir)
    if not aid:
        print(f"WATCH-FAIL {watch_id} | rows | no watermark: run --seed first | wm=unchanged")
        return 2
    if last_seq is not None and last_seq < 0:
        entry = {"watch_id": watch_id, "ts": utc_ts(time.time()), "ok": False,
                 "step": "rows", "error": _sentinel_msg(watch_id), "wm": -1}
        append_ledger(wm_dir, entry)
        print(f"WATCH-FAIL {watch_id} | rows | {_sentinel_msg(watch_id)} | wm=-1 unchanged")
        return 2
    try:
        with open(rows_file) as f:
            payload = json.load(f)
    except (OSError, ValueError) as e:
        entry = {"watch_id": watch_id, "ts": utc_ts(time.time()), "ok": False,
                 "step": "rows", "error": f"unreadable rows file: {e}", "wm": last_seq}
        append_ledger(wm_dir, entry)
        print(f"WATCH-FAIL {watch_id} | rows | unreadable rows file | wm={last_seq} unchanged")
        return 2

    # Error payload from the worker: record, do NOT advance the watermark.
    # A timeout never reads as empty or as seen; the next tick re-reads.
    if isinstance(payload, dict) and "error" in payload:
        err = str(payload["error"])[:200]
        save_watermark(watch_id, wm_dir, aid, last_seq, f"read_error: {err[:80]}")
        entry = {"watch_id": watch_id, "ts": utc_ts(time.time()), "ok": False,
                 "step": "read", "error": err, "wm": last_seq}
        append_ledger(wm_dir, entry)
        print(f"WATCH-FAIL {watch_id} | read | {err} | wm={last_seq} unchanged")
        return 0

    rows = payload if isinstance(payload, list) else payload.get("rows", [])
    # Deterministic verdict: walk seq-ascending. A user row is pending until a
    # later non-canned assistant row. A canned assistant row does NOT clear it
    # (a refusal is not a substantive reply — the message stays unhandled).
    pending = []  # list of user rows awaiting a reply
    for row in sorted(rows, key=lambda r: r.get("s", 0)):
        role = row.get("r")
        if role == "user":
            pending.append(row)
        elif role == "assistant" and not row.get("is_canned"):
            pending = []

    max_seq = last_seq
    for row in rows:
        try:
            s = int(row.get("s", 0))
        except (TypeError, ValueError):
            continue
        if s > max_seq:
            max_seq = s

    unhandled = []
    for u in pending:
        item = {"seq": u.get("s"), "ts": utc_ts(u.get("ca", 0))}
        if mode == "safety-nudge":
            item["topic"] = "(text withheld per safety-watch policy)"
        else:
            item["text"] = (u.get("txt") or "")[:400]
        unhandled.append(item)

    # Advance the watermark only on a complete successful read.
    save_watermark(watch_id, wm_dir, aid, max_seq, "ok")
    entry = {"watch_id": watch_id, "ts": utc_ts(time.time()), "ok": True,
             "new": len(rows), "unhandled": len(unhandled), "wm": max_seq,
             "brief": unhandled}
    append_ledger(wm_dir, entry)

    if unhandled:
        first = unhandled[0]
        if mode == "safety-nudge":
            brief = f"{len(unhandled)} unhandled user msg(s), latest seq {first['seq']} at {first['ts']}"
        else:
            brief = f"{len(unhandled)} unhandled: seq {first['seq']} at {first['ts']}: {(first.get('text') or '')[:80]}"
    else:
        brief = "clean"
    print(f"WATCH-OK {watch_id} | wm={max_seq} | new={len(rows)} unhandled={len(unhandled)} | {brief}")
    return 0


def main():
    # Hang-proofing: 60s SIGALRM watchdog. On fire, print the failure line
    # and exit — the worker must never hang inside the script.
    def _alarm(signum, frame):
        sys.stdout.write("WATCH-FAIL unknown | script-timeout | 60s SIGALRM | wm=unchanged\n")
        sys.stdout.flush()
        os._exit(2)

    try:
        signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(60)
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--watch-id", required=False, default=None)
    ap.add_argument("--wm-dir", default=None)
    ap.add_argument("--print-aid", action="store_true")
    ap.add_argument("--seed", nargs=2, metavar=("AID", "LAST_SEQ"))
    ap.add_argument("--query", action="store_true")
    ap.add_argument("--read-jsonl", action="store_true",
                    help="read message rows from the local session transcript")
    ap.add_argument("--tail-jsonl", type=int, default=None, metavar="N",
                    help="with --read-jsonl: return last N message rows")
    ap.add_argument("--tip-jsonl", action="store_true",
                    help="print max seq of the local session transcript")
    ap.add_argument("--aid", default=None,
                    help="agent id override for --read-jsonl/--tip-jsonl")
    ap.add_argument("--rows", metavar="JSON_FILE")
    args = ap.parse_args()

    wm_dir = args.wm_dir or os.environ.get("SIDECHAT_WATCH_WM_DIR") or DEFAULT_WM_DIR
    # Local-transcript modes bypass the watch registry when --aid is given
    # (e.g. squawk resolves its aid per-run instead of using a watermark).
    if args.read_jsonl:
        if args.aid:
            return cmd_read_jsonl(args.watch_id, wm_dir, aid=args.aid,
                                  tail_n=args.tail_jsonl)
        if args.watch_id not in WATCHES:
            print(json.dumps({"error": "unknown watch id: %s" % args.watch_id}))
            return 2
        return cmd_read_jsonl(args.watch_id, wm_dir, tail_n=args.tail_jsonl)
    if args.tip_jsonl:
        aid = args.aid
        if aid is None and args.watch_id in WATCHES:
            aid, _, _ = load_watermark(args.watch_id, wm_dir)
        if not aid:
            print("ERROR: no aid (seed the watermark or pass --aid)")
            return 2
        return cmd_tip_jsonl(aid)
    if args.watch_id not in WATCHES:
        print(f"WATCH-FAIL {args.watch_id} | args | unknown watch id | wm=unchanged")
        return 2
    if args.print_aid:
        cmd_print_aid(args.watch_id, wm_dir)
        return 0
    if args.seed:
        return cmd_seed(args.watch_id, wm_dir, args.seed[0], args.seed[1])
    if args.query:
        return cmd_query(args.watch_id, wm_dir)
    if args.rows:
        return cmd_rows(args.watch_id, wm_dir, args.rows)
    ap.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
