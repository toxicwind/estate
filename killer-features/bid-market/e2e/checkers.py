"""Independent ground-truth checkers for the e2e task batch.

Each checker recomputes the expected result DIRECTLY from the fixture files
using pure-Python logic that is intentionally written differently from any
bidder solution (no shell-outs, no shared code with executor solutions).
A checker returns (passed: bool, detail: str).

check(task, in_dir, out_dir) -> (bool, str)
"""

import csv
import json
import math
import os
import random
import re
from collections import Counter


def _read(p):
    with open(p) as f:
        return f.read()


def _missing(out_dir, names):
    miss = [n for n in names if not os.path.isfile(os.path.join(out_dir, n))]
    return miss


# -- A: shell-text --------------------------------------------------------

def check_A1(task, in_dir, out_dir):
    miss = _missing(out_dir, ["top10.txt"])
    if miss:
        return False, "missing outputs: %s" % miss
    words = _read(os.path.join(in_dir, "words.txt")).split()
    top = Counter(words).most_common()
    top.sort(key=lambda kv: (-kv[1], kv[0]))
    expected = ["%d %s" % (c, w) for w, c in top[:10]]
    got = _read(os.path.join(out_dir, "top10.txt")).splitlines()
    if got == expected:
        return True, "top10 matches (%d distinct words)" % len(set(words))
    return False, "mismatch: got %r expected %r" % (got[:3], expected[:3])


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def check_A2(task, in_dir, out_dir):
    miss = _missing(out_dir, ["emails.txt"])
    if miss:
        return False, "missing outputs: %s" % miss
    log = _read(os.path.join(in_dir, "server.log"))
    expected = sorted(set(EMAIL_RE.findall(log)))
    got = _read(os.path.join(out_dir, "emails.txt")).splitlines()
    if got == expected:
        return True, "%d unique emails" % len(expected)
    return False, "mismatch: got %d lines, expected %d" % (len(got), len(expected))


def check_A3(task, in_dir, out_dir):
    miss = _missing(out_dir, ["stats.txt"])
    if miss:
        return False, "missing outputs: %s" % miss
    total, n = 0, 0
    with open(os.path.join(in_dir, "sales.csv")) as f:
        for row in csv.DictReader(f):
            total += int(row["amount"])
            n += 1
    expected = ["sum=%d" % total, "count=%d" % n, "avg=%.2f" % (total / n)]
    got = _read(os.path.join(out_dir, "stats.txt")).splitlines()
    if got == expected:
        return True, "sum=%d count=%d" % (total, n)
    return False, "mismatch: got %r expected %r" % (got, expected)


def check_A4(task, in_dir, out_dir):
    miss = _missing(out_dir, ["dups.txt"])
    if miss:
        return False, "missing outputs: %s" % miss
    lines = _read(os.path.join(in_dir, "events.txt")).splitlines()
    cnt = Counter(lines)
    dups = sorted(((c, l) for l, c in cnt.items() if c > 1),
                  key=lambda t: (-t[0], t[1]))
    expected = ["%d\t%s" % (c, l) for c, l in dups]
    got = _read(os.path.join(out_dir, "dups.txt")).splitlines()
    if got == expected:
        return True, "%d duplicated lines" % len(dups)
    return False, "mismatch: got %d lines, expected %d" % (len(got), len(expected))


# -- B: shell-file --------------------------------------------------------

def check_B1(task, in_dir, out_dir):
    miss = _missing(out_dir, ["data.tsv"])
    if miss:
        return False, "missing outputs: %s" % miss
    with open(os.path.join(in_dir, "data.csv")) as f:
        expected_rows = [tuple(r) for r in csv.reader(f)]
    got_rows = [tuple(l.rstrip("\n").split("\t")) for l in
                _read(os.path.join(out_dir, "data.tsv")).splitlines()]
    # semantic compare: any valid TSV with the right cells passes
    if got_rows == expected_rows:
        return True, "%d rows converted" % len(expected_rows)
    return False, "tsv content mismatch (%d vs %d rows)" % (len(got_rows),
                                                            len(expected_rows))


def check_B2(task, in_dir, out_dir):
    for name in ["a.txt", "b.txt", "c.txt"]:
        src = os.path.join(in_dir, "raw", name)
        dst = os.path.join(out_dir, name)
        if not os.path.isfile(dst):
            return False, "missing output: %s" % name
        with open(src, "rb") as f:
            raw = f.read()
        # independent normalization: CRLF->LF, strip trailing [ \t] per line
        text = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode()
        expected = "\n".join(ln.rstrip(" \t") for ln in text.split("\n"))
        if text.endswith("\n") and not expected.endswith("\n"):
            expected += "\n"
        with open(dst, "rb") as f:
            got = f.read().decode()
        if got != expected:
            return False, "%s: normalization mismatch" % name
    return True, "3 files normalized"


def check_B3(task, in_dir, out_dir):
    miss = _missing(out_dir, ["records.csv"])
    if miss:
        return False, "missing outputs: %s" % miss
    recs = [_json_loads(l) for l in
            _read(os.path.join(in_dir, "records.jsonl")).splitlines() if l.strip()]
    expected = [("id", "name", "score")] + \
        [(str(r["id"]), r["name"], str(r["score"])) for r in recs]
    try:
        with open(os.path.join(out_dir, "records.csv")) as f:
            got = [tuple(r) for r in csv.reader(f)]
    except Exception as e:
        return False, "records.csv unreadable: %s" % e
    # semantic compare: any valid CSV (quoted or not) with the right cells
    if got == expected:
        return True, "%d records" % len(recs)
    return False, "csv content mismatch (%d vs %d rows)" % (len(got),
                                                             len(expected))


def _json_loads(s):
    return json.loads(s)


def io_StringIO():
    import io
    return io.StringIO()


def check_B4(task, in_dir, out_dir):
    names = ["chunk_%02d.txt" % i for i in range(5)]
    miss = _missing(out_dir, names)
    if miss:
        return False, "missing outputs: %s" % miss
    original = _read(os.path.join(in_dir, "lines.txt")).splitlines()
    if len(original) != 1000:
        return False, "fixture changed: %d lines" % len(original)
    cat = []
    for n in names:
        chunk = _read(os.path.join(out_dir, n)).splitlines()
        if len(chunk) != 200:
            return False, "%s has %d lines, expected 200" % (n, len(chunk))
        cat.extend(chunk)
    if cat == original:
        return True, "5x200 chunks concatenate exactly"
    return False, "concatenated chunks differ from original"


# -- C: python-compute ----------------------------------------------------

def _sieve_sum(limit):
    sieve = bytearray(b"\x01") * limit
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(math.isqrt(limit)) + 1):
        if sieve[i]:
            sieve[i * i:limit:i] = b"\x00" * ((limit - 1 - i * i) // i + 1)
    return sum(i for i, v in enumerate(sieve) if v)


def check_C1(task, in_dir, out_dir):
    miss = _missing(out_dir, ["answer.txt"])
    if miss:
        return False, "missing outputs: %s" % miss
    expected = str(_sieve_sum(200000))
    got = _read(os.path.join(out_dir, "answer.txt")).strip()
    if got == expected:
        return True, "prime sum = %s" % expected
    return False, "got %r expected %r" % (got, expected)


def check_C2(task, in_dir, out_dir):
    miss = _missing(out_dir, ["C.json"])
    if miss:
        return False, "missing outputs: %s" % miss
    A = json.loads(_read(os.path.join(in_dir, "A.json")))
    B = json.loads(_read(os.path.join(in_dir, "B.json")))
    n = len(A)
    C = [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)]
         for i in range(n)]
    got = json.loads(_read(os.path.join(out_dir, "C.json")))
    if got == C:
        return True, "40x40 product exact"
    return False, "matrix product mismatch"


def check_C3(task, in_dir, out_dir):
    miss = _missing(out_dir, ["answer.txt"])
    if miss:
        return False, "missing outputs: %s" % miss
    a, b = 0, 1
    for _ in range(35):
        a, b = b, a + b
    expected = str(a)
    got = _read(os.path.join(out_dir, "answer.txt")).strip()
    if got == expected:
        return True, "fib(35) = %s" % expected
    return False, "got %r expected %r" % (got, expected)


def check_C4(task, in_dir, out_dir):
    miss = _missing(out_dir, ["pi.txt"])
    if miss:
        return False, "missing outputs: %s" % miss
    rng = random.Random(12345)
    n = 200000
    inside = sum(1 for _ in range(n)
                 if (lambda x, y: x * x + y * y <= 1)(rng.random(), rng.random()))
    expected = "%.6f" % (4 * inside / n)
    got = _read(os.path.join(out_dir, "pi.txt")).strip()
    if got == expected:
        return True, "pi = %s" % expected
    return False, "got %r expected %r" % (got, expected)


# -- D: python-data --------------------------------------------------------

def check_D1(task, in_dir, out_dir):
    miss = _missing(out_dir, ["totals.json"])
    if miss:
        return False, "missing outputs: %s" % miss
    totals = {}
    for line in _read(os.path.join(in_dir, "records.jsonl")).splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        totals[r["dept"]] = totals.get(r["dept"], 0) + r["amount"]
    expected = json.dumps(totals, sort_keys=True)
    got_raw = _read(os.path.join(out_dir, "totals.json"))
    try:
        got = json.dumps(json.loads(got_raw), sort_keys=True)
    except Exception as e:
        return False, "totals.json not valid JSON: %s" % e
    if got == expected:
        return True, "%d depts" % len(totals)
    return False, "totals mismatch"


def check_D2(task, in_dir, out_dir):
    miss = _missing(out_dir, ["ranked.csv"])
    if miss:
        return False, "missing outputs: %s" % miss
    with open(os.path.join(in_dir, "scores.csv")) as f:
        rows = list(csv.reader(f))
    header, data = rows[0], rows[1:]
    seen, uniq = set(), []
    for r in data:
        t = tuple(r)
        if t not in seen:
            seen.add(t)
            uniq.append(r)
    uniq.sort(key=lambda r: (-int(r[1]), r[0]))
    expected = [tuple(header)] + [tuple(r) for r in uniq]
    try:
        with open(os.path.join(out_dir, "ranked.csv")) as f:
            got = [tuple(r) for r in csv.reader(f)]
    except Exception as e:
        return False, "ranked.csv unreadable: %s" % e
    # semantic compare: any valid CSV with the right rows passes
    if got == expected:
        return True, "%d unique rows ranked" % len(uniq)
    return False, "ranked.csv mismatch (%d vs %d rows)" % (len(got),
                                                            len(expected))


def check_D3(task, in_dir, out_dir):
    miss = _missing(out_dir, ["ma.txt"])
    if miss:
        return False, "missing outputs: %s" % miss
    xs = [float(l) for l in _read(os.path.join(in_dir, "series.txt")).splitlines()]
    expected = ["%.6f" % (sum(xs[i:i + 5]) / 5) for i in range(len(xs) - 4)]
    got = _read(os.path.join(out_dir, "ma.txt")).splitlines()
    if got == expected:
        return True, "%d moving averages" % len(expected)
    return False, "ma mismatch: got %d lines, expected %d" % (len(got), len(expected))


def check_D4(task, in_dir, out_dir):
    miss = _missing(out_dir, ["hist.json"])
    if miss:
        return False, "missing outputs: %s" % miss
    bins = {("%d-%d" % (lo, lo + 10)): 0 for lo in range(0, 100, 10)}
    with open(os.path.join(in_dir, "values.csv")) as f:
        for row in csv.DictReader(f):
            v = float(row["value"])
            lo = min(int(v // 10) * 10, 90)
            bins["%d-%d" % (lo, lo + 10)] += 1
    expected = json.dumps(bins, sort_keys=True)
    got_raw = _read(os.path.join(out_dir, "hist.json"))
    try:
        got = json.dumps(json.loads(got_raw), sort_keys=True)
    except Exception as e:
        return False, "hist.json not valid JSON: %s" % e
    if got == expected:
        return True, "bins sum=%d" % sum(bins.values())
    return False, "histogram mismatch"


CHECKERS = {t: fn for t, fn in [
    ("A1", check_A1), ("A2", check_A2), ("A3", check_A3), ("A4", check_A4),
    ("B1", check_B1), ("B2", check_B2), ("B3", check_B3), ("B4", check_B4),
    ("C1", check_C1), ("C2", check_C2), ("C3", check_C3), ("C4", check_C4),
    ("D1", check_D1), ("D2", check_D2), ("D3", check_D3), ("D4", check_D4),
]}


def check(task, in_dir, out_dir):
    fn = CHECKERS[task["id"]]
    return fn(task, in_dir, out_dir)
