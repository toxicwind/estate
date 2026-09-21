#!/usr/bin/env python3
"""race_exec: bridge auto-racer with dispatch-gating.

Races the two hatch<->yote exec lanes (WS daemon via unix socket, legacy
HTTPS) and dispatches on the lane that proves itself first.

Two race modes:

  dispatch-race (default, safe for ANY command):
      Race only the lane READINESS probes (connect / session handshake).
      The winner dispatches; the loser NEVER dispatches. This preserves
      exec.py's no-double-dispatch contract: a command that may have
      executed remotely is never re-run on the other lane.

  full-race (--idempotent, caller asserts the command is side-effect free):
      Dispatch on both lanes concurrently; first valid correlated result
      wins; the loser thread is abandoned (capture mode accumulates
      locally, so abandoning is safe).

Dispatch-gating: a bounded semaphore (default 4) caps concurrent
dispatches fleet-wide in this process so a burst of callers never floods
the bridge; callers beyond the gate fail fast after --gate-ceiling.

Every race appends one JSONL line (fsync'd) to
~/.cache/shingle/bridge_race_ledger.jsonl.

HFT doctrine: race redundant paths, first-valid-wins, fail fast with short
ceilings, never retry-spin. (lane-goals, 2026-09-21)

Usage:
    race_exec.py "cmd" [workdir] [--timeout N] [--read-timeout S]
                 [--idempotent] [--gate N] [--gate-ceiling S] [--json]
"""

from __future__ import annotations

import concurrent.futures as cf
import importlib.util
import json
import os
import socket
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXEC_PY = os.path.join(HERE, "exec.py")
LEDGER = os.path.expanduser("~/.cache/shingle/bridge_race_ledger.jsonl")
SENDER = "race_exec"

DEFAULT_GATE_SIZE = 4
DEFAULT_GATE_CEILING = 30.0
PROBE_TIMEOUT = 5.0  # per-lane readiness probe ceiling (fail fast)


class RaceError(RuntimeError):
    pass


class GateTimeout(RaceError):
    pass


# One gate per process; sized at first use (CLI --gate can resize).
_GATE: threading.BoundedSemaphore | None = None
_GATE_SIZE = DEFAULT_GATE_SIZE


def gate(size: int = DEFAULT_GATE_SIZE) -> threading.BoundedSemaphore:
    global _GATE, _GATE_SIZE
    if _GATE is None or size != _GATE_SIZE:
        _GATE = threading.BoundedSemaphore(size)
        _GATE_SIZE = size
    return _GATE


def load_exec():
    """Import exec.py from this directory (no package needed)."""
    spec = importlib.util.spec_from_file_location("awrawr_exec", EXEC_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _append_ledger(entry: dict) -> None:
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        pass  # the race result must never die because the ledger did


def _probe_ws(m) -> tuple[bool, float, str]:
    """Readiness probe for the WS lane: down-flag, then a bare connect."""
    t0 = time.monotonic()
    try:
        if m._ws_known_down():
            return False, (time.monotonic() - t0) * 1000, "ws lane marked down"
    except Exception as e:  # noqa: BLE001 - a broken flag reader is "down"
        return False, (time.monotonic() - t0) * 1000, "ws flag read: %s" % e
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(PROBE_TIMEOUT)
        try:
            s.connect(m.WS_SOCK)
        finally:
            s.close()
        return True, (time.monotonic() - t0) * 1000, "ws socket connect ok"
    except OSError as e:
        return False, (time.monotonic() - t0) * 1000, "ws connect: %s" % e


def _probe_https(m, read_timeout: float) -> tuple[bool, float, str]:
    """Readiness probe for the HTTPS lane: degraded flag, then session."""
    t0 = time.monotonic()
    try:
        down, why = m._https_known_down()
        if down:
            return False, (time.monotonic() - t0) * 1000, "https degraded: %s" % why
    except Exception as e:  # noqa: BLE001
        return False, (time.monotonic() - t0) * 1000, "https flag read: %s" % e
    try:
        sid = m._load_session()
        if sid:
            return True, (time.monotonic() - t0) * 1000, "https session cached"
        m._initialize(read_timeout)
        return True, (time.monotonic() - t0) * 1000, "https handshake ok"
    except Exception as e:  # noqa: BLE001 - handshake failure is "down"
        return False, (time.monotonic() - t0) * 1000, "https init: %s" % e


def _dispatch_ws(m, cmd, workdir, timeout):
    return m._ws_exec(cmd, workdir, None, timeout, capture=True)


def _dispatch_https(m, cmd, workdir, read_timeout):
    return m._https_exec_capture(cmd, workdir, read_timeout)


def _race_probes(m, read_timeout: float) -> list[tuple[str, bool, float, str]]:
    """Run both readiness probes concurrently.

    Returns [(lane, ok, ms, note), ...] ordered by completion,
    first-valid first. Once a lane probes healthy, stragglers get one
    short grace window (0.5s) to land their notes for the ledger, then
    the executor is shut down WITHOUT waiting: probe threads are
    abandoned, never joined (a slow lane must not stall the race past
    its own ceiling).
    """
    ex = cf.ThreadPoolExecutor(max_workers=2, thread_name_prefix="race-probe")
    results: list[tuple[str, bool, float, str]] = []
    try:
        futs = {
            ex.submit(_probe_ws, m): "ws",
            ex.submit(_probe_https, m, read_timeout): "https",
        }
        pending = set(futs)
        won = False
        while pending:
            done, pending = cf.wait(pending,
                                    return_when=cf.FIRST_COMPLETED,
                                    timeout=PROBE_TIMEOUT + 2)
            for fut in done:
                lane = futs[fut]
                try:
                    ok, ms, note = fut.result()
                except Exception as e:  # noqa: BLE001 - probe crash is "down"
                    ok, ms, note = False, 0.0, "probe crashed: %s" % e
                results.append((lane, ok, ms, note))
                if ok:
                    won = True
            if won:
                # one grace window for the straggler's note, then abandon
                if pending:
                    done, pending = cf.wait(pending, timeout=0.5)
                    for fut in done:
                        lane = futs[fut]
                        try:
                            ok, ms, note = fut.result()
                        except Exception as e:  # noqa: BLE001
                            ok, ms, note = False, 0.0, "probe crashed: %s" % e
                        results.append((lane, ok, ms, note))
                return results
        return results
    finally:
        ex.shutdown(wait=False, cancel_futures=True)


def _enrich(result: dict, **kw) -> dict:
    result = dict(result or {})
    result.update(kw)
    return result


def race_exec(cmd: str, workdir: str = "/home/toxic", timeout=None,
              read_timeout: float | None = None, idempotent: bool = False,
              gate_size: int = DEFAULT_GATE_SIZE,
              gate_ceiling: float = DEFAULT_GATE_CEILING,
              race_ceiling: float | None = None,
              _exec=None) -> dict:
    """Race the bridge lanes and dispatch. See module docstring."""
    m = _exec or load_exec()
    if read_timeout is None:
        read_timeout = m._DEFAULT_READ_TIMEOUT
    t0 = time.monotonic()
    probes: dict[str, dict] = {}

    g = gate(gate_size)
    gw0 = time.monotonic()
    if not g.acquire(timeout=gate_ceiling):
        raise GateTimeout(
            "dispatch gate full (%d in flight); failing fast after %.1fs"
            % (gate_size, gate_ceiling))
    gate_wait_ms = (time.monotonic() - gw0) * 1000
    try:
        forced = os.environ.get("AWRAWR_TRANSPORT", "ws") == "https"
        mode = "dispatch-race"
        winner = None

        if forced:
            winner = "https"
            probes["https"] = {"ok": True, "ms": 0.0,
                               "note": "AWRAWR_TRANSPORT=https forced"}
        else:
            for lane, ok, ms, note in _race_probes(m, read_timeout):
                probes[lane] = {"ok": ok, "ms": ms, "note": note}
                if ok and winner is None:
                    winner = lane
                    break  # first-valid-wins: stop at the first healthy lane
            if winner is None:
                raise RaceError(
                    "no healthy lane: %s" % "; ".join(
                        "%s(%s)" % (ln, p["note"])
                        for ln, p in probes.items()))

        if idempotent and not forced:
            mode = "full-race"
            result, winner = _full_race(m, cmd, workdir, timeout, read_timeout,
                                        probes)
        else:
            result = _dispatch_lane(m, winner, cmd, workdir, timeout,
                                    read_timeout, probes, forced)
        total_ms = (time.monotonic() - t0) * 1000
        result = _enrich(result, race_winner=winner, race_mode=mode,
                         race_ms=total_ms, gate_wait_ms=gate_wait_ms,
                         lanes_probed={k: v["note"] for k, v in probes.items()})
        _append_ledger({
            "ts": time.time(), "cmd": cmd[:120], "workdir": workdir,
            "race_winner": winner, "race_mode": mode, "race_ms": total_ms,
            "gate_wait_ms": gate_wait_ms,
            "code": result.get("code"), "ok": result.get("ok", False),
            "lanes": {k: {"ok": v["ok"], "ms": round(v["ms"], 1)}
                      for k, v in probes.items()},
        })
        return result
    finally:
        g.release()


def _dispatch_lane(m, lane, cmd, workdir, timeout, read_timeout, probes,
                   forced=False):
    """Dispatch on exactly one lane. Honors exec.py's fallback contract.

    A WS exception AFTER dispatch (e.g. correlation failure) is reported
    as a failure WITHOUT re-dispatching on HTTPS — the command may have
    executed remotely, and re-running it risks double execution.
    """
    if lane == "ws":
        try:
            result = _dispatch_ws(m, cmd, workdir, timeout)
        except Exception as e:  # noqa: BLE001 - post-dispatch failure
            return _enrich({"code": 1, "stdout": "", "stderr": "",
                            "error": "ws dispatch failed: %s" % e,
                            "ok": False, "transport": "ws"},
                           fell_back=False, dispatch_error=str(e))
        if result is None:
            # WS pre-dispatch failure: daemon never saw the command, so the
            # HTTPS re-dispatch is safe (same contract as exec.py main).
            result = _dispatch_https(m, cmd, workdir, read_timeout)
            return _enrich(result, fell_back=True, fell_back_from="ws")
        return _enrich(result, fell_back=False)
    result = _dispatch_https(m, cmd, workdir, read_timeout)
    return _enrich(result, fell_back=False)


def _full_race(m, cmd, workdir, timeout, read_timeout, probes):
    """Both lanes dispatch; first VALID correlated result wins.

    Only for idempotent commands. A result is valid when it is a dict with
    no error. Correlation failures on a lane disqualify that lane, never
    the race. Returns (result_dict, winning_lane).
    """
    def run_ws():
        try:
            r = _dispatch_ws(m, cmd, workdir, timeout)
            if r is None:
                return None
            return ("ws", r)
        except Exception:  # noqa: BLE001 - lane failure disqualifies
            return None

    def run_https():
        try:
            return ("https", _dispatch_https(m, cmd, workdir, read_timeout))
        except Exception:  # noqa: BLE001
            return None

    ex = cf.ThreadPoolExecutor(max_workers=2, thread_name_prefix="race-full")
    try:
        futs = {ex.submit(run_ws), ex.submit(run_https)}
        done, pending = cf.wait(futs, return_when=cf.FIRST_COMPLETED,
                                timeout=read_timeout)
        for fut in done:
            got = fut.result()
            if got is None:
                continue
            lane, result = got
            if isinstance(result, dict) and not result.get("error"):
                return (_enrich(result, full_race_loser="abandoned",
                                fell_back=False), lane)
        # First finisher invalid: take whatever the other lane produced.
        for fut in pending:
            try:
                got = fut.result(timeout=read_timeout)
            except Exception:  # noqa: BLE001
                got = None
            if got is not None:
                lane, result = got
                if isinstance(result, dict):
                    return _enrich(result, fell_back=False), lane
        raise RaceError("full race: no valid result from either lane")
    finally:
        # Abandon the loser: capture-mode accumulates locally, so nothing
        # remote is left half-driven by us. Never join a slow lane.
        ex.shutdown(wait=False, cancel_futures=True)


def main() -> int:
    args = sys.argv[1:]
    idem = "--idempotent" in args
    if idem:
        args.remove("--idempotent")
    json_mode = "--json" in args
    if json_mode:
        args.remove("--json")
    timeout = None
    read_timeout = None
    gate_size = DEFAULT_GATE_SIZE
    gate_ceiling = DEFAULT_GATE_CEILING

    def take(flag, cast, default):
        if flag in args:
            i = args.index(flag)
            try:
                v = cast(args[i + 1])
            except (IndexError, ValueError):
                print("race_exec.py: %s needs a value" % flag,
                      file=sys.stderr)
                sys.exit(2)
            del args[i:i + 2]
            return v
        return default

    timeout = take("--timeout", int, None)
    read_timeout = take("--read-timeout", float, None)
    gate_size = take("--gate", int, DEFAULT_GATE_SIZE)
    gate_ceiling = take("--gate-ceiling", float, DEFAULT_GATE_CEILING)

    if not args:
        print(__doc__.strip().split("\n\n")[0], file=sys.stderr)
        print("usage: race_exec.py \"cmd\" [workdir] [--timeout N] "
              "[--read-timeout S] [--idempotent] [--gate N] "
              "[--gate-ceiling S] [--json]", file=sys.stderr)
        return 2
    cmd = args[0]
    workdir = args[1] if len(args) > 1 else "/home/toxic"
    try:
        result = race_exec(cmd, workdir, timeout=timeout,
                           read_timeout=read_timeout, idempotent=idem,
                           gate_size=gate_size, gate_ceiling=gate_ceiling)
    except RaceError as e:
        print("race_exec: %s" % e, file=sys.stderr)
        return 1
    if json_mode:
        out, err = result.get("stdout", ""), result.get("stderr", "")
        if len(out) + len(err) > 200_000:
            out, err = out[:200_000], err[: max(0, 200_000 - len(out))]
            result = dict(result)
            result["stdout"], result["stderr"] = out, err
            result["truncated"] = True
        print(json.dumps(result))
        return 0
    print(result.get("stdout", ""), end="")
    if result.get("stderr"):
        print(result["stderr"], end="", file=sys.stderr)
    print("[race: %s via %s in %.0fms]" % (result.get("race_mode"),
          result.get("race_winner"), result.get("race_ms", 0)),
          file=sys.stderr)
    return result.get("code", 1) or 0


if __name__ == "__main__":
    sys.exit(main())
