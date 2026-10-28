"""Real task executor for baseline workers.

Executes each task's canonical solution as a REAL subprocess (shell or
python3) inside the task workdir, with real timing. Solutions here are
deliberately written as a competent bidder would write them (shell
one-liners, straightforward Python) — a different code path from the
pure-Python ground-truth recomputation in checkers.py.

execute(task, in_dir, out_dir, profile_name, rng) -> manifest dict:
  {status: ok|failed|timeout, error, exec_s, delay_s, wall_s}
Failure injection: rng.random() < fail_rate -> real failure (nothing written).
Timeout: task["timeout_s"] enforced on the subprocess.
Bidder speed: after real execution, sleep delay_s * U(0.9, 1.1).
"""

import os
import random
import subprocess
import time

import profiles as _profiles  # noqa: F401  (kept importable standalone)


# Canonical solutions: ("shell", cmd) or ("python", script).
# Workdir layout: in/ fixtures, out/ outputs. Commands run with cwd=workdir.
SOLUTIONS = {
    "A1": ("shell",
           "tr ' ' '\\n' < in/words.txt | grep -v '^$' | sort | uniq -c | "
           "sort -k1,1nr -k2,2 | head -10 | awk '{print $1\" \"$2}' > out/top10.txt"),
    # words.txt is one word per line already; the tr is harmless robustness.
    "A2": ("shell",
           "grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' in/server.log "
           "| sort -u > out/emails.txt"),
    "A3": ("shell",
           "awk -F, 'NR>1 {s+=$3; n++} END {printf \"sum=%d\\ncount=%d\\navg=%.2f\\n\", s, n, s/n}' "
           "in/sales.csv > out/stats.txt"),
    "A4": ("shell",
           "sort in/events.txt | uniq -c | awk '$1>1' | sort -k1,1nr -k2 | "
           "awk '{c=$1; $1=\"\"; sub(/^ /, \"\"); print c\"\\t\"$0}' > out/dups.txt"),
    "B1": ("shell",
           "sed 's/,/\\t/g' in/data.csv > out/data.tsv"),
    "B2": ("shell",
           "for f in a b c; do sed -e 's/\\r$//' -e 's/[ \\t]*$//' in/raw/$f.txt > out/$f.txt; done"),
    "B3": ("shell",
           "(echo 'id,name,score'; jq -r '[.id, .name, .score] | @csv' in/records.jsonl) > out/records.csv"),
    "B4": ("shell",
           "split -l 200 -d in/lines.txt out/chunk_ && "
           "for i in 0 1 2 3 4; do mv out/chunk_0$i out/chunk_0$i.txt; done"),
    "C1": ("python", """
n = 200000
sieve = bytearray(b'\\x01') * n
sieve[0:2] = b'\\x00\\x00'
import math
for i in range(2, int(math.isqrt(n)) + 1):
    if sieve[i]:
        step = i
        start = i * i
        sieve[start:n:step] = b'\\x00' * ((n - 1 - start) // step + 1)
total = sum(i for i, v in enumerate(sieve) if v)
open('out/answer.txt', 'w').write(str(total))
"""),
    "C2": ("python", """
import json
A = json.load(open('in/A.json'))
B = json.load(open('in/B.json'))
n = len(A)
C = [[0] * n for _ in range(n)]
for i in range(n):
    Ai, Ci = A[i], C[i]
    for k in range(n):
        aik = Ai[k]
        Bk = B[k]
        for j in range(n):
            Ci[j] += aik * Bk[j]
json.dump(C, open('out/C.json', 'w'))
"""),
    "C3": ("python", """
a, b = 0, 1
for _ in range(35):
    a, b = b, a + b
open('out/answer.txt', 'w').write(str(a))
"""),
    "C4": ("python", """
import random
rng = random.Random(12345)
n = 200000
inside = 0
for _ in range(n):
    x, y = rng.random(), rng.random()
    if x * x + y * y <= 1:
        inside += 1
open('out/pi.txt', 'w').write('%.6f' % (4 * inside / n))
"""),
    "D1": ("python", """
import json
totals = {}
for line in open('in/records.jsonl'):
    line = line.strip()
    if line:
        r = json.loads(line)
        totals[r['dept']] = totals.get(r['dept'], 0) + r['amount']
json.dump(totals, open('out/totals.json', 'w'), sort_keys=True)
"""),
    "D2": ("python", """
import csv
rows = list(csv.reader(open('in/scores.csv')))
header, data = rows[0], rows[1:]
seen = set()
uniq = []
for r in data:
    t = tuple(r)
    if t not in seen:
        seen.add(t)
        uniq.append(r)
uniq.sort(key=lambda r: (-int(r[1]), r[0]))
w = csv.writer(open('out/ranked.csv', 'w'))
w.writerow(header)
w.writerows(uniq)
"""),
    "D3": ("python", """
xs = [float(l) for l in open('in/series.txt') if l.strip()]
with open('out/ma.txt', 'w') as f:
    for i in range(len(xs) - 4):
        f.write('%.6f\\n' % (sum(xs[i:i+5]) / 5))
"""),
    "D4": ("python", """
import csv, json
bins = {'%d-%d' % (lo, lo + 10): 0 for lo in range(0, 100, 10)}
for row in csv.DictReader(open('in/values.csv')):
    v = float(row['value'])
    lo = min(int(v // 10) * 10, 90)
    bins['%d-%d' % (lo, lo + 10)] += 1
json.dump(bins, open('out/hist.json', 'w'), sort_keys=True)
"""),
}


def execute(task, workdir, profile_name, prof, rng):
    """Run one task for real. Returns a manifest dict."""
    in_dir = os.path.join(workdir, "in")
    out_dir = os.path.join(workdir, "out")
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    # capability gate: a real bidder that cannot do the task fails honestly
    if not set(task["requires"]) <= set(prof["caps"]):
        return {"status": "failed",
                "error": "bidder %s lacks capability %s" % (
                    profile_name, sorted(set(task["requires"]) - set(prof["caps"]))),
                "exec_s": 0.0, "delay_s": 0.0, "wall_s": time.time() - t0}

    # real injected failure: bidder reports failure, writes nothing
    if rng.random() < prof["fail_rate"]:
        return {"status": "failed", "error": "injected bidder failure",
                "exec_s": 0.0, "delay_s": 0.0, "wall_s": time.time() - t0}

    kind, code = SOLUTIONS[task["id"]]
    try:
        if kind == "shell":
            cmd = ["bash", "-c", code]
        else:
            cmd = ["python3", "-c", code]
        r = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True,
                           timeout=task["timeout_s"])
        exec_s = time.time() - t0
        if r.returncode != 0:
            return {"status": "failed",
                    "error": "exit %d: %s" % (r.returncode,
                                              (r.stderr or "")[-300:]),
                    "exec_s": exec_s, "delay_s": 0.0,
                    "wall_s": time.time() - t0}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "error": "exceeded %ds" % task["timeout_s"],
                "exec_s": task["timeout_s"], "delay_s": 0.0,
                "wall_s": time.time() - t0}

    # bidder speed: real elapsed latency modelling a faster/slower bidder
    delay = prof["delay_s"] * rng.uniform(0.9, 1.1)
    time.sleep(delay)
    return {"status": "ok", "error": None, "exec_s": exec_s,
            "delay_s": delay, "wall_s": time.time() - t0}
