#!/usr/bin/env python3
"""
Hearth's eyes on yote: single-pass progress snapshot, JSON to stdout.

Covers: oracle-market loop, ledger growth, stuck tasks, bidder daemons,
core pitchfork daemons + health, bridge holder. Never changes anything.
Channel dir can be overridden with argv[1] (used by --selftest).
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

def _resolve_pf():
    """Resolve the pitchfork binary without a version-pinned path.

    Order: live supervisor's own exe (can never skew vs the supervisor
    pitchfork must talk to) -> mise `latest` symlink (tracks newest
    install) -> mise shim -> /usr/bin fallback. Survives mise upgrades
    (e.g. 2.25.0 -> 2.27.0) without edits. (ember, 2026-09-20)
    """
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            cmdline = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode()
        except OSError:
            continue
        if "pitchfork supervisor run" in cmdline:
            try:
                exe = os.readlink(proc / "exe")
            except OSError:
                continue
            if exe.endswith("/pitchfork") and Path(exe).is_file():
                return exe
    for cand in (
        "/home/toxic/.local/share/mise/installs/pitchfork/latest/pitchfork",
        "/home/toxic/.local/share/mise/shims/pitchfork",
        "/usr/bin/pitchfork",
    ):
        if Path(cand).is_file():
            return cand
    return "/home/toxic/.local/share/mise/installs/pitchfork/latest/pitchfork"


PF = _resolve_pf()
LEDGER = Path("/tmp/e2e-market/ledger.json")
PLOF = ["tau-1826-health", "super-ralph-e2e"]
DAEMONS = {
    "kimi-auto-shim": 25153,
    "beellama-fast": 25122,
    "whatsapp-mcp": 25146,
    "toolcall-llm": 25152,
}
STUCK_UNSEEN_S = 180      # task_post with no ledger trace older than this
STUCK_WEDGED_S = 1800     # task_open but no terminal event older than this

out = {"ts": time.time(), "errors": []}
channel = Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "--selftest" \
    else Path("/home/toxic/sovereign/hatch/agents/ember/squawk-root/bid-market")


def sh(cmd, timeout=15):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.stdout
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"sh {' '.join(cmd[:2])}: {type(e).__name__}")
        return ""


def pf_statuses():
    stats = {}
    for line in sh([PF, "list"]).splitlines():
        parts = line.split()
        if len(parts) >= 2 and "/" in parts[0]:
            stats[parts[0]] = parts[1]
    return stats


def parse_frontmatter(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def load_ledger(path=LEDGER):
    events = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return events


def health(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health",
                                    timeout=5) as r:
            return r.status
    except Exception as e:  # noqa: BLE001
        return f"ERR:{type(e).__name__}"


def snapshot(chan_dir, ledger_events):
    now = time.time()
    snap = {}
    pf = pf_statuses()

    # --- oracle-market loop ---
    ostat = pf.get("sovereign/oracle-market", "missing")
    oproc = bool(sh(["pgrep", "-f", "oracle_loop.py"]).strip())
    snap["oracle"] = {"pitchfork": ostat, "proc_alive": oproc}

    # --- ledger ---
    by_tid = {}
    for e in ledger_events:
        tid = e.get("task_id")
        if tid:
            by_tid.setdefault(tid, set()).add(e.get("event"))
    last_ts = max((e.get("ts", 0) for e in ledger_events), default=0)
    w30 = [e for e in ledger_events if now - e.get("ts", 0) < 1800]
    w1h = [e for e in ledger_events if now - e.get("ts", 0) < 3600]
    wins = {}
    for e in w30:
        if e.get("event") == "settled" and e.get("verified"):
            w = e.get("winner", "?")
            wins[w] = wins.get(w, 0) + 1
    plof = {}
    for tid in PLOF:
        evs = by_tid.get(tid, set())
        if "settled" in evs:
            plof[tid] = ("settled-verified" if any(
                e.get("event") == "settled" and e.get("verified")
                for e in ledger_events if e.get("task_id") == tid)
                else "settled-unverified")
        elif "task_open" in evs:
            plof[tid] = "open"
        elif "no_assign" in evs:
            plof[tid] = "no-assign"
        else:
            plof[tid] = "missing"
    snap["ledger"] = {
        "lines": len(ledger_events),
        "last_ts": last_ts,
        "last_age_s": round(now - last_ts, 1) if last_ts else None,
        "open_30m": sum(1 for e in w30 if e.get("event") == "task_open"),
        "settled_30m": sum(1 for e in w30 if e.get("event") == "settled"),
        "verified_30m": sum(1 for e in w30
                             if e.get("event") == "settled" and e.get("verified")),
        "no_assign_30m": sum(1 for e in w30 if e.get("event") == "no_assign"),
        "settled_1h": sum(1 for e in w1h if e.get("event") == "settled"),
        "wins_30m": wins,
        "proof_of_life": plof,
    }

    # --- stuck tasks ---
    stuck = []
    if chan_dir.is_dir():
        for name in sorted(os.listdir(chan_dir)):
            if not name.endswith(".md"):
                continue
            meta = parse_frontmatter(chan_dir / name)
            if meta.get("msg_type") != "task_post":
                continue
            tid = meta.get("task_id", "")
            if not tid:
                continue
            age = now - (chan_dir / name).stat().st_mtime
            evs = by_tid.get(tid, set())
            if "task_open" not in evs and age > STUCK_UNSEEN_S:
                stuck.append({"task_id": tid, "kind": "unseen",
                              "age_s": round(age), "file": name})
            elif "task_open" in evs and not (evs & {"settled", "no_assign"}) \
                    and age > STUCK_WEDGED_S:
                stuck.append({"task_id": tid, "kind": "wedged",
                              "age_s": round(age), "file": name})
    snap["stuck_tasks"] = stuck

    # --- bidders ---
    bidders = []
    for name, status in sorted(pf.items()):
        if not name.startswith("sovereign/bidder-"):
            continue
        short = name.split("/", 1)[1]
        act = Path(f"/tmp/{short}.activity")
        age = round(now - act.stat().st_mtime, 1) if act.exists() else None
        bidders.append({"name": name, "status": status,
                        "activity_age_s": age})
    snap["bidders"] = bidders

    # --- core daemons ---
    daemons = {}
    for name, port in DAEMONS.items():
        daemons[name] = {"pitchfork": pf.get(f"sovereign/{name}", "missing"),
                         "health": health(port)}
    # bridge daemon expected stopped-clean; holder alive is what matters
    daemons["awrawr-ws-exec"] = {
        "pitchfork": pf.get("sovereign/awrawr-ws-exec", "missing")}
    snap["daemons"] = daemons

    # --- bridge holder ---
    holder = {"listening": False, "pid": None, "alive": False,
              "cmd_ok": False}
    m = re.search(r"pid=(\d+)", sh(["ss", "-ltnp", "sport = :8379"]))
    if m:
        holder["listening"] = True
        pid = m.group(1)
        holder["pid"] = int(pid)
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes()
            holder["alive"] = True
            holder["cmd_ok"] = b"awrawr_ws_exec" in cmd
        except OSError:
            pass
    snap["bridge"] = holder
    return snap


def selftest():
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="hearth-test-"))
    now = time.time()
    # unseen stuck task: task_post file, no ledger trace, old
    f1 = tmp / "00001-tester-task-post-old.md"
    f1.write_text("---\nmsg_type: task_post\ntask_id: stuck-unseen-1\n"
                  "---\n{\"task_id\": \"stuck-unseen-1\"}")
    os.utime(f1, (now - 600, now - 600))
    # fresh task: not stuck
    f2 = tmp / "00002-tester-task-post-fresh.md"
    f2.write_text("---\nmsg_type: task_post\ntask_id: fresh-1\n"
                  "---\n{\"task_id\": \"fresh-1\"}")
    # wedged task: task_open in ledger, no terminal event, old file
    f3 = tmp / "00003-tester-task-post-wedged.md"
    f3.write_text("---\nmsg_type: task_post\ntask_id: wedged-1\n"
                  "---\n{\"task_id\": \"wedged-1\"}")
    os.utime(f3, (now - 4000, now - 4000))
    led = [{"event": "task_open", "task_id": "wedged-1", "ts": now - 4000},
           {"event": "task_open", "task_id": "fresh-1", "ts": now - 10}]
    snap = snapshot(tmp, led)
    kinds = sorted((s["task_id"], s["kind"]) for s in snap["stuck_tasks"])
    print(json.dumps({"selftest_stuck": kinds,
                      "selftest_ledger_lines": snap["ledger"]["lines"]}))
    assert kinds == [("stuck-unseen-1", "unseen"), ("wedged-1", "wedged")], \
        f"FAIL: {kinds}"
    print("SELFTEST PASS")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        out.update(snapshot(channel, load_ledger()))
        print(json.dumps(out))
