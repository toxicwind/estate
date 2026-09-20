#!/usr/bin/env python3
"""market auctioneer daemon -- market/v1.

Watches the public 'market' channel, runs short bidding windows, picks
winners by the frozen t2-architect score, posts signed ASSIGN, tracks
RESULTs, re-auctions fail-fast on timeout/no-bids, keeps a JSONL ledger and
per-bidder calibration.

EVENT-DRIVEN (no polling loops): a watchdog/inotify observer pushes new
market/*.md files into a queue; a deadline heap drives window-close and
result-timeout; the main loop blocks on the queue with a timeout of the
next deadline. Deadlines are conditions, not cadences.
"""
import heapq
import json
import os
import queue
import sys
import threading
import time
import traceback
from pathlib import Path

BASE = Path("/home/toxic/sovereign/killer-features/bid-market")
sys.path.insert(0, str(BASE))
import market as M

IDENTITY = "auctioneer"
STATE_FILE = BASE / "state.json"
MAX_ATTEMPTS = 4          # initial round + 3 re-auctions, then CANCEL
BUDGET_ESCALATION = 1.25  # budget *= 1.25^(attempt-1) on re-auction
GRACE_S = 30.0            # one-time result-deadline extension on fresh heartbeat
HB_FRESH_S = 20.0
WINDOW_MIN, WINDOW_MAX, WINDOW_DEFAULT = 5.0, 30.0, 10.0


def log(*a):
    print("[auctioneer]", *a, flush=True)


class Auctioneer:
    def __init__(self):
        self.q = queue.Queue()
        self.tasks = {}          # task_id -> task dict
        self.processed = set()   # seqs already handled (restart idempotent)
        self.deadlines = []      # heap of (ts, kind, task_id)
        self.cal = M.load_calib()
        self._load_state()
        M.ensure_key(IDENTITY)

    # ------------------------------------------------------------ persistence
    def _load_state(self):
        try:
            s = json.loads(STATE_FILE.read_text())
            self.tasks = s.get("tasks", {})
            self.processed = set(s.get("processed", []))
        except (OSError, ValueError):
            pass

    def _save_state(self):
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(
            {"tasks": self.tasks, "processed": sorted(self.processed)[-5000:]},
            sort_keys=True) + "\n")
        os.replace(tmp, STATE_FILE)

    # -------------------------------------------------------------- deadlines
    def _push_deadline(self, ts, kind, task_id):
        heapq.heappush(self.deadlines, (ts, kind, task_id))

    def _next_timeout(self):
        if not self.deadlines:
            return None
        return max(0.0, self.deadlines[0][0] - time.time())

    def _fire_due(self):
        now = time.time()
        while self.deadlines and self.deadlines[0][0] <= now:
            ts, kind, task_id = heapq.heappop(self.deadlines)
            try:
                if kind == "window":
                    self._close_window(task_id)
                elif kind == "result":
                    self._result_timeout(task_id)
            except Exception:
                log("deadline handler failed:", traceback.format_exc())

    # ------------------------------------------------------------------ fleet
    def _digest(self, text):
        try:
            cp = M._canonical_post()
            cp._post_message(M.CHAT_ROOT, "fleet", body=text, sender=IDENTITY,
                             title="market-digest", status="market")
        except Exception as e:
            log("fleet digest failed:", e)

    # ------------------------------------------------------------------ tasks
    def _task(self, task_id):
        return self.tasks.get(task_id)

    def _handle_task_post(self, m):
        w = m["wire"]
        task_id = m["task_id"]
        attempt = int(w.get("attempt", 1) or 1)
        t = self._task(task_id)
        if t and t["state"] == "OPEN" and attempt <= t["attempt"]:
            return  # duplicate / stale repost
        if t and t["state"] == "ASSIGNED" and attempt <= t["attempt"]:
            return
        window = min(WINDOW_MAX, max(WINDOW_MIN,
                                     float(w.get("window_s", WINDOW_DEFAULT) or
                                           WINDOW_DEFAULT)))
        now = time.time()
        self.tasks[task_id] = {
            "task_id": task_id,
            "title": w.get("title", m["title"]),
            "budget": float(w.get("budget", 0) or 0),
            "deadline_s": float(w.get("deadline_s", 300) or 300),
            "window_s": window,
            "attempt": attempt,
            "state": "OPEN",
            "bids": [],
            "invalid": [],
            "window_open_ts": now,
            "window_close_ts": now + window,
            "winner": None,
            "scores": {},
            "assign_ts": None,
            "result_deadline_ts": None,
            "last_hb": None,
            "grace_used": False,
        }
        self._push_deadline(now + window, "window", task_id)
        M.append_ledger({"event": "task_post", "task_id": task_id,
                         "attempt": attempt, "window_s": window,
                         "budget": self.tasks[task_id]["budget"],
                         "deadline_s": self.tasks[task_id]["deadline_s"],
                         "seq": m["seq"], "sender": m["sender"]})
        log(f"OPEN {task_id} attempt {attempt} window {window:.0f}s")

    def _verify_sig(self, m):
        """HMAC-verify; returns True or raises. TASK_POST skips (open)."""
        M.verify_file(m["path"])
        return True

    def _handle_bid(self, m):
        w = m["wire"]
        task_id = m["task_id"]
        t = self._task(task_id)
        recv = time.time()
        bid = {"bidder": w.get("bidder"), "confidence": w.get("confidence"),
               "cost": w.get("cost"), "eta_s": w.get("eta_s"),
               "seq": m["seq"], "recv_ts": recv,
               "latency_ms": max(0.0, (recv - M.ts_to_epoch(m["ts"]))) * 1000.0}
        reason = None
        try:
            self._verify_sig(m)
        except Exception as e:
            reason = f"bad-signature: {e}"
        if reason is None and m["sender"] != w.get("bidder"):
            reason = "sender/bidder mismatch"
        if reason is None and (not t or t["state"] != "OPEN"):
            reason = "no-open-task"
        if reason is None and int(w.get("attempt", 0) or 0) != t["attempt"]:
            reason = "stale-attempt"
        if reason is None and recv > t["window_close_ts"]:
            reason = "late"
        if reason is None and any(b["bidder"] == bid["bidder"] for b in t["bids"]):
            reason = "duplicate-bidder"
        if reason is None:
            try:
                c, co, e = float(w["confidence"]), float(w["cost"]), float(w["eta_s"])
                assert 0.0 <= c <= 1.0 and co >= 0 and e >= 0
                bid.update(confidence=c, cost=co, eta_s=e,
                           cal=M.get_cal(self.cal, bid["bidder"]))
            except (KeyError, TypeError, ValueError, AssertionError):
                reason = "bad-fields"
        if reason:
            bid["invalid_reason"] = reason
            if t:
                t["invalid"].append(bid)
            log(f"BID rejected {task_id}/{bid['bidder']}: {reason}")
        else:
            t["bids"].append(bid)
            log(f"BID {task_id} {bid['bidder']} conf={bid['confidence']} "
                f"cost={bid['cost']} eta={bid['eta_s']} "
                f"lat={bid['latency_ms']:.0f}ms")

    def _close_window(self, task_id):
        t = self._task(task_id)
        if not t or t["state"] != "OPEN":
            return
        decide_start = time.time()
        scored = []
        for b in t["bids"]:
            s = M.score_bid(b["confidence"], b["cal"], b["cost"],
                            t["budget"], b["eta_s"], t["deadline_s"])
            scored.append((b, s))
        scored.sort(key=lambda bs: (-bs[1], bs[0]["recv_ts"], bs[0]["seq"]))
        decision_ms = (time.time() - decide_start) * 1000.0
        if not scored:
            M.append_ledger({"event": "auction", "task_id": task_id,
                             "attempt": t["attempt"], "winner": None,
                             "reason": "no-bids", "n_bids": 0,
                             "n_invalid": len(t["invalid"]),
                             "invalid": t["invalid"]})
            log(f"no bids for {task_id} attempt {t['attempt']}")
            self._reauction_or_cancel(t, "no-bids")
            return
        winner, wscore = scored[0][0], scored[0][1]
        scores = {b["bidder"]: round(s, 6) for b, s in scored}
        now = time.time()
        human = (f"ASSIGN {task_id} -> {winner['bidder']} "
                 f"(score {wscore:.3f}, {len(scored)} bids, attempt {t['attempt']})")
        payload = {"task_id": task_id, "attempt": t["attempt"],
                   "winner": winner["bidder"], "scores": scores,
                   "n_bids": len(scored), "assign_ts": now,
                   "result_deadline_ts": now + t["deadline_s"]}
        # post BEFORE mutating state: a post failure must not strand the task
        seq, _ = M.post_wire(M.CHANNEL, IDENTITY,
                             f"assign-{task_id}", human, payload, "ASSIGN")
        t.update(state="ASSIGNED", winner=winner["bidder"], scores=scores,
                 assign_ts=now,
                 result_deadline_ts=now + t["deadline_s"])
        self._push_deadline(t["result_deadline_ts"], "result", task_id)
        M.append_ledger({
            "event": "auction", "task_id": task_id, "attempt": t["attempt"],
            "winner": winner["bidder"], "winning_score": round(wscore, 6),
            "scores": scores, "n_bids": len(scored),
            "n_invalid": len(t["invalid"]), "invalid": t["invalid"],
            "bids": [{k: b[k] for k in
                      ("bidder", "confidence", "cost", "eta_s", "cal",
                       "latency_ms", "seq")} for b, _ in scored],
            "decision_ms": round(decision_ms, 2),
            "window_s": t["window_s"]})
        M.append_ledger({"event": "assign", "task_id": task_id,
                         "attempt": t["attempt"], "winner": winner["bidder"],
                         "seq": seq})
        self._digest(f"market: ASSIGN {task_id} -> {winner['bidder']} "
                     f"(score {wscore:.3f}, {len(scored)} bids)")
        log(human)

    def _reauction_or_cancel(self, t, reason):
        task_id = t["task_id"]
        if t["attempt"] >= MAX_ATTEMPTS:
            t["state"] = "CANCELLED"
            human = f"CANCEL {task_id}: {reason} after {t['attempt']} rounds"
            payload = {"task_id": task_id, "attempt": t["attempt"],
                       "reason": "max-reattempts"}
            seq, _ = M.post_wire(M.CHANNEL, IDENTITY, f"cancel-{task_id}",
                                 human, payload, "CANCEL")
            M.append_ledger({"event": "cancel", "task_id": task_id,
                             "attempt": t["attempt"], "reason": reason,
                             "seq": seq})
            self._digest(f"market: CANCEL {task_id} ({reason}, "
                         f"{t['attempt']} rounds, escalating to fleet)")
            log(human)
            return
        attempt = t["attempt"] + 1
        budget = t["budget"] * BUDGET_ESCALATION
        window = t["window_s"]
        human = (f"TASK {task_id}: {t['title']}\n\n"
                 f"Re-auction attempt {attempt} (previous: {reason}). "
                 f"Budget escalated to {budget:.2f}.")
        payload = {"task_id": task_id, "title": t["title"], "attempt": attempt,
                   "budget": budget, "deadline_s": t["deadline_s"],
                   "window_s": window, "posted_ts": time.time(),
                   "reauction_reason": reason}
        seq, _ = M.post_wire(M.CHANNEL, IDENTITY, f"task-{task_id}-r{attempt}",
                             human, payload, "TASK_POST")
        M.append_ledger({"event": "reauction", "task_id": task_id,
                         "attempt": attempt, "reason": reason,
                         "budget": budget, "seq": seq})
        log(f"re-auction {task_id} attempt {attempt} ({reason})")
        # the new TASK_POST re-enters through the watcher and re-OPENS the task

    def _handle_result(self, m):
        w = m["wire"]
        task_id = m["task_id"]
        t = self._task(task_id)
        if not t or t["state"] != "ASSIGNED":
            log(f"RESULT for non-assigned task {task_id}: ignored")
            return
        try:
            self._verify_sig(m)
        except Exception as e:
            log(f"RESULT bad signature {task_id}: {e}")
            return
        if m["sender"] != w.get("bidder") or w.get("bidder") != t["winner"]:
            log(f"RESULT sender mismatch {task_id}: ignored")
            return
        if int(w.get("attempt", 0) or 0) != t["attempt"]:
            log(f"RESULT stale attempt {task_id}: ignored")
            return
        ok = (w.get("status") == "done")
        q = float(w.get("quality", 1.0 if ok else 0.0) or 0.0)
        new_cal = M.record_outcome(self.cal, t["winner"], ok, q)
        M.save_calib(self.cal)
        t["state"] = "DONE" if ok else "FAILED"
        M.append_ledger({"event": "result", "task_id": task_id,
                         "attempt": t["attempt"], "bidder": t["winner"],
                         "status": w.get("status"),
                         "quality": q, "new_cal": round(new_cal, 4),
                         "summary": str(w.get("summary", ""))[:500],
                         "seq": m["seq"]})
        self._digest(f"market: RESULT {task_id} {w.get('status')} "
                     f"by {t['winner']} (cal {new_cal:.3f})")
        log(f"RESULT {task_id} {w.get('status')} winner={t['winner']} "
            f"cal={new_cal:.3f}")
        if not ok:
            self._reauction_or_cancel(t, "task-failed")

    def _result_timeout(self, task_id):
        t = self._task(task_id)
        if not t or t["state"] != "ASSIGNED":
            return
        now = time.time()
        if (not t["grace_used"] and t["last_hb"]
                and now - t["last_hb"] < HB_FRESH_S):
            t["grace_used"] = True
            t["result_deadline_ts"] = now + GRACE_S
            self._push_deadline(t["result_deadline_ts"], "result", task_id)
            M.append_ledger({"event": "grace", "task_id": task_id,
                             "attempt": t["attempt"],
                             "extended_to": t["result_deadline_ts"]})
            log(f"grace +{GRACE_S:.0f}s for {task_id} (fresh heartbeat)")
            return
        new_cal = M.record_outcome(self.cal, t["winner"], False)
        M.save_calib(self.cal)
        t["state"] = "FAILED"
        M.append_ledger({"event": "result", "task_id": task_id,
                         "attempt": t["attempt"], "bidder": t["winner"],
                         "status": "timeout", "new_cal": round(new_cal, 4)})
        self._digest(f"market: RESULT {task_id} timeout by {t['winner']} "
                     f"(cal {new_cal:.3f})")
        log(f"TIMEOUT {task_id} winner={t['winner']} cal={new_cal:.3f}")
        self._reauction_or_cancel(t, "timeout")

    def _handle_heartbeat(self, m):
        w = m["wire"]
        t = self._task(m["task_id"])
        if not t or t["state"] != "ASSIGNED":
            return
        try:
            self._verify_sig(m)
        except Exception:
            return
        if m["sender"] == w.get("bidder") == t["winner"]:
            t["last_hb"] = time.time()
            log(f"heartbeat {m['task_id']} from {t['winner']}")

    def _handle_cancel(self, m):
        if m["sender"] != IDENTITY:
            log(f"CANCEL from non-auctioneer {m['sender']}: ignored")
            return
        try:
            self._verify_sig(m)
        except Exception as e:
            log(f"CANCEL bad signature: {e}")
            return
        t = self._task(m["task_id"])
        if t:
            t["state"] = "CANCELLED"

    # ---------------------------------------------------------------- routing
    def handle_file(self, path):
        m = M.parse_file(path)
        if not m or m["missing"]:
            return
        if m["seq"] in self.processed:
            return
        self.processed.add(m["seq"])
        # never process our own fleet digests; only market channel files arrive
        try:
            mt = m["msg_type"]
            if mt == "TASK_POST":
                self._handle_task_post(m)
            elif mt == "BID":
                self._handle_bid(m)
            elif mt == "RESULT":
                self._handle_result(m)
            elif mt == "HEARTBEAT":
                self._handle_heartbeat(m)
            elif mt == "CANCEL":
                self._handle_cancel(m)
            elif mt == "ASSIGN":
                pass  # ours (or foreign); not actionable
        except Exception:
            log("handler failed:", traceback.format_exc())
        self._save_state()

    def sweep(self):
        files = sorted(M.MARKET_DIR.glob("*.md"))
        for p in files:
            self.handle_file(p)
        # re-arm deadlines for in-flight tasks (restart recovery)
        now = time.time()
        for tid, t in self.tasks.items():
            if t["state"] == "OPEN":
                t["window_close_ts"] = now + t["window_s"]
                self._push_deadline(t["window_close_ts"], "window", tid)
                log(f"recovered OPEN {tid}: fresh {t['window_s']:.0f}s window")
            elif t["state"] == "ASSIGNED":
                rd = max(now + 5.0, t.get("result_deadline_ts") or now + 5.0)
                t["result_deadline_ts"] = rd
                self._push_deadline(rd, "result", tid)
                log(f"recovered ASSIGNED {tid}: result deadline rearmed")
        self._save_state()

    def run(self):
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        outer = self

        class H(FileSystemEventHandler):
            def on_created(self, e):
                if not e.is_directory and e.src_path.endswith(".md"):
                    outer.q.put(e.src_path)

            def on_moved(self, e):
                if not e.is_directory and e.dest_path.endswith(".md"):
                    outer.q.put(e.dest_path)

        obs = Observer()
        obs.schedule(H(), str(M.MARKET_DIR), recursive=False)
        obs.start()
        log(f"watching {M.MARKET_DIR} (inotify)")
        self.sweep()
        try:
            while True:
                try:
                    item = self.q.get(timeout=self._next_timeout())
                    self.handle_file(item)
                except queue.Empty:
                    pass
                self._fire_due()
        except KeyboardInterrupt:
            log("stopping")
        finally:
            obs.stop()
            obs.join()
            self._save_state()


if __name__ == "__main__":
    Auctioneer().run()
