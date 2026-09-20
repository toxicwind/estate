#!/usr/bin/env python3
"""Task-spec loader for code-racer.

A task dir:
    <task>/
        task.md        # problem statement (human/agent readable)
        tests/         # real pytest acceptance tests; `import solution` must work
        limits.yaml    # solve_timeout_s, test_timeout_s, workers (all optional)

returns a Task: name, dir, statement, tests_dir, solve_timeout_s,
test_timeout_s, workers.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULTS = {"solve_timeout_s": 120.0, "test_timeout_s": 60.0, "workers": 8}


def _parse_simple_yaml(text: str) -> dict:
    """Top-level `key: value` only — no PyYAML dependency."""
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        else:
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
        out[k] = v
    return out


@dataclass
class Task:
    name: str
    dir: Path
    statement: str
    tests_dir: Path
    solve_timeout_s: float = 120.0
    test_timeout_s: float = 60.0
    workers: int = 8


def load(task_dir) -> Task:
    d = Path(task_dir).expanduser().resolve()
    if not d.is_dir():
        raise FileNotFoundError(f"task dir not found: {d}")
    tests = d / "tests"
    if not tests.is_dir():
        raise FileNotFoundError(f"task {d} has no tests/ dir")
    test_files = list(tests.glob("test_*.py")) + list(tests.glob("*_test.py"))
    if not test_files:
        raise ValueError(f"task {d}: tests/ has no test files")
    lim = dict(DEFAULTS)
    lf = d / "limits.yaml"
    if lf.exists():
        lim.update(_parse_simple_yaml(lf.read_text(encoding="utf-8")))
    stmt = (d / "task.md").read_text(encoding="utf-8") if (d / "task.md").exists() else ""
    return Task(
        name=d.name,
        dir=d,
        statement=stmt,
        tests_dir=tests,
        solve_timeout_s=float(lim["solve_timeout_s"]),
        test_timeout_s=float(lim["test_timeout_s"]),
        workers=int(lim["workers"]),
    )
