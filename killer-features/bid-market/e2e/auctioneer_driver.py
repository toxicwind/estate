"""E2E auctioneer DRIVER (test harness — not the production auctioneer).

t2-impl-auctioneer is still building the real auctioneer. To get REAL e2e
evidence now, this driver implements PROTOCOL.md v0's auction mechanics
exactly:
  - TASK_POST (HMAC-signed via signpost.py) with the task spec
  - bid collection over the protocol's bid_window_ms (inotify-driven)
  - deterministic tie-break: highest confidence, lowest eta_ms,
    lexicographically smallest bidder_id
  - ASSIGN (signed), then inotify-driven RESULT collection
The bidders are the REAL bidder.py processes; the wire format, signing,
and timing are all real. When the real auctioneer lands, this driver is
retired (run_e2e market --auctioneer real).
"""

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIDMARKET = HERE.parent  # killer-features/bid-market
sys.path.insert(0, str(BIDMARKET))
sys.path.insert(0, str(HERE))

import signpost  # noqa: E402
import tasks as task_defs  # noqa: E402
from executor import SOLUTIONS  # noqa: E402

CHANNEL = "bid-market"
AUCTIONEER_ID = "auctioneer-e2e"
BID_WINDOW_S = 8.0
RESULT_TIMEOUT_S = 150.0

TAGS = {"shell-text": ["shell", "text"], "shell-file": ["shell", "file"],
        "python-compute": ["python", "compute"],
        "python-data": ["python", "data"]}

_chan_dir = signpost.CHAT_ROOT / CHANNEL


def parse_frontmatter(path):
    fm, body = {}, ""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return fm, body
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fm, text
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        if ":" in lines[i]:
            k, v = lines[i].split(":", 1)
            fm[k.strip()] = v.strip()
        i += 1
    return fm, "\n".join(lines[i + 1:])


def _json_body(body):
    body = body.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(body)


def build_payload(task, workdir):
    """Turn an e2e task into a PROTOCOL.md TASK_POST (kind, payload, tags).

    Reuses the exact canonical solutions from executor.py (proven by
    selftest), anchored at the absolute workdir so the bidder's executor
    (cwd=/tmp for python, inherited for shell) hits the right files.
    """
    kind = "shell" if set(task["requires"]) == {"shell"} else "python"
    skind, code = SOLUTIONS[task["id"]]
    assert skind == kind, "solution kind mismatch for %s" % task["id"]
    if kind == "shell":
        payload = "cd %s && %s" % (shlex.quote(workdir), code)
    else:
        payload = "import os\nos.chdir(%r)\n%s" % (workdir, code)
    return kind, payload, TAGS[task["category"]]


def _inotify_drain(timeout_s):
    """Block until timeout_s with zero wakeups when idle; yield filenames."""
    p = subprocess.Popen(
        ["inotifywait", "-m", "-e", "close_write", "-e", "moved_to",
         "--format", "%f", "--timeout", str(int(timeout_s + 0.5)),
         str(_chan_dir)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        for line in p.stdout:
            yield line.strip()
    finally:
        p.kill()


def _scan(task_id, msg_types):
    """Scan channel files for messages of msg_types matching task_id."""
    out = []
    if not _chan_dir.is_dir():
        return out
    for path in sorted(_chan_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        if fm.get("msg_type") not in msg_types:
            continue
        try:
            payload = _json_body(body)
        except (ValueError, IndexError):
            continue
        tid = payload.get("task_id") or fm.get("task_id")
        if tid == task_id:
            out.append(payload)
    return out


def post_task(task, workdir, task_id):
    kind, payload, tags = build_payload(task, workdir)
    # timeout 30s: every e2e task completes in <5s real; keeps flash
    # (max_timeout_ms=30s) in the auction — a 120s timeout would
    # silently exclude the fastest bidder from every auction.
    spec = {"task_id": task_id, "title": task["title"], "kind": kind,
            "payload": payload, "timeout_ms": 30_000,
            "bid_window_ms": int(BID_WINDOW_S * 1000), "tags": tags,
            "posted_ts": time.time()}
    signpost.ensure_key(AUCTIONEER_ID)
    seq, _ = signpost.post(CHANNEL, AUCTIONEER_ID, "task_post", spec,
                           task_id=task_id,
                           title="task-%s" % task_id, status="bid-market")
    return spec, seq


def collect_bids(task_id):
    for _ in _inotify_drain(BID_WINDOW_S):
        pass  # wake on activity; the window is the deadline
    return _scan(task_id, {"bid"})


def pick_winner(bids):
    """PROTOCOL.md deterministic tie-break."""
    return min(bids, key=lambda b: (-float(b["confidence"]),
                                   float(b["eta_ms"]), b["bidder_id"]))


def post_assign(task_id, winner):
    spec = {"task_id": task_id, "winner": winner["bidder_id"],
            "winning_confidence": winner["confidence"],
            "posted_ts": time.time()}
    signpost.post(CHANNEL, AUCTIONEER_ID, "assign", spec, task_id=task_id,
                  title="assign-%s" % task_id, status="bid-market")
    return spec


def await_result(task_id):
    for _ in _inotify_drain(RESULT_TIMEOUT_S):
        got = _scan(task_id, {"result"})
        if got:
            return got[0]
    return None


def run_market(run_dir, batch_id):
    """Post the batch through the real marketplace. Returns the ledger."""
    batch_in = os.path.join(run_dir, "in")
    os.makedirs(batch_in, exist_ok=True)
    _chan_dir.mkdir(parents=True, exist_ok=True)
    ledger = {}
    for t in task_defs.TASKS:
        task_id = "%s-%s" % (batch_id, t["id"])
        in_dir = task_defs.materialize(t, batch_in)
        # move materialized dir to the batch-prefixed name bidders will use
        want = os.path.join(batch_in, task_id)
        have = os.path.join(batch_in, t["id"])
        if os.path.isdir(want):
            import shutil
            shutil.rmtree(want)
        os.rename(have, want)
        workdir = os.path.join(run_dir, "work", task_id)
        in_w = os.path.join(workdir, "in")
        out_dir = os.path.join(workdir, "out")
        os.makedirs(in_w, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)  # bidders don't create it;
        # without this every shell `> out/...` redirect fails (exit 1)
        for root, _, files in os.walk(want):
            for fn in files:
                s = os.path.join(root, fn)
                rel = os.path.relpath(s, want)
                d = os.path.join(in_w, os.path.dirname(rel))
                os.makedirs(d, exist_ok=True)
                try:
                    os.link(s, os.path.join(d, fn))
                except FileExistsError:
                    pass
        entry = {"bidder": None, "posted_ts": None, "assigned_ts": None,
                 "completed_ts": None, "status": "unassigned",
                 "out_dir": out_dir, "in_dir": want, "bids": []}
        ledger[task_id] = entry
        t0 = time.time()
        spec, _ = post_task(t, workdir, task_id)
        entry["posted_ts"] = spec["posted_ts"]
        bids = collect_bids(task_id)
        entry["bids"] = [
            {"bidder_id": b["bidder_id"], "confidence": b["confidence"],
             "eta_ms": b["eta_ms"], "cost_ms": b.get("cost_ms")} for b in bids]
        if not bids:
            entry["status"] = "unassigned"
            print("  [%s] NO BIDS" % task_id)
            continue
        winner = pick_winner(bids)
        post_assign(task_id, winner)
        entry["bidder"] = winner["bidder_id"]
        entry["assigned_ts"] = time.time()
        entry["n_bids"] = len(bids)
        entry["winning_confidence"] = winner["confidence"]
        res = await_result(task_id)
        entry["completed_ts"] = time.time()
        if res is None:
            entry["status"] = "timeout"
            print("  [%s] winner=%s bids=%d RESULT TIMEOUT" %
                  (task_id, winner["bidder_id"], len(bids)))
        else:
            entry["status"] = "ok" if res.get("success") else "failed"
            entry["duration_ms"] = res.get("duration_ms")
            entry["error"] = res.get("error")
            print("  [%s] winner=%s bids=%d conf=%.3f status=%s dur=%.0fms "
                  "wall=%.1fs" % (task_id, winner["bidder_id"], len(bids),
                                  float(winner["confidence"]), entry["status"],
                                  res.get("duration_ms") or 0,
                                  time.time() - t0))
    with open(os.path.join(run_dir, "ledger.json"), "w") as f:
        json.dump(ledger, f, indent=1)
    return ledger
