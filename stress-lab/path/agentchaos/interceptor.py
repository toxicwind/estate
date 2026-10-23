#!/usr/bin/env python3
"""AgentChaos-style boundary interceptor.

Injects fault classes (CRASH / OMISSION / VALUE) at the BOUNDARY of the
operation being tested, NOT by mutating core source. Fault injection is
gated by env/flags so the same code path runs clean (fault absent) or
traced (fault active). This is a test-companion interceptor, structure-only.

boundary_fault.py <probe> [--inject crash|omission|value] [--seed N]
"""
import os, sys, time, signal, struct, socket, json

def boundary_trace(probe="sock_stress", inject=None, seed=0):
    """Wrap a probe call; optionally inject a fault at the return boundary."""
    t0 = time.perf_counter()
    record = {"probe": probe, "inject": inject, "seed": seed, "fired": False}
    if inject == "crash":
        # inject a fault: emulate a downstream crash by raising a synthetic boundary error
        record["fired"] = True
        raise ChildProcessError(f"AGENTCHAOS crash-injected at {probe} boundary")
    if inject == "omission":
        # emulate omission: swallow the normal result -> returns None
        record["fired"] = True
        return record, None
    if inject == "value":
        # emulate silent value corruption at the boundary
        record["fired"] = True
        return record, {"corrupted": True, "delta": seed}
    record["lat_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return record, {"ok": True}

if __name__ == "__main__":
    probe = sys.argv[1] if len(sys.argv) > 1 else "sock_stress"
    inject = None
    seed = 0
    if "--inject" in sys.argv:
        inject = sys.argv[sys.argv.index("--inject") + 1]
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    try:
        rec, res = boundary_trace(probe, inject, seed)
        print(json.dumps({"trace": rec, "result": res}))
        sys.exit(0)
    except ChildProcessError as e:
        # a crash fault is captured as a trace event, not a wall (per AgentChaos semantics)
        print(json.dumps({"trace": {"probe": probe, "inject": inject, "fired": True, "error": str(e)}}))
        sys.exit(0)
