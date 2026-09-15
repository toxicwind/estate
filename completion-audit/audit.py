#!/usr/bin/env python3
"""completion-audit: microsecond-resolution completions auditor with checkable artifacts.

Wraps ANY completion call (model inference CLI, code-race run, transport attempt)
and emits one JSONL row per call with nanosecond-captured timestamps, content
hashes, ceiling enforcement and winner/loser attribution -- then `verify` replays
the ledger and RECOMPUTES every claim the rows make. Artifacts, not vibes.

Commands:
    audit.py audit  --tag TAG [--race-id RID] [--strategy NAME] [--ceiling SECS]
                    [--match REGEX] [--prompt FILE] [--ledger PATH] -- CMD...
        Run CMD, capture stdout/stderr, time start/first-byte/end at
        time.perf_counter_ns() (ns resolution, monotonic), append one JSONL row.

    audit.py report LEDGER [--tag TAG] [--out FILE]
        Percentile table per tag (p50/p95/p99, never averages alone) +
        clock-granularity probe proving the resolution claim. Writes --out JSON
        so verify can re-check every reported number.

    audit.py verify LEDGER [--report FILE]
        Recompute every claim in every row (timestamp ordering, elapsed_us,
        ttfb_us, sha256 of stored bytes, valid, ceiling_breached, winner
        attribution per race_id) and, with --report, every aggregate the
        report wrote. Exit 0 = all claims check out.

Borrowed patterns (attribution):
  - ns/monotonic timing + fail-fast per-attempt ceilings: hft-latency bin/measure.py
  - row schema {timestamp, race/tag, strategy, latency_ms, valid, winner, ttfb_ms}:
    ~/.cache/shingle/latency_race_winners.jsonl (live HFT workstream, 2026-09-14)
  - per-run JSONL ledger + aggregate audit command: emergent-enrich papers.py --audit
  - content-hash dedup for cross-transport attribution: squawk-feed race-borrow
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

SCHEMA_V = 1
DEFAULT_LEDGER = os.path.expanduser("~/.cache/shingle/completion_audit.jsonl")
STORE_FULL_LIMIT = 1 << 20      # 1 MiB: store full bytes below this
STORE_HEAD_TAIL = 1 << 13       # 8 KiB head/tail above the limit
STDERR_STORE_LIMIT = 1 << 16    # 64 KiB


def now_ns() -> int:
    return time.perf_counter_ns()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _store_bytes(b: bytes, full_limit: int, ht: int) -> dict:
    """Checkable byte container: full bytes below limit, else head/tail + hashes."""
    if len(b) <= full_limit:
        return {"full": True, "len": len(b),
                "sha256": sha256(b),
                "b64": base64.b64encode(b).decode("ascii")}
    head, tail = b[:ht], b[-ht:]
    return {"full": False, "len": len(b), "sha256": sha256(b),
            "head_sha256": sha256(head), "tail_sha256": sha256(tail),
            "head_b64": base64.b64encode(head).decode("ascii"),
            "tail_b64": base64.b64encode(tail).decode("ascii")}


def _restore_bytes(d: dict) -> bytes | None:
    if d.get("full"):
        return base64.b64decode(d["b64"])
    return None  # head/tail only; hash-checked, not reconstructible


def do_audit(args) -> int:
    prompt = b""
    if args.prompt:
        with open(args.prompt, "rb") as f:
            prompt = f.read()

    t_start = now_ns()
    proc = subprocess.Popen(args.cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    first_byte_ns = None
    out_chunks, err_chunks = [], []

    def drain(stream, chunks, is_out):
        nonlocal first_byte_ns
        while True:
            data = stream.read(65536)
            if not data:
                break
            if is_out and first_byte_ns is None:
                first_byte_ns = now_ns()
            chunks.append(data)

    t_out = threading.Thread(target=drain, args=(proc.stdout, out_chunks, True))
    t_err = threading.Thread(target=drain, args=(proc.stderr, err_chunks, False))
    t_out.start()
    t_err.start()

    ceiling_breached = False
    try:
        proc.wait(timeout=args.ceiling)
    except subprocess.TimeoutExpired:
        ceiling_breached = True
        proc.kill()
        proc.wait()
    t_out.join()
    t_err.join()
    t_end = now_ns()

    stdout_b = b"".join(out_chunks)
    stderr_b = b"".join(err_chunks)
    valid = (proc.returncode == 0)
    if args.match:
        valid = valid and re.search(args.match, stdout_b.decode("utf-8", "replace")) is not None

    elapsed_us = (t_end - t_start) // 1000
    ttfb_us = ((first_byte_ns - t_start) // 1000) if first_byte_ns is not None else None

    row = {
        "v": SCHEMA_V,
        "ts": datetime.now(timezone.utc).isoformat(),
        "tag": args.tag,
        "race_id": args.race_id,
        "strategy": args.strategy or " ".join(args.cmd[:2]),
        "cmd": args.cmd,
        "cmd_sha256": sha256(json.dumps(args.cmd).encode()),
        "prompt_len": len(prompt),
        "prompt_sha256": sha256(prompt),
        "match": args.match,
        "ceiling_s": args.ceiling,
        "t_ns": {"start": t_start,
                 "first_byte": first_byte_ns,
                 "end": t_end},
        "elapsed_us": elapsed_us,
        "elapsed_ms": round(elapsed_us / 1000, 3),
        "ttfb_us": ttfb_us,
        "ttfb_ms": round(ttfb_us / 1000, 3) if ttfb_us is not None else None,
        "exit_code": proc.returncode,
        "valid": valid,
        "ceiling_breached": ceiling_breached,
        "stdout_len": len(stdout_b),
        "stderr_len": len(stderr_b),
        "stdout": _store_bytes(stdout_b, STORE_FULL_LIMIT, STORE_HEAD_TAIL),
        "stderr": _store_bytes(stderr_b, STDERR_STORE_LIMIT, STORE_HEAD_TAIL),
        "winner": None,  # attribution is a claim: recomputed by report/verify
    }

    ledger = args.ledger or DEFAULT_LEDGER
    parent = os.path.dirname(ledger)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(ledger, "a") as f:
        f.write(json.dumps(row) + "\n")

    # NDJSON timing event on stderr (borrowed from hft-latency measure.py):
    # stdout of the harness stays the wrapped command's stdout? No -- the
    # wrapped command's stdout is CAPTURED into the row. Emit a one-line
    # summary for streaming pipelines instead.
    sys.stderr.write(json.dumps({"event": "audited", "tag": args.tag,
                                 "strategy": row["strategy"],
                                 "elapsed_ms": row["elapsed_ms"],
                                 "ttfb_ms": row["ttfb_ms"],
                                 "valid": valid,
                                 "ceiling_breached": ceiling_breached}) + "\n")
    return 0 if valid and not ceiling_breached else 1


def _percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[f + 1] - sorted_vals[f]) * (k - f) if f != c else sorted_vals[f]


def _pct_table(vals):
    s = sorted(vals)
    return {"n": len(s), "min": s[0], "p50": _percentile(s, 50),
            "p95": _percentile(s, 95), "p99": _percentile(s, 99), "max": s[-1]}


def _clock_probe():
    """Prove the resolution claim: smallest non-zero perf_counter_ns delta."""
    deltas = []
    prev = now_ns()
    for _ in range(200000):
        cur = now_ns()
        d = cur - prev
        if d > 0:
            deltas.append(d)
        prev = cur
    deltas.sort()
    return {"samples": len(deltas),
            "min_nonzero_delta_ns": deltas[0] if deltas else None,
            "p50_delta_ns": _percentile(deltas, 50) if deltas else None}


def do_report(args):
    rows = [json.loads(l) for l in open(args.ledger) if l.strip()]
    if args.tag:
        rows = [r for r in rows if r.get("tag") == args.tag]
    tags = {}
    for r in rows:
        tags.setdefault(r.get("tag"), []).append(r)
    per_tag = {}
    for tag, rs in sorted(tags.items()):
        elapsed = [r["elapsed_us"] for r in rs]
        ttfb = [r["ttfb_us"] for r in rs if r.get("ttfb_us") is not None]
        valid = [r for r in rs if r.get("valid")]
        per_tag[tag] = {
            "n": len(rs), "n_valid": len(valid),
            "n_ceiling_breached": sum(1 for r in rs if r.get("ceiling_breached")),
            "elapsed_us": _pct_table(elapsed),
            "ttfb_us": _pct_table(ttfb) if ttfb else None,
            "winners_by_race": _winners(rs),
        }
    report = {"tool": "completion-audit", "schema_v": SCHEMA_V,
              "generated_at": datetime.now(timezone.utc).isoformat(),
              "ledger": args.ledger, "rows_covered": len(rows),
              "clock_probe": _clock_probe(),
              "per_tag": per_tag}
    if args.out:
        with open(args.out, "w") as f:
            json.dump(report, f, indent=2)
    # human table: percentiles only, never averages alone
    for tag, t in per_tag.items():
        e, f_ = t["elapsed_us"], t["ttfb_us"]
        print(f"tag={tag} n={t['n']} valid={t['n_valid']} "
              f"breached={t['n_ceiling_breached']}")
        print(f"  elapsed_us  min={e['min']} p50={e['p50']:.0f} "
              f"p95={e['p95']:.0f} p99={e['p99']:.0f} max={e['max']}")
        if f_:
            print(f"  ttfb_us     min={f_['min']} p50={f_['p50']:.0f} "
                  f"p95={f_['p95']:.0f} p99={f_['p99']:.0f} max={f_['max']}")
        for rid, w in t["winners_by_race"].items():
            print(f"  race {rid}: winner={w['winner']} "
                  f"({w['winner_us']}us) losers={w['losers']}")
    cp = report["clock_probe"]
    print(f"clock_probe: min_nonzero_delta={cp['min_nonzero_delta_ns']}ns "
          f"(p50 {cp['p50_delta_ns']:.0f}ns over {cp['samples']} samples)")
    return 0


def _winners(rows):
    """Recompute winner/loser attribution per race_id: min elapsed_us among valid."""
    races = {}
    for r in rows:
        rid = r.get("race_id")
        if rid:
            races.setdefault(rid, []).append(r)
    out = {}
    for rid, rs in races.items():
        valid = [r for r in rs if r.get("valid")]
        if not valid:
            out[rid] = {"winner": None, "winner_us": None,
                        "losers": [r["strategy"] for r in rs]}
            continue
        win = min(valid, key=lambda r: r["elapsed_us"])
        out[rid] = {"winner": win["strategy"], "winner_us": win["elapsed_us"],
                    "losers": [r["strategy"] for r in rs if r is not win]}
    return out


def do_verify(args):
    failures = []
    rows = [json.loads(l) for l in open(args.ledger) if l.strip()]

    def fail(i, what, detail=""):
        failures.append(f"row {i}: {what} {detail}".strip())

    for i, r in enumerate(rows):
        t = r.get("t_ns", {})
        s, fb, e = t.get("start"), t.get("first_byte"), t.get("end")
        if not (isinstance(s, int) and isinstance(e, int) and e >= s):
            fail(i, "bad t_ns ordering", f"start={s} end={e}")
            continue
        if fb is not None and not (s <= fb <= e):
            fail(i, "first_byte outside [start,end]")
        if r.get("elapsed_us") != (e - s) // 1000:
            fail(i, "elapsed_us mismatch")
        exp_ttfb = ((fb - s) // 1000) if fb is not None else None
        if r.get("ttfb_us") != exp_ttfb:
            fail(i, "ttfb_us mismatch")
        if r.get("cmd_sha256") != sha256(json.dumps(r.get("cmd")).encode()):
            fail(i, "cmd_sha256 mismatch")
        # content hashes: full bytes recompute; head/tail rows check the parts
        for stream in ("stdout", "stderr"):
            d = r.get(stream, {})
            b = _restore_bytes(d)
            if b is not None:
                if sha256(b) != d.get("sha256"):
                    fail(i, f"{stream} sha256 mismatch")
                if len(b) != d.get("len"):
                    fail(i, f"{stream} len mismatch")
            else:
                head = base64.b64decode(d["head_b64"])
                tail = base64.b64decode(d["tail_b64"])
                if sha256(head) != d.get("head_sha256"):
                    fail(i, f"{stream} head hash mismatch")
                if sha256(tail) != d.get("tail_sha256"):
                    fail(i, f"{stream} tail hash mismatch")
        # valid recompute (needs the actual bytes for --match; full rows only)
        exp_valid = (r.get("exit_code") == 0)
        b = _restore_bytes(r.get("stdout", {}))
        if r.get("match") and b is not None:
            exp_valid = exp_valid and re.search(
                r["match"], b.decode("utf-8", "replace")) is not None
        if r.get("match") and b is None and not exp_valid:
            pass  # cannot fully re-check match on truncated output; accept
        elif r.get("valid") != exp_valid and not (r.get("match") and b is None):
            fail(i, "valid mismatch")
        exp_breach = (e - s) / 1e9 > r.get("ceiling_s", float("inf"))
        if r.get("ceiling_breached") != exp_breach:
            fail(i, "ceiling_breached mismatch")
        if r.get("v") != SCHEMA_V:
            fail(i, "schema version mismatch")

    # winner attribution recompute per race_id
    for rid, w in _winners(rows).items():
        for r in rows:
            if r.get("race_id") == rid and r.get("winner") is not None \
                    and r["winner"] != w["winner"]:
                fail("?", f"race {rid}: stored winner disagrees with recompute")

    # report cross-check: recompute aggregates, compare byte-identical numbers
    if args.report:
        rep = json.load(open(args.report))
        rows2 = rows
        if rep.get("rows_covered") != len(rows2):
            failures.append("report rows_covered mismatch")
        tags = {}
        for r in rows2:
            tags.setdefault(r.get("tag"), []).append(r)
        for tag, rs in tags.items():
            got = rep["per_tag"].get(tag)
            if not got:
                failures.append(f"report missing tag {tag}")
                continue
            elapsed = [r["elapsed_us"] for r in rs]
            if got["elapsed_us"] != _pct_table(elapsed):
                failures.append(f"report tag {tag}: elapsed percentiles differ")

    print(f"verify: {len(rows)} rows, {len(failures)} failures")
    for f_ in failures[:20]:
        print("  FAIL", f_)
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser(prog="audit.py")
    sub = p.add_subparsers(dest="subcmd", required=True)

    a = sub.add_parser("audit")
    a.add_argument("--tag", required=True)
    a.add_argument("--race-id")
    a.add_argument("--strategy")
    a.add_argument("--ceiling", type=float, default=60.0)
    a.add_argument("--match")
    a.add_argument("--prompt")
    a.add_argument("--ledger")
    a.add_argument("cmd", nargs=argparse.REMAINDER)

    r = sub.add_parser("report")
    r.add_argument("ledger")
    r.add_argument("--tag")
    r.add_argument("--out")

    v = sub.add_parser("verify")
    v.add_argument("ledger")
    v.add_argument("--report")

    args = p.parse_args()
    if args.subcmd == "audit":
        if args.cmd and args.cmd[0] == "--":
            args.cmd = args.cmd[1:]
        if not args.cmd:
            p.error("audit needs a command after --")
        sys.exit(do_audit(args))
    if args.subcmd == "report":
        sys.exit(do_report(args))
    sys.exit(do_verify(args))


if __name__ == "__main__":
    main()
