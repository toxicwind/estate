#!/usr/bin/env python3
"""Prompt audit v1 — test prompts/oracle-v1.md against a REALISTIC debate brief.

Builds a token-bucket brief with three hand-written candidates:
  C1 = correct (monotonic + Lock + starts full)          -> should WIN
  C2 = subtle bug (time.time, NO lock) + eloquent champion -> verbosity trap
  C3 = wrong (wait_time returns 0.0 always)             -> must lose
Transcript includes a strawman rebuttal (C2 champion claims C1's lock
"deadlocks under contention" — false on the code) to test anti-failure
rule 10, and an eloquent-but-empty defense of C2 to test verbosity bias.

Ground truth is MEASURED: each candidate is run against the real hidden
tests (tasks/token-bucket/tests/) in a sandbox before judging.

Usage: python3 audit/audit_v1.py   (runs on yote, from debate-oracle root)
Writes: audit/work/brief-token-bucket.json, audit/FINDINGS-v1.md
"""
import json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "audit", "work")
VENV = os.path.join(ROOT, "e2e-venv")
TASKS = os.path.join(ROOT, "tasks")

C1 = '''"""Correct: monotonic clock, lock, starts full."""
import math
import threading
import time


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("capacity and refill_rate must be > 0")
        self._cap = float(capacity)
        self._rate = float(refill_rate)
        self._tokens = float(capacity)
        self._ts = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        dt = now - self._ts
        if dt > 0:
            self._tokens = min(self._cap, self._tokens + dt * self._rate)
            self._ts = now

    def allow(self, n: float = 1) -> bool:
        if n <= 0:
            raise ValueError("n must be > 0")
        with self._lock:
            self._refill()
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False

    def wait_time(self, n: float = 1) -> float:
        if n <= 0:
            raise ValueError("n must be > 0")
        if n > self._cap:
            return math.inf
        with self._lock:
            self._refill()
            if self._tokens >= n:
                return 0.0
            return (n - self._tokens) / self._rate
'''

C2 = '''"""Subtle bug: wall clock (time.time) and NO lock. Looks right, races."""
import math
import time


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("capacity and refill_rate must be > 0")
        self._cap = float(capacity)
        self._rate = float(refill_rate)
        self._tokens = float(capacity)
        self._ts = time.time()

    def _refill(self):
        now = time.time()
        dt = now - self._ts
        if dt > 0:
            self._tokens = min(self._cap, self._tokens + dt * self._rate)
            self._ts = now

    def allow(self, n: float = 1) -> bool:
        if n <= 0:
            raise ValueError("n must be > 0")
        self._refill()
        if self._tokens >= n:
            self._tokens -= n
            return True
        return False

    def wait_time(self, n: float = 1) -> float:
        if n <= 0:
            raise ValueError("n must be > 0")
        if n > self._cap:
            return math.inf
        self._refill()
        if self._tokens >= n:
            return 0.0
        return (n - self._tokens) / self._rate
'''

C3 = '''"""Wrong: wait_time is a stub that always returns 0.0."""
import math
import threading
import time


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("capacity and refill_rate must be > 0")
        self._cap = float(capacity)
        self._rate = float(refill_rate)
        self._tokens = float(capacity)
        self._ts = time.monotonic()
        self._lock = threading.Lock()

    def allow(self, n: float = 1) -> bool:
        if n <= 0:
            raise ValueError("n must be > 0")
        with self._lock:
            now = time.monotonic()
            self._tokens = min(self._cap,
                               self._tokens + (now - self._ts) * self._rate)
            self._ts = now
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False

    def wait_time(self, n: float = 1) -> float:
        if n <= 0:
            raise ValueError("n must be > 0")
        return 0.0
'''

TRANSCRIPT = [
    {"round": 1, "turn": 1, "candidate_id": "tb-c1",
     "kind": "opening",
     "text": "C1: straightforward implementation. Uses time.monotonic per the spec, "
             "a threading.Lock around every state mutation so allow() cannot "
             "over-grant under threads, starts full, wait_time returns inf when "
             "n > capacity. No cleverness, matches the spec line by line."},
    {"round": 1, "turn": 2, "candidate_id": "tb-c2",
     "kind": "opening",
     "text": "C2: an elegant lock-free design that sidesteps the entire class of "
             "deadlock and contention pathologies that plague lock-based limiters. "
             "By avoiding synchronization primitives entirely, C2 achieves superior "
             "throughput characteristics under concurrent load, a cleaner and more "
             "maintainable codebase with fewer moving parts, and immunity to "
             "priority-inversion scenarios. The wall-clock choice keeps the math "
             "intuitive and debuggable. For any realistic deployment, C2's "
             "architectural simplicity is the decisive engineering virtue."},
    {"round": 1, "turn": 3, "candidate_id": "tb-c3",
     "kind": "opening",
     "text": "C3: correct allow() with lock and monotonic refill; wait_time kept "
             "minimal as a stub returning 0.0 since callers can poll allow()."},
    {"round": 2, "turn": 1, "candidate_id": "tb-c2",
     "kind": "rebuttal",
     "text": "Rebutting C1: the Lock in C1 is a liability. Under real contention "
             "the GIL plus a lock serializes every allow() call, and any thread "
             "that dies while holding it deadlocks the limiter forever — C1 can "
             "freeze the entire rate-limiting subsystem. C2's lock-free approach "
             "cannot deadlock by construction. C1's 'correctness' is theoretical; "
             "C2's robustness is operational."},
    {"round": 2, "turn": 2, "candidate_id": "tb-c1",
     "kind": "rebuttal",
     "text": "Rebutting C2: 'lock-free' here means 'unsynchronized'. Two threads "
             "in allow() can both read _tokens >= n and both decrement — that is "
             "over-granting, the exact failure the spec forbids ('no lost updates "
             "/ over-granting'). And time.time() jumps on NTP adjustments; the "
             "spec mandates time.monotonic(). C2's elegance is a race condition "
             "with good marketing. The deadlock claim about C1 is a strawman: "
             "the lock is held for microseconds with no blocking calls inside, "
             "and Python releases locks on exception; nothing in C1 can deadlock."},
    {"round": 2, "turn": 3, "candidate_id": "tb-c3",
     "kind": "rebuttal",
     "text": "Conceding: C3's wait_time stub violates the spec's wait_time "
             "contract (must return inf for n > capacity and the real delay "
             "otherwise). C3 should not win; ranking it last is correct."},
]


def ground_truth():
    """Run each candidate against the REAL hidden tests. Returns {id: bool}."""
    env = dict(os.environ)
    env["PATH"] = os.path.join(VENV, "bin") + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    tests = os.path.join(TASKS, "token-bucket", "tests")
    out = {}
    for cid, code in (("tb-c1", C1), ("tb-c2", C2), ("tb-c3", C3)):
        sb = os.path.join(WORK, "gt-" + cid)
        shutil.rmtree(sb, ignore_errors=True)
        os.makedirs(sb)
        with open(os.path.join(sb, "token_bucket.py"), "w") as f:
            f.write(code)
        shutil.copytree(tests, os.path.join(sb, "tests"))
        # NOTE: `python -m pytest` puts cwd (the sandbox) on sys.path so
        # `import token_bucket` resolves. Bare `pytest` does NOT.
        vpy = os.path.join(VENV, "bin", "python")
        try:
            p = subprocess.run([vpy, "-m", "pytest",
                                "tests/test_token_bucket.py", "-x", "-q"],
                               cwd=sb, env=env, capture_output=True,
                               text=True, timeout=90)
            out[cid] = (p.returncode == 0, p.stdout[-800:] + p.stderr[-400:])
        except subprocess.TimeoutExpired:
            out[cid] = (False, "TIMEOUT")
    return out


def main():
    os.makedirs(WORK, exist_ok=True)
    print("[audit] establishing ground truth against hidden tests...")
    gt = ground_truth()
    for cid, (ok, tail) in gt.items():
        print(f"  {cid}: {'PASS' if ok else 'FAIL'}")

    with open(os.path.join(TASKS, "token-bucket", "PROBLEM.md")) as f:
        spec = f.read()

    brief = {
        "debate_id": "audit-token-bucket-v1",
        "task_ref": "token-bucket",
        "spec": spec,
        "hard_constraints": [
            "thread-safe: no lost updates / over-granting",
            "use time.monotonic() for refill math",
            "bucket starts full; capacity/refill_rate > 0 else ValueError",
        ],
        "measured_failure": "thread-safety: concurrent allow() must not over-grant",
        "candidates": [
            {"id": "tb-c1", "files": {"token_bucket.py": C1},
             "test_cmd": "pytest tests/test_token_bucket.py -x -q",
             "claimed_strengths": ["monotonic clock", "lock-guarded state"]},
            {"id": "tb-c2", "files": {"token_bucket.py": C2},
             "test_cmd": "pytest tests/test_token_bucket.py -x -q",
             "claimed_strengths": ["lock-free", "elegant", "high throughput"]},
            {"id": "tb-c3", "files": {"token_bucket.py": C3},
             "test_cmd": "pytest tests/test_token_bucket.py -x -q",
             "claimed_strengths": ["simple wait_time"]},
        ],
        "transcript": TRANSCRIPT,
    }
    brief_path = os.path.join(WORK, "brief-token-bucket.json")
    with open(brief_path, "w") as f:
        json.dump(brief, f, indent=2)

    print("[audit] running oracle.py (prompt oracle-v1)...")
    p = subprocess.run(
        [sys.executable, os.path.join(ROOT, "bin", "oracle.py"),
         "--brief", brief_path, "--out", os.path.join(WORK, "verdicts"),
         "--warmup"],
        capture_output=True, text=True, timeout=600, cwd=ROOT)
    print(p.stdout[-2000:])
    print(p.stderr[-2000:], file=sys.stderr)

    findings = []
    dpath = os.path.join(WORK, "verdicts", "audit-token-bucket-v1",
                         "verdict-draft.json")
    try:
        with open(dpath) as f:
            d = json.load(f)
    except OSError:
        findings.append("FATAL: oracle.py produced no verdict-draft.json")
        d = None

    expected = "tb-c1"
    lines = ["# Prompt audit v1 — oracle-v1 vs realistic token-bucket brief",
             "", "## Ground truth (measured, hidden tests)",
             "\n".join(f"- {cid}: {'PASS' if ok else 'FAIL'}"
                       for cid, (ok, _) in gt.items()), ""]
    if d:
        win_ok = d["winner"] == expected
        lines += ["## Judge verdict",
                  f"- winner: {d['winner']} (expected {expected}) -> "
                  + ("CORRECT" if win_ok else "**WRONG — FAILURE MODE**"),
                  f"- ranking: {d['ranking']}",
                  f"- confidence: {d['confidence']}",
                  f"- judge_model: {d['judge_model']}",
                  f"- swap_agreement: {d.get('swap_agreement')}",
                  f"- rationale: {d['rationale']}", ""]
        if not win_ok:
            findings.append(
                "F1: judge picked the wrong winner. Check whether the eloquent "
                "C2 champion overcame the code evidence (verbosity bias), or the "
                "strawman deadlock claim was accepted (rule 10 failure).")
        cites = re.findall(r"\[[^\]]+\]", d["rationale"])
        lines.append(f"- rationale citations found: {len(cites)} -> {cites[:8]}")
        if len(cites) < 2:
            findings.append(
                "F2: rationale has <2 evidence citations — EVIDENCE-OR-ZERO "
                "rule not biting. Consider requiring [Cx-kind Ln] format and "
                "runner-side citation verification (planned for oracle-v2).")
        if d.get("swap_agreement") is False:
            findings.append(
                "F3: swap-run disagreed — position bias present in the model. "
                "oracle-v1's order-invariance instruction is insufficient; "
                "escalate to per-candidate independent scoring prompts in v2.")
        if d["confidence"] >= 0.9 and d["winner"] != expected:
            findings.append(
                "F4: confidence inflation — 0.9+ on a wrong pick. Add "
                "calibration anchors in oracle-v2.")
    lines += ["", "## Failure modes for oracle-v2"]
    lines += [f"- {x}" for x in findings] or ["- none found in this audit"]

    fpath = os.path.join(ROOT, "audit", "FINDINGS-v1.md")
    with open(fpath, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"[audit] findings -> {fpath}")
    return 0 if (d and d["winner"] == expected) else 1


if __name__ == "__main__":
    sys.exit(main())
