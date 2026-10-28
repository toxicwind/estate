#!/usr/bin/env python3
"""One code-racer contestant.

Runs a registered strategy's command (fail-fast), then runs the task's REAL
acceptance tests against the produced solution.py. Prints RACE-PASS on stdout
and exits 0 ONLY when the tests pass; anything else -> RACE-FAIL, exit 1.
Emits a candidate_result NDJSON event on stderr for the winners ledger.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry import load as load_registry  # noqa: E402
from task_loader import load as load_task  # noqa: E402


def _run(cmd, timeout, cwd=None, env=None):
    t0 = time.perf_counter_ns()
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env
        )
        timed_out, rc = False, p.returncode
    except subprocess.TimeoutExpired:
        timed_out, rc = True, None
        p = None
    dt = round((time.perf_counter_ns() - t0) / 1e9, 6)
    if timed_out:
        return {"rc": None, "timed_out": True, "elapsed_s": dt,
                "stdout": "", "stderr": "timeout"}
    return {"rc": rc, "timed_out": False, "elapsed_s": dt,
            "stdout": (p.stdout or "")[-4000:], "stderr": (p.stderr or "")[-4000:]}


def parse_pytest(out: str):
    """-> (passed, failed); failed == -1 means pytest output unparseable."""
    m = re.search(r"(\d+) failed, (\d+) passed", out)
    if m:
        return int(m.group(2)), int(m.group(1))
    m = re.search(r"(\d+) passed", out)
    if m:
        return int(m.group(1)), 0
    m = re.search(r"(\d+) failed", out)
    if m:
        return 0, int(m.group(1))
    return 0, -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--solve-timeout", type=float, required=True)
    ap.add_argument("--test-timeout", type=float, required=True)
    a = ap.parse_args()

    def emit(o):
        sys.stderr.write(json.dumps(o) + "\n")
        sys.stderr.flush()

    t_all = time.perf_counter_ns()
    task = load_task(a.task)
    strats = {s.name: s for s in load_registry(a.registry)}
    if a.strategy not in strats:
        print("RACE-FAIL unknown-strategy")
        return 1
    st = strats[a.strategy]

    outdir = Path(tempfile.mkdtemp(prefix=f"cr-{a.strategy}-"))
    env = dict(os.environ)
    env.update(st.env)
    env["SOLUTION_DIR"] = str(outdir)
    env["TASK_DIR"] = str(task.dir)
    env["TASK_MD"] = str(task.dir / "task.md")
    solve_cap = st.timeout_s or a.solve_timeout
    solve = _run(st.expand(str(outdir), str(task.dir)), solve_cap, env=env)
    sol = outdir / "solution.py"
    has_solution = sol.exists() and sol.stat().st_size > 0

    passed, failed = 0, -1
    test = {"rc": None, "timed_out": False, "elapsed_s": 0.0}
    if has_solution:
        bed = Path(tempfile.mkdtemp(prefix=f"cr-test-{a.strategy}-"))
        try:
            shutil.copy(sol, bed / "solution.py")
            for f in task.tests_dir.iterdir():
                if f.is_file():
                    shutil.copy(f, bed / f.name)
            test = _run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short",
                 "-p", "no:cacheprovider"],
                a.test_timeout,
                cwd=str(bed),
            )
            passed, failed = parse_pytest(test["stdout"] + test["stderr"])
        finally:
            shutil.rmtree(bed, ignore_errors=True)

    valid = (
        has_solution
        and not test["timed_out"]
        and test["rc"] == 0
        and failed == 0
        and passed > 0
    )
    total_s = round((time.perf_counter_ns() - t_all) / 1e9, 6)
    emit({
        "event": "candidate_result",
        "name": a.strategy,
        "solve": {"rc": solve["rc"], "timed_out": solve["timed_out"],
                  "elapsed_s": solve["elapsed_s"]},
        "tests": {"passed": passed, "failed": failed, "rc": test["rc"],
                  "timed_out": test["timed_out"], "elapsed_s": test["elapsed_s"]},
        "valid": valid,
        "total_s": total_s,
    })
    shutil.rmtree(outdir, ignore_errors=True)
    if valid:
        print(f"RACE-PASS {a.strategy} solve={solve['elapsed_s']}s "
              f"tests={test['elapsed_s']}s passed={passed}")
        return 0
    if not has_solution:
        reason = "no-solution"
    elif test["timed_out"]:
        reason = "test-timeout"
    else:
        reason = f"tests-failed passed={passed} failed={failed}"
    print(f"RACE-FAIL {a.strategy} {reason}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
