#!/usr/bin/env python3
"""Ember: autonomous backlog pump for oracle_loop.py (2026-09-21).

Adds:
  1. BACKLOG path constant (ORACLE_BACKLOG env-overridable).
  2. OracleLoop._pump_backlog(): pops the next queued task from the
     JSONL backlog and posts it as intake_request (the front door).
     Claims before posting (crash-safe, never double-launches).
  3. Call in _maybe_start_next_work() after the swarm plea (defensive).
  4. Call in run() at startup when the market is idle (defensive).

Idempotent: re-running applies nothing twice. Backs up the original.
"""
import re
import sys
import time
from pathlib import Path

LOOP = Path("/home/toxic/sovereign/agents/oracle-market/bin/oracle_loop.py")
BACKUP = LOOP.with_name(
    "oracle_loop.py.bak-ember-backlog-%s" % time.strftime("%Y%m%d"))

PUMP_METHOD = '''
    # ----- autonomous backlog pump (2026-09-21, ember) -------------------
    def _pump_backlog(self):
        """Autonomous task supply: when the market is idle and the swarm
        has proposed nothing, pop the next queued task from the backlog
        file and feed it through intake (the front door), so auctions
        launch without waiting on a human. The backlog is JSONL, one task
        per line: {"title","text","added_by","added_ts","status"}.
        Entries are claimed (status -> posted) BEFORE the channel post,
        so a crash can never double-launch a task; a claimed-but-unposted
        task stays visible in the file for manual re-queue. Returns the
        entry dict, or None when there is nothing to pump."""
        try:
            if not BACKLOG.exists():
                return None
            raw = BACKLOG.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            self.log("backlog_read_error", reason=str(e))
            return None
        entries = []
        for ln in raw:
            ln = ln.strip()
            if not ln:
                continue
            try:
                entries.append(json.loads(ln))
            except (json.JSONDecodeError, ValueError):
                continue
        idx = None
        for i, e in enumerate(entries):
            if (isinstance(e, dict) and e.get("status") == "queued"
                    and (e.get("text") or "").strip()):
                idx = i
                break
        if idx is None:
            return None
        # Claim BEFORE posting: crash-safe, never double-launches.
        entries[idx]["status"] = "posted"
        entries[idx]["posted_ts"] = time.time()
        try:
            tmp = BACKLOG.with_name(BACKLOG.name + ".tmp")
            tmp.write_text(
                "\\n".join(json.dumps(e) for e in entries) + "\\n",
                encoding="utf-8")
            os.replace(tmp, BACKLOG)
        except OSError as e:
            self.log("backlog_claim_error", reason=str(e))
            return None
        text = entries[idx]["text"]
        title = entries[idx].get("title") or "backlog-task"
        try:
            name = self.market.post(
                "intake_request",
                "intake-%s" % self._safe_frm(title),
                {"text": text},
                note=("oracle-market: autonomous backlog pump -- no swarm "
                      "proposal arrived; launching next queued task."),
                frm=FROM)
        except Exception as e:
            self.log("backlog_post_error", reason=str(e), title=title)
            return None
        self.log("backlog_pumped", title=title, file=name)
        self.fleet_note(
            "oracle-market: backlog -> intake: %s" % title[:120])
        return entries[idx]

'''

EDIT1_OLD = 'LOCKFILE = Path(os.environ.get("ORACLE_LOCK", str(AGENT_DIR / "oracle.lock")))\n'
EDIT1_NEW = (EDIT1_OLD +
             'BACKLOG = Path(os.environ.get("ORACLE_BACKLOG", str(WORK / "task-backlog.jsonl")))\n')

EDIT3_OLD = '''        self.log("next_work_request", prev_task=prev_tid)

    # ----- ingest -----'''
EDIT3_NEW = '''        self.log("next_work_request", prev_task=prev_tid)
        # Autonomous supply: if the swarm proposes nothing, the backlog
        # pump feeds the next queued task through intake. Defensive: a
        # pump failure must never break the settlement path.
        try:
            self._pump_backlog()
        except Exception as e:
            self.log("backlog_pump_error", reason=str(e))

    # ----- ingest -----'''

EDIT4_OLD = '''        self.reconstruct()
        self._arm_channel()
        self._arm_parent()
'''
EDIT4_NEW = '''        self.reconstruct()
        self._arm_channel()
        self._arm_parent()
        # Startup kick: if the market is idle after replay and the backlog
        # holds queued work, launch the first auction now -- no settlement
        # will ever re-trigger the pump for the current idle state.
        # Defensive: never break startup.
        try:
            if not any(a.state in ("OPEN", "ASSIGNED")
                       for a in self.auctions.values()):
                self._pump_backlog()
        except Exception as e:
            self.log("backlog_startup_pump_error", reason=str(e))
'''


def main():
    text = LOOP.read_text(encoding="utf-8")
    orig = text

    # Edit 1: BACKLOG constant
    if "ORACLE_BACKLOG" in text:
        print("edit1: BACKLOG constant already present, skipping")
    else:
        assert EDIT1_OLD in text, "edit1 anchor not found"
        text = text.replace(EDIT1_OLD, EDIT1_NEW, 1)
        print("edit1: BACKLOG constant added")

    # Edit 2: _pump_backlog method before _maybe_start_next_work
    if "def _pump_backlog" in text:
        print("edit2: _pump_backlog already present, skipping")
    else:
        anchor = "    def _maybe_start_next_work(self, prev_tid):"
        assert anchor in text, "edit2 anchor not found"
        text = text.replace(anchor, PUMP_METHOD + anchor, 1)
        print("edit2: _pump_backlog method added")

    # Edit 3: pump call in _maybe_start_next_work
    if "backlog_pump_error" in text:
        print("edit3: settlement pump call already present, skipping")
    else:
        assert EDIT3_OLD in text, "edit3 anchor not found"
        text = text.replace(EDIT3_OLD, EDIT3_NEW, 1)
        print("edit3: settlement pump call added")

    # Edit 4: startup pump in run()
    if "backlog_startup_pump_error" in text:
        print("edit4: startup pump already present, skipping")
    else:
        assert EDIT4_OLD in text, "edit4 anchor not found"
        text = text.replace(EDIT4_OLD, EDIT4_NEW, 1)
        print("edit4: startup pump added")

    if text == orig:
        print("no changes needed")
        return 0
    if not BACKUP.exists():
        BACKUP.write_text(orig, encoding="utf-8")
        print("backup written:", BACKUP)
    LOOP.write_text(text, encoding="utf-8")
    print("patched:", LOOP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
