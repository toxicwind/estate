#!/usr/bin/env python3
"""Candidate registry for code-racer.

strategies/registry.json:
    {"strategies": [
        {"name": "alpha",
         "cmd": ["python3", "/abs/path/solver.py", "{outdir}"],
         "env": {"KEY": "val"},     # optional extra env
         "timeout_s": 60}           # optional per-strategy solve cap
    ]}

Contract (frozen 2026-09-20, t1-impl-core):
 - cmd is an argv list. "{outdir}" (or "$outdir") in any element is replaced
   with a fresh, unique per-run directory; "{taskdir}" (or "$taskdir") is
   replaced with the task dir (contains task.md + tests/ + limits.yaml).
   SOLUTION_DIR and TASK_DIR env vars are set to the same dirs.
 - The strategy MUST write its solution to <outdir>/solution.py — a python
   module the acceptance tests import as `solution`. It may read the problem
   statement from <taskdir>/task.md.
 - Exit codes are advisory. VALIDITY = solution.py exists AND the task's
   acceptance tests pass against it. A broken solution never wins no matter
   how fast it finishes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Strategy:
    name: str
    cmd: list
    env: dict = field(default_factory=dict)
    timeout_s: float | None = None

    def expand(self, outdir: str, taskdir: str = "") -> list:
        return [
            str(a).replace("{outdir}", outdir).replace("$outdir", outdir)
                   .replace("{taskdir}", taskdir).replace("$taskdir", taskdir)
            for a in self.cmd
        ]


def load(path) -> list[Strategy]:
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8"))
    items = data.get("strategies", data) if isinstance(data, dict) else data
    out = []
    for s in items:
        if "name" not in s or "cmd" not in s:
            raise ValueError(f"strategy entry needs name+cmd: {s!r}")
        out.append(
            Strategy(
                name=s["name"],
                cmd=list(s["cmd"]),
                env=dict(s.get("env") or {}),
                timeout_s=s.get("timeout_s"),
            )
        )
    names = [s.name for s in out]
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate strategy names: {names}")
    return out


def select(all_strats: list[Strategy], spec: str) -> list[Strategy]:
    if spec.strip().lower() == "all":
        return list(all_strats)
    want = [w.strip() for w in spec.split(",") if w.strip()]
    by_name = {s.name: s for s in all_strats}
    missing = [w for w in want if w not in by_name]
    if missing:
        raise ValueError(f"unknown strategies: {missing} (have: {sorted(by_name)})")
    return [by_name[w] for w in want]
