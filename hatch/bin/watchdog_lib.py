#!/usr/bin/env python3
"""watchdog_lib — shared watchdog mechanics (hatch side).

Single home for the patterns every watchdog needs, so a fake-completion
bug gets fixed ONCE here instead of per-watchdog:

  - atomic state writes (write-temp + fsync + os.replace): a restart can
    never leave a half-written state file behind.
  - run ledger (atomic JSONL append of start+complete markers): a restart
    can neither lose nor duplicate a run's verdict. Gaps = lost runs,
    flagged by boot_selfcheck().
  - live pause observation (/proc T-state), never stale state files:
    verify_pause() counts actually-frozen processes; no watchdog may
    claim "paused" without it.
  - ConditionRegistry: seen-set + condition-hash dedup with
    escalate-on-change and cleared notifications. Replaces "re-fire the
    same alert every N minutes" with "fire on new/changed, remind on
    still-broken after REMIND_AFTER_S, announce when cleared".
  - boot_selfcheck(): validates watchdog state files at startup
    (schema, staleness, lost runs). Runs at the top of every watchdog
    tick — no separate @reboot hook needed, so it survives restarts
    and scheduler changes.

Canonical: hatch/bin/watchdog_lib.py in toxicwind/sovereign-projects.
Deployed: ~/workspace/bin/watchdog_lib.py (copy of canonical; keep in sync).
"""

import json
import os
import time
import uuid

# Still-broken reminder ceiling: re-fire an unchanged condition at most
# this often (escalation), instead of every dedup window.
REMIND_AFTER_S = 6 * 3600

# A run with no completion marker older than this is a lost run.
LOST_RUN_AFTER_S = 900


# --------------------------------------------------------------------------
# atomic persistence
# --------------------------------------------------------------------------

def atomic_write_text(path, text):
    """Write text to path atomically: temp file + fsync + os.replace.

    A crash/restart mid-write leaves either the old or the new file,
    never a truncated one.
    """
    path = str(path)
    tmp = f"{path}.tmp-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    with open(tmp, "w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_write_json(path, obj):
    atomic_write_text(path, json.dumps(obj, indent=1))


def append_ledger(path, record):
    """Append one JSONL record atomically.

    A single os.write() with O_APPEND is atomic for small records, so
    concurrent watchdog ticks can share one ledger without interleaving.
    Returns the record.
    """
    path = str(path)
    line = (json.dumps(record) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)
    return record


# --------------------------------------------------------------------------
# live process observation (never trust a state file for this)
# --------------------------------------------------------------------------

def proc_state(pid):
    """Single-char /proc state for pid, or None if gone."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            parts = f.read().rsplit(")", 1)[1].split()
        return parts[0]
    except (FileNotFoundError, IndexError, ValueError):
        return None


def ppid_map():
    m = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/stat") as f:
                parts = f.read().rsplit(")", 1)[1].split()
            m[int(pid)] = int(parts[1])
        except (FileNotFoundError, IndexError, ValueError):
            pass
    return m


def ancestors(pid, pm):
    seen = set()
    while pid in pm and pid not in seen:
        seen.add(pid)
        pid = pm[pid]
    return seen


def find_hatch_execd():
    """pid of the runtime's tool executor, or None."""
    import subprocess
    try:
        out = subprocess.run(
            ["pgrep", "-f", "hatch-execd --runtime-cell-leader"],
            capture_output=True, text=True, timeout=10)
        pids = [int(p) for p in out.stdout.split()]
        return pids[0] if pids else None
    except Exception:
        return None


def verify_pause():
    """Observe the LIVE pause state. Returns dict:

      {"frozen": N, "checked": M, "why": str}

    frozen = descendants of hatch-execd currently in T (SIGSTOP) state,
    excluding our own process chain. A watchdog may only claim "paused"
    when frozen > 0. why explains a zero result.
    """
    root = find_hatch_execd()
    if not root:
        return {"frozen": 0, "checked": 0,
                "why": "hatch-execd not found (pgrep missed)"}
    pm = ppid_map()
    me = os.getpid()
    my_chain = ancestors(me, pm) | {me}
    try:
        my_pgid = os.getpgid(me)
    except OSError:
        my_pgid = None
    frozen, checked = 0, 0
    for pid in pm:
        if pid in my_chain or pid == root:
            continue
        if my_pgid is not None:
            try:
                if os.getpgid(pid) == my_pgid:
                    continue
            except OSError:
                pass
        if root in ancestors(pid, pm):
            checked += 1
            if proc_state(pid) == "T":
                frozen += 1
    why = "ok" if frozen else (
        f"{checked} exacd descendants alive, none T-frozen")
    return {"frozen": frozen, "checked": checked, "why": why}


# --------------------------------------------------------------------------
# ConditionRegistry — dedup with escalate-on-change
# --------------------------------------------------------------------------

class ConditionRegistry:
    """Seen-set + condition-hash dedup for watchdog alerts.

    State shape (persisted inside the watchdog's state file under "conds"):
        {key: {"sig": str, "first": ts, "last": ts, "n": int}}

    note(key, sig, now) -> "fire" | "suppress" | "remind"
      fire:     new condition, or the signature CHANGED (new error detail,
                worsened, different shape) -> post the alert.
      suppress: identical condition already reported -> stay silent.
      remind:   identical condition, but REMIND_AFTER_S has passed since
                the last post -> one "still ongoing" reminder.

    sweep(observed_keys) -> [cleared keys]: conditions in the registry
      that were NOT observed this run have cleared. The caller posts one
      "cleared" note per key and drops them. Only call sweep() when the
      run actually observed the domain (good snapshot / readable
      watchlist) — never on the blind early-return path.
    """

    def __init__(self, conds_dict, remind_after_s=REMIND_AFTER_S):
        self.d = conds_dict
        self.remind_after_s = remind_after_s

    def note(self, key, sig, now):
        e = self.d.get(key)
        if e is None:
            self.d[key] = {"sig": sig, "first": now, "last": now, "n": 1}
            return "fire"
        if e.get("sig") == "legacy":
            # Migrated from the old time-dedup format: adopt the real
            # signature silently so the upgrade itself doesn't re-fire
            # every known condition at once.
            e["sig"] = sig
            if now - e.get("last", 0) >= self.remind_after_s:
                e["last"] = now
                e["n"] = e.get("n", 0) + 1
                return "remind"
            return "suppress"
        if e.get("sig") != sig:
            e["sig"] = sig
            e["first"] = now
            e["last"] = now
            e["n"] = e.get("n", 0) + 1
            return "fire"  # state CHANGED -> escalate
        if now - e.get("last", 0) >= self.remind_after_s:
            e["last"] = now
            e["n"] = e.get("n", 0) + 1
            return "remind"
        return "suppress"

    def active(self):
        """Keys with a currently-true condition (single source of truth
        for pulse verdicts — no separate issues list to drift)."""
        return sorted(self.d.keys())

    def count(self, key):
        return self.d.get(key, {}).get("n", 0)

    def since(self, key):
        return self.d.get(key, {}).get("first", 0)

    def sweep(self, observed_keys):
        """Return keys that were active but not observed -> cleared."""
        observed = set(observed_keys)
        cleared = [k for k in self.d if k not in observed]
        for k in cleared:
            del self.d[k]
        return sorted(cleared)


def migrate_legacy_alerts(state):
    """One-time migration: old time-dedup alerts {key: ts} -> conds.

    Preserves suppression across the upgrade so deploying the new code
    does not re-fire every known condition at once.
    """
    old = state.pop("alerts", None)
    if not old:
        return
    conds = state.setdefault("conds", {})
    now = time.time()
    for key, ts in old.items():
        if key not in conds:
            conds[key] = {"sig": "legacy", "first": ts, "last": ts, "n": 1}


# --------------------------------------------------------------------------
# run ledger — completion markers
# --------------------------------------------------------------------------

def ledger_run_start(ledger_path, name, extra=None):
    run_id = f"{int(time.time())}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    rec = {"run_id": run_id, "watchdog": name, "phase": "start",
           "ts": time.time()}
    if extra:
        rec.update(extra)
    append_ledger(ledger_path, rec)
    return run_id


def ledger_run_complete(ledger_path, run_id, name, verdict, extra=None):
    rec = {"run_id": run_id, "watchdog": name, "phase": "complete",
           "ts": time.time(), "verdict": verdict}
    if extra:
        rec.update(extra)
    append_ledger(ledger_path, rec)
    return rec


def ledger_find_lost(ledger_path, now=None):
    """Run_ids with a start but no complete older than LOST_RUN_AFTER_S.

    A SIGSTOP-frozen or SIGKILLed watchdog shows up here — the exact
    "run lost its output when its service restarted" case.
    """
    now = now or time.time()
    starts, completes = {}, set()
    try:
        with open(ledger_path) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if r.get("phase") == "start":
                    starts[r["run_id"]] = r.get("ts", 0)
                elif r.get("phase") == "complete":
                    completes.add(r.get("run_id"))
    except FileNotFoundError:
        return []
    return sorted(
        rid for rid, ts in starts.items()
        if rid not in completes and now - ts > LOST_RUN_AFTER_S)


# --------------------------------------------------------------------------
# boot self-check — validates watchdog state files at startup
# --------------------------------------------------------------------------

def boot_selfcheck(checks):
    """Run a list of check thunks; each returns (ok: bool, detail: str).

    Returns {"ok": bool, "findings": [str]}. Findings are non-empty only
    on problems. Watchdogs call this at the top of every tick (covers
    boot: the first tick after a restart) and alert on findings.
    """
    findings = []
    for name, thunk in checks:
        try:
            ok, detail = thunk()
        except Exception as e:  # noqa: BLE001
            ok, detail = False, f"{type(e).__name__}: {e}"
        if not ok:
            findings.append(f"{name}: {detail}")
    return {"ok": not findings, "findings": findings}


def check_json_state(path, required_keys):
    """Thunk factory: state file parses and has required keys.

    Corrupt files are quarantined to <path>.corrupt-<ts> (never deleted
    silently) so the watchdog can start clean.
    """
    def _check():
        p = str(path)
        try:
            with open(p) as f:
                d = json.load(f)
        except FileNotFoundError:
            return True, "absent (will be created)"
        except (json.JSONDecodeError, ValueError, OSError) as e:
            q = f"{p}.corrupt-{int(time.time())}"
            try:
                os.replace(p, q)
            except OSError:
                q = "(quarantine failed)"
            return False, f"corrupt ({type(e).__name__}) -> quarantined to {q}"
        missing = [k for k in required_keys if k not in d]
        if missing:
            return False, f"missing keys {missing}"
        return True, "ok"
    return _check


def check_pause_state_consistent(state_path):
    """Thunk: swarm-paused.json agrees with live /proc state."""
    def _check():
        try:
            with open(state_path) as f:
                st = json.load(f)
        except FileNotFoundError:
            return True, "no pause state (swarm not paused)"
        except (json.JSONDecodeError, ValueError, OSError) as e:
            return False, f"unreadable ({type(e).__name__})"
        pids = st.get("pids", [])
        if not pids and not st.get("yote_pids"):
            return False, "empty pid lists but file exists (stale)"
        alive = [p for p in pids if proc_state(p) is not None]
        frozen = [p for p in pids if proc_state(p) == "T"]
        if frozen:
            return True, f"{len(frozen)}/{len(pids)} pids T-frozen (pause live)"
        if alive:
            return False, (f"STALE: {len(alive)}/{len(pids)} pids alive but "
                           f"NONE T-frozen — pause not in effect")
        return False, (f"STALE: all {len(pids)} pids gone — pause state "
                       f"is a ghost (resume would be a no-op)")
    return _check
