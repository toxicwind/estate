#!/usr/bin/env python3
"""poll_log.py — capped tail-poll helper for bridge workers.

Tails a bridge worker's log via `agent.py log <id> --tail N` while ENFORCING
poll-rate caps BEFORE touching the bridge, so aggregate observability
traffic stays under a documented budget at fleet scale.

CAPS (documented + enforced):
  MIN_POLL_INTERVAL_SEC = 10    max 0.1 polls/sec/worker (burst gate)
  MAX_POLLS_PER_MINUTE  = 5     sliding 60s window (sustained <= 0.0833 polls/sec/worker)
  DEFAULT_TAIL_LINES    = 40
  MAX_LINE_CHARS        = 500   per-line truncation
  MAX_POLL_BYTES        = 20480 (20 KiB) per-poll byte budget

DERIVED BRIDGE BUDGET (per worker, worst case):
  5 polls/min x 20 KiB = 100 KiB/min = ~1.7 KiB/sec/worker
  10 workers -> 0.8 polls/sec, ~17 KiB/sec
  50 workers -> 4.2 polls/sec, ~83 KiB/sec, ~5 MiB/min
  Each poll is one exec.py round-trip (HTTPS ~0.6-7s wall, WS ~0.2s warm);
  the caps keep poll volume far under the bridge's serial capacity.

BEHAVIOR:
  - Calls too soon (before MIN_POLL_INTERVAL_SEC elapsed, or the 60s sliding
    window already holds MAX_POLLS_PER_MINUTE served polls) are SKIPPED:
    the bridge is NOT touched. Exit code 2, machine-readable reason.
  - Served polls are measured (wall latency ms, bytes returned) and every
    attempt is appended to a per-worker measurement log for evidence.

USAGE:
  poll_log.py <worker-id> [--tail N] [--json]
  poll_log.py --show-caps
"""
import argparse
import json
import os
import subprocess
import sys
import time

# --- enforced caps ----------------------------------------------------------
MIN_POLL_INTERVAL_SEC = 10
MAX_POLLS_PER_MINUTE = 5
DEFAULT_TAIL_LINES = 40
MAX_LINE_CHARS = 500
MAX_POLL_BYTES = 20480  # 20 KiB

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_PY = os.path.join(SKILL_DIR, "bin", "agent.py")
STATE_DIR = os.path.expanduser("~/.cache/capped-poll")


def sanitize(wid):
    return "".join(c if (c.isalnum() or c in "-_.") else "_" for c in wid)


def state_paths(wid):
    os.makedirs(STATE_DIR, exist_ok=True)
    base = os.path.join(STATE_DIR, sanitize(wid))
    return base + ".json", base + ".measurements.jsonl"


def load_state(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"last_poll_ts": 0.0, "recent_polls": []}


def save_state(path, state):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, path)


def log_measurement(mlog, row):
    row = dict(row)
    row["ts"] = time.time()
    with open(mlog, "a") as f:
        f.write(json.dumps(row) + "\n")


def check_caps(state, now):
    """Return (allowed: bool, reason: str, next_eligible_ts: float)."""
    recent = [t for t in state.get("recent_polls", []) if now - t < 60.0]
    state["recent_polls"] = recent
    last = state.get("last_poll_ts", 0.0)
    next_ok = last + MIN_POLL_INTERVAL_SEC
    if now < next_ok:
        return (False, "min-interval",
                "%.1fs since last poll; min interval %ds" %
                (now - last, MIN_POLL_INTERVAL_SEC), next_ok)
    if len(recent) >= MAX_POLLS_PER_MINUTE:
        oldest = min(recent)
        next_ok = oldest + 60.0
        return (False, "sliding-window",
                "%d polls in trailing 60s (cap %d)" %
                (len(recent), MAX_POLLS_PER_MINUTE), next_ok)
    return (True, "", "", now)


def poll_bridge(wid, tail_lines):
    """Run agent.py log; return (rc, stdout, stderr, latency_ms)."""
    t0 = time.monotonic()
    p = subprocess.run(
        [sys.executable, AGENT_PY, "log", wid, "--tail", str(tail_lines)],
        capture_output=True, text=True, timeout=180)
    latency_ms = (time.monotonic() - t0) * 1000.0
    return p.returncode, p.stdout or "", p.stderr or "", latency_ms


def cap_bytes(text):
    lines = []
    total = 0
    for raw in text.splitlines():
        line = raw[:MAX_LINE_CHARS]
        if raw != line:
            line += " ...[truncated]"
        if total + len(line) + 1 > MAX_POLL_BYTES:
            lines.append("...[poll byte budget %d bytes reached]" %
                         MAX_POLL_BYTES)
            break
        lines.append(line)
        total += len(line) + 1
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("worker_id", nargs="?", help="bridge worker id")
    ap.add_argument("--tail", type=int, default=DEFAULT_TAIL_LINES)
    ap.add_argument("--json", action="store_true",
                    help="machine-readable output")
    ap.add_argument("--show-caps", action="store_true")
    args = ap.parse_args()

    if args.show_caps:
        caps = {
            "min_poll_interval_sec": MIN_POLL_INTERVAL_SEC,
            "max_polls_per_minute": MAX_POLLS_PER_MINUTE,
            "default_tail_lines": DEFAULT_TAIL_LINES,
            "max_line_chars": MAX_LINE_CHARS,
            "max_poll_bytes": MAX_POLL_BYTES,
            "worst_case_bytes_per_sec_per_worker":
                MAX_POLLS_PER_MINUTE / 60.0 * MAX_POLL_BYTES,
        }
        print(json.dumps(caps, indent=2))
        return 0

    if not args.worker_id:
        ap.error("worker_id required")
    wid = args.worker_id
    spath, mlog = state_paths(wid)
    state = load_state(spath)
    now = time.time()

    allowed, reason, detail, next_ok = check_caps(state, now)
    if not allowed:
        row = {"served": False, "skipped_reason": reason, "detail": detail,
               "next_eligible_ts": next_ok, "latency_ms": 0.0, "bytes": 0}
        log_measurement(mlog, row)
        out = {"served": False, "skipped_reason": reason, "detail": detail,
               "next_eligible_ts": next_ok}
        if args.json:
            print(json.dumps(out))
        else:
            print("SKIP worker=%s reason=%s detail=%s next_eligible=%.1f" %
                  (wid, reason, detail, next_ok))
        return 2

    # mark BEFORE the bridge call so concurrent invocations serialize
    state["last_poll_ts"] = now
    state["recent_polls"].append(now)
    save_state(spath, state)

    rc, stdout, stderr, latency_ms = poll_bridge(wid, args.tail)
    capped = cap_bytes(stdout)
    row = {"served": True, "rc": rc, "tail_lines": args.tail,
           "latency_ms": round(latency_ms, 1),
           "bytes": len(capped.encode("utf-8"))}
    log_measurement(mlog, row)

    out = {"served": True, "rc": rc, "latency_ms": round(latency_ms, 1),
           "bytes": row["bytes"], "log": capped}
    if args.json:
        print(json.dumps(out))
    else:
        print(capped)
        if rc != 0 and stderr:
            sys.stderr.write("agent.py stderr: %s\n" % stderr.strip())
        print("--- served worker=%s latency_ms=%.0f bytes=%d "
              "cap=%d/min/60s-window ---" %
              (wid, latency_ms, row["bytes"], MAX_POLLS_PER_MINUTE))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
