#!/usr/bin/env python3
"""Unit tests for watchdog_lib, progress-watchdog (hatch side), and the
yote-side snapshot producer.

Covers:
  - ConditionRegistry: new fires, same suppresses, changed re-fires,
    clears on resolution, legacy migration silent adoption
  - domain-sweeps: yote/hatch keys never clear each other's conditions
  - atomic writes: no torn JSON, no stray temp files
  - run ledger: start/complete markers, lost-run detection
  - pause verification on a disposable child (SIGSTOP -> frozen T state)
  - pulse: never "all green" while conditions are active or stale
  - re-announce cap: max 3 re-posts per stuck task
  - per-request intake backlog: a later unrelated triage decision must
    not mask a stale intake_request; each decision consumed once
"""
import hashlib
import importlib.util
import importlib.machinery
import json
import os
import signal
import sys
import tempfile
import time
from pathlib import Path

TESTDIR = Path(__file__).resolve().parent
BIN = Path.home() / "workspace" / "bin"
sys.path.insert(0, str(BIN))
import watchdog_lib as wl  # noqa: E402

importlib.util  # noqa: E402  (kept for parity with loader helper below)


def _load_noext(name, path):
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


# progress-watchdog (hatch side) is import-safe: constants + mkdir only.
# Point at the staged canonical copy under test.
_pw = _load_noext("hatch_progress_watchdog",
                  str(TESTDIR / "canonical-hatch-pw"))

# snapshot producer (yote side) is import-safe too.
_sp = _load_noext("yote_snapshot", str(TESTDIR / "canonical-snapshot.py"))

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS {name}")
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"FAIL {name} {detail}")


# --------------------------------------------------------------------------
# ConditionRegistry
# --------------------------------------------------------------------------
def t_condition_registry():
    d = {}
    reg = wl.ConditionRegistry(d)
    now = time.time()

    # new condition fires
    r = reg.note("daemon:x", "dead", now)
    check("cond-new-fires", r == "fire", f"r={r}")

    # same condition suppresses
    r = reg.note("daemon:x", "dead", now)
    check("cond-same-suppresses", r == "suppress")

    # changed signature re-fires
    r = reg.note("daemon:x", "back", now)
    check("cond-changed-refires", r == "fire", f"r={r}")

    # change counts
    check("cond-change-counts", reg.count("daemon:x") == 2,
          f"d={reg.d['daemon:x']}")

    # active() lists keys
    check("cond-active-lists-key", "daemon:x" in reg.active())

    # sweep keeps observed, clears unobserved
    cleared = reg.sweep(["daemon:x"])
    check("cond-sweep-keeps-observed", cleared == [])
    cleared = reg.sweep([])
    check("cond-sweep-clears-unobserved", cleared == ["daemon:x"])
    check("cond-clear-removes", "daemon:x" not in reg.active())

    # legacy migration: first real signature adopted silently
    d2 = {"daemon:x": {"sig": "legacy", "first": 0, "last": 0, "n": 1}}
    reg2 = wl.ConditionRegistry(d2)
    r = reg2.note("daemon:x", "dead", now)
    check("cond-legacy-silent", r == "suppress", f"r={r}")
    check("cond-legacy-adopted", d2["daemon:x"]["sig"] == "dead")


def t_sweep_domain():
    # yote sweep never clears hatch:* keys and vice versa
    act = ["hatch:quiet", "daemon:x", "oracle:loop-dead"]
    check("sweep-yote-clears-yote-only",
          _pw.sweep_domain_keys(act, [], True) == ["daemon:x",
                                                  "oracle:loop-dead"])
    check("sweep-hatch-clears-hatch-only",
          _pw.sweep_domain_keys(act, [], False) == ["hatch:quiet"])
    check("sweep-all-observed-clears-nothing",
          _pw.sweep_domain_keys(act, act, True) == [])


# --------------------------------------------------------------------------
# atomic writes
# --------------------------------------------------------------------------
def t_atomic():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "state.json"
        wl.atomic_write_json(p, {"a": 1})
        check("atomic-valid-json", json.loads(p.read_text()) == {"a": 1})
        big = {f"k{i}": "v" * 100 for i in range(500)}
        wl.atomic_write_json(p, big)
        check("atomic-large-roundtrip", json.loads(p.read_text()) == big)
        stray = [x for x in Path(td).iterdir() if x.name != "state.json"]
        check("atomic-no-stray-temps", stray == [], f"stray={stray}")


# --------------------------------------------------------------------------
# run ledger
# --------------------------------------------------------------------------
def t_run_ledger():
    with tempfile.TemporaryDirectory() as td:
        lp = Path(td) / "runs.jsonl"
        rid = wl.ledger_run_start(lp, "progress-watchdog")
        # A run whose start is older than LOST_RUN_AFTER_S with no
        # completion is a lost run (SIGKILL/restart mid-run).
        lost = wl.ledger_find_lost(lp, now=time.time()
                                   + wl.LOST_RUN_AFTER_S + 5)
        check("ledger-lost-run-detected",
              any(r == rid for r in lost), f"lost={lost}")
        wl.ledger_run_complete(lp, rid, "progress-watchdog", "ok",
                               {"fired": []})
        lost2 = wl.ledger_find_lost(lp, now=time.time()
                                    + wl.LOST_RUN_AFTER_S + 5)
        check("ledger-completed-not-lost", rid not in lost2)
        lines = lp.read_text().strip().splitlines()
        recs = [json.loads(l) for l in lines]
        phases = [r["phase"] for r in recs
                  if r.get("run_id") == rid]
        check("ledger-start-complete-markers", phases == ["start", "complete"],
              f"phases={phases}")


# --------------------------------------------------------------------------
# pause verification on a disposable child (never touches fleet workers)
# --------------------------------------------------------------------------
def t_verify_pause():
    pid = os.fork()
    if pid == 0:
        # child: idle forever, only signals touch it
        while True:
            signal.pause()
    try:
        os.kill(pid, signal.SIGSTOP)
        # event-driven wait: WUNTRACED reaps the stop transition itself
        os.waitpid(pid, os.WUNTRACED)
        st = wl.proc_state(pid)
        check("proc-stopped-reads-T", st == "T", f"state={st}")
        # verify_pause() is system-wide over hatch-execd descendants;
        # here we only assert its contract shape, the T-state read
        # above is the disposable-child proof.
        info = wl.verify_pause()
        check("verify-pause-contract",
              set(info) == {"frozen", "checked", "why"},
              f"info={info}")
    finally:
        os.kill(pid, signal.SIGCONT)
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
    check("proc-reaped", wl.proc_state(pid) is None)


# --------------------------------------------------------------------------
# pulse verdict
# --------------------------------------------------------------------------
def t_pulse():
    pv = _pw.pulse_verdict
    check("pulse-green-when-clear", pv(True, []) == "all green this half hour")
    check("pulse-never-green-with-daemon-cond",
          pv(True, ["daemon:beellama-fast"]) != "all green this half hour")
    check("pulse-names-active-conds",
          "daemon:x" in pv(True, ["daemon:x"]))
    check("pulse-stale-not-green",
          "eyes closed" in pv(False, []))
    check("pulse-stale-beats-clear",
          pv(False, []) != "all green this half hour")
    check("pulse-oracle-cond-not-green",
          pv(True, ["oracle:loop-dead"]) != "all green this half hour")


# --------------------------------------------------------------------------
# re-announce cap
# --------------------------------------------------------------------------
def t_reannounce():
    reann = {"task-1": {"attempts": 3}}
    check("reann-first-allowed", _pw.reannounce_allowed({}, "t"))
    check("reann-2-allowed",
          _pw.reannounce_allowed({"t": {"attempts": 2}}, "t"))
    check("reann-3-spent", not _pw.reannounce_allowed(reann, "task-1"))
    check("reann-4-spent",
          not _pw.reannounce_allowed({"t": {"attempts": 4}}, "t"))
    check("reann-other-task-unaffected",
          _pw.reannounce_allowed(reann, "task-2"))


# --------------------------------------------------------------------------
# per-request intake backlog
# --------------------------------------------------------------------------
def _mk_ledger_decision(ts, frm, note=""):
    return {"event": "intake-decision", "ts": ts, "from": frm,
            "decision": "TASK", "note": note}


def _write_intake(d, name, frm, mtime):
    p = d / name
    p.write_text(f"---\nmsg_type: intake_request\nfrom: {frm}\n---\nbody\n")
    os.utime(p, (mtime, mtime))
    return p


def t_intake_backlog():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        now = 1_789_941_200.0
        # stale intake: filed 2000s ago, never triaged
        _write_intake(d, "100100-ember-intake-1789939200.md", "ember",
                      now - 2000)
        bl = _sp.intake_backlog(d, [], now)
        check("backlog-stale-intake-flagged",
              len(bl) == 1 and bl[0]["file"].endswith("1789939200.md"),
              f"bl={bl}")

        # its own decision within the window clears it
        dec = [_mk_ledger_decision(now - 1999, "ember")]
        bl = _sp.intake_backlog(d, dec, now)
        check("backlog-triaged-not-flagged", bl == [], f"bl={bl}")

        # an UNRELATED later decision must NOT clear the stale intake
        dec2 = [_mk_ledger_decision(now - 100, "lodestone")]
        bl = _sp.intake_backlog(d, dec2, now)
        check("backlog-unrelated-later-decision-no-mask",
              len(bl) == 1, f"bl={bl}")

        # non-intake files ignored
        (d / "notes.md").write_text("hello")
        bl = _sp.intake_backlog(d, [], now)
        check("backlog-non-intake-ignored", len(bl) == 1, f"bl={bl}")

        # REJECT counts as a triage decision
        dec3 = [{"event": "intake-decision", "ts": now - 1999,
                 "from": "ember", "decision": "REJECT"}]
        bl = _sp.intake_backlog(d, dec3, now)
        check("backlog-reject-counts-as-triaged", bl == [], f"bl={bl}")

        # each decision consumed once: two stale intakes from the same
        # sender need two decisions
        _write_intake(d, "100101-ember-intake-1789939300.md", "ember",
                      now - 1900)
        one = [_mk_ledger_decision(now - 1999, "ember")]
        bl = _sp.intake_backlog(d, one, now)
        check("backlog-decision-consumed-once", len(bl) == 1,
              f"bl={[b['file'] for b in bl]}")

        # fresh file (<120s) gets inotify grace, not flagged
        _write_intake(d, "100102-ember-intake-fresh.md", "ember", now - 30)
        bl = _sp.intake_backlog(d, [], now)
        files = [b["file"] for b in bl]
        check("backlog-fresh-file-grace",
              not any("fresh" in f for f in files), f"files={files}")


def main():
    t_condition_registry()
    t_sweep_domain()
    t_atomic()
    t_run_ledger()
    t_verify_pause()
    t_pulse()
    t_reannounce()
    t_intake_backlog()
    print(f"\n{PASS}/{PASS + FAIL} passed")
    if FAIL:
        print(f"FAILURES: {FAILURES}")
        sys.exit(1)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
