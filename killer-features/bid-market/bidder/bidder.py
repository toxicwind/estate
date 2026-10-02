#!/usr/bin/env python3
"""Bidder daemon for the squawk bid-market (market/v1 wire).

Watches the `market` channel with inotify (event-driven, no polling),
bids fast on TASK_POST, executes on ASSIGN, posts signed RESULTs.

Usage:
    python3 bidder/bidder.py --profile flash|mule|specialist [--instance N]
                             [--channel market] [--once]

Each instance gets its own identity: bidder-<profile>[-N], with its own
HMAC key. Run N concurrently:
    cd /home/toxic/sovereign/killer-features/bid-market
    for p in flash mule specialist; do
      nohup python3 bidder/bidder.py --profile $p > bidder/var/bidder-$p.log 2>&1 &
    done

Wire: market/v1 via market.py (YAML body behind the marker line, signed).
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))   # market.py
sys.path.insert(0, str(HERE))   # profiles, bid_logic, executor, reputation

import market as M  # noqa: E402
import bid_logic     # noqa: E402
import executor      # noqa: E402
import profiles      # noqa: E402
import reputation    # noqa: E402

WINDOW_MIN, WINDOW_MAX = 5.0, 30.0


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def ensure_channel(channel):
    d = M.CHAT_ROOT / channel
    if not d.is_dir():
        chat_py = M.CHAT_CODE / "chat.py"
        subprocess.run([sys.executable, str(chat_py), "--root", str(M.CHAT_ROOT),
                        "init", channel], check=False, timeout=30,
                       capture_output=True)
    return d


class Bidder:
    def __init__(self, profile_name, instance, channel):
        self.profile = profiles.get(profile_name)
        self.channel = channel
        self.chan_dir = ensure_channel(channel)
        self.bidder_id = ("bidder-%s-%d" % (profile_name, instance)
                          if instance > 1 else "bidder-%s" % profile_name)
        self.state_dir = HERE / "var"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / ("%s-state.json" % self.bidder_id)
        self.state = self._load_state()
        M.ensure_key(self.bidder_id)
        log("bidder %s up | profile=%s caps=%s | channel=%s" % (
            self.bidder_id, profile_name, self.profile["caps"], channel))

    # ---- state ----
    def _load_state(self):
        try:
            st = json.loads(self.state_path.read_text())
        except (OSError, ValueError):
            st = {}
        st.setdefault("seen_seq", 0)
        st.setdefault("bids", {})   # "task_id#attempt" -> confidence
        st.setdefault("won", [])    # ["task_id#attempt"]
        return st

    def _save_state(self):
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state))
        os.replace(tmp, self.state_path)

    @staticmethod
    def _key(task_id, attempt):
        return "%s#%s" % (task_id, attempt)

    # ---- message handling ----
    def handle_file(self, path):
        m = M.parse_file(path)
        if m is None:
            return
        if m["seq"] <= self.state["seen_seq"]:
            return
        self.state["seen_seq"] = m["seq"]
        mt = m["msg_type"]
        if mt == "TASK_POST":
            self.on_task_post(m)
        elif mt == "ASSIGN":
            self.on_assign(m)
        self._save_state()

    def _task_from_post(self, m):
        w = m["wire"]
        return {
            "task_id": m["task_id"],
            "attempt": int(w.get("attempt", 1) or 1),
            "title": w.get("title", ""),
            "desc": m["human"],
            "budget": float(w.get("budget", 0) or 0),
            "deadline_s": float(w.get("deadline_s", 300) or 300),
            "window_s": w.get("window_s"),
            "posted_ts": w.get("posted_ts"),
            # optional execution extension (wire-compatible extras)
            "kind": w.get("kind", "shell"),
            "payload": w.get("payload"),
            "tags": w.get("tags"),
        }

    def on_task_post(self, m):
        task = self._task_from_post(m)
        key = self._key(task["task_id"], task["attempt"])
        if key in self.state["bids"]:
            return  # one bid per attempt (HFT: first wins)
        window = min(WINDOW_MAX, max(WINDOW_MIN,
                                     float(task["window_s"] or 10.0)))
        now = time.time()
        posted = float(task["posted_ts"] or 0)
        age_s = (now - posted) if posted else 0.0
        if posted and age_s > window:
            log("task %s: window closed (%.1fs > %.0fs), skip"
                % (task["task_id"], age_s, window))
            return
        rep = reputation.load(self.bidder_id)
        bid = bid_logic.compute_bid(self.profile, reputation.score(rep),
                                    float(rep.get("cal_mult", 1.0)),
                                    task, observed_latency_s=max(0.0, age_s))
        if not bid:
            log("task %s: no bid (profile mismatch)" % task["task_id"])
            return
        t0 = time.time()
        human = ("BID %(task_id)s from %(bidder)s: conf=%(confidence).3f "
                 "cost=%(cost).1f eta=%(eta_s).1fs" %
                 {"task_id": task["task_id"], "bidder": self.bidder_id, **bid})
        payload = {"task_id": task["task_id"], "attempt": task["attempt"],
                   "bidder": self.bidder_id,
                   "confidence": bid["confidence"], "cost": bid["cost"],
                   "eta_s": bid["eta_s"], "posted_ts": time.time(),
                   "capabilities": bid["capabilities"]}
        seq, _ = M.post_wire(self.channel, self.bidder_id,
                             "bid-%s" % task["task_id"], human, payload, "BID")
        latency_s = (time.time() - t0) + max(0.0, age_s)
        reputation.record_bid(self.bidder_id, latency_s)
        self.state["bids"][key] = bid["confidence"]
        self._save_state()
        log("task %s#%d: BID conf=%.3f cost=%.1f eta=%.1fs (post %.0fms) -> #%d"
            % (task["task_id"], task["attempt"], bid["confidence"],
               bid["cost"], bid["eta_s"], latency_s * 1000, seq))

    def on_assign(self, m):
        w = m["wire"]
        task_id = m["task_id"]
        attempt = int(w.get("attempt", 1) or 1)
        if w.get("winner") != self.bidder_id:
            return
        key = self._key(task_id, attempt)
        if key in self.state["won"]:
            return
        self.state["won"].append(key)
        self._save_state()
        reputation.record_assign(self.bidder_id)
        log("task %s#%d: ASSIGNED to me, executing" % (task_id, attempt))
        task = self._find_task(task_id, attempt)
        if not task or not task.get("payload"):
            # abstract v1 task (no executable spec): report honestly
            self.post_result(task_id, attempt, False, 0.0,
                             "no executable payload in TASK_POST (abstract task)",
                             summary="cannot execute: TASK_POST carries no kind/payload")
            return
        pred = self.state["bids"].get(key, 0.5)
        hb = lambda: self.post_heartbeat(task_id, attempt)  # noqa: E731
        success, output, dur_s, error = executor.run_task(task, heartbeat_cb=hb)
        summary = (output.strip().splitlines() or [""])[0][:200]
        if error:
            summary = (summary + " | " + error)[:200]
        self.post_result(task_id, attempt, success, dur_s, error,
                         summary=summary, output=output,
                         predicted=pred)

    def _find_task(self, task_id, attempt):
        best = None
        for path in sorted(self.chan_dir.glob("*.md")):
            m = M.parse_file(path)
            if m is None or m["msg_type"] != "TASK_POST":
                continue
            if m["task_id"] != task_id:
                continue
            t = self._task_from_post(m)
            if t["attempt"] == attempt:
                return t
            best = t
        return best

    def post_heartbeat(self, task_id, attempt):
        human = "HEARTBEAT %s#%d from %s (still working)" % (
            task_id, attempt, self.bidder_id)
        payload = {"task_id": task_id, "attempt": attempt,
                   "bidder": self.bidder_id, "ts": time.time()}
        M.post_wire(self.channel, self.bidder_id, "hb-%s" % task_id,
                    human, payload, "HEARTBEAT")

    def post_result(self, task_id, attempt, success, duration_s, error,
                    summary="", output="", predicted=0.5):
        reputation.record_result(self.bidder_id, predicted, success, duration_s)
        status = "done" if success else "failed"
        human = "RESULT %s#%d: %s by %s\n\n%s" % (
            task_id, attempt, status, self.bidder_id, summary)
        payload = {"task_id": task_id, "attempt": attempt,
                   "bidder": self.bidder_id, "status": status,
                   "quality": 1.0 if success else 0.0,
                   "summary": summary, "duration_s": round(duration_s, 2),
                   "posted_ts": time.time()}
        if error:
            payload["error"] = error[:500]
        seq, _ = M.post_wire(self.channel, self.bidder_id,
                             "result-%s" % task_id, human, payload, "RESULT")
        log("task %s#%d: RESULT %s dur=%.1fs -> #%d"
            % (task_id, attempt, status, duration_s, seq))

    # ---- watch loop ----
    def sweep(self):
        for path in sorted(self.chan_dir.glob("*.md")):
            if path.name.startswith("ledger"):
                continue
            self.handle_file(str(path))

    def watch(self):
        self.sweep()
        log("inotify watching %s" % self.chan_dir)
        p = subprocess.Popen(
            ["inotifywait", "-m", "-e", "close_write", "-e", "moved_to",
             "--format", "%f", str(self.chan_dir)],
            stdout=subprocess.PIPE, text=True)
        for line in p.stdout:
            fname = line.strip()
            if not fname.endswith(".md") or fname.startswith("ledger"):
                continue
            self.handle_file(str(self.chan_dir / fname))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True,
                    choices=sorted(profiles.PROFILES))
    ap.add_argument("--instance", type=int, default=1)
    ap.add_argument("--channel", default=M.CHANNEL)
    ap.add_argument("--once", action="store_true",
                    help="sweep only, then exit (for testing)")
    args = ap.parse_args()
    b = Bidder(args.profile, args.instance, args.channel)
    if args.once:
        b.sweep()
        log("once mode: done")
        return
    b.watch()


if __name__ == "__main__":
    main()
