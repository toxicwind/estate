"""E2E task batch for the squawk bid-marketplace (Team 2).

16 REAL small tasks in 4 categories x 4 tasks. Every task:
  - has deterministic fixtures (seeded generators -> in/<task>/)
  - is executed for REAL by bidder/worker processes (no mocks)
  - has an INDEPENDENT ground-truth checker in checkers.py that recomputes
    the expected result from the fixtures (never trusts stored answers)

Task dict fields:
  id, title, category, requires (set: {"shell"} and/or {"python"}),
  prompt (natural-language instructions, as the auctioneer would post),
  fixtures: {relpath: generator_fn}  (generator takes no args, returns str/bytes),
  outputs: [relpath under out/],
  timeout_s
"""

import csv
import io
import json
import random


# ---------------------------------------------------------------- fixtures

def _g_words():
    rng = random.Random(11)
    vocab = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf",
             "hotel", "india", "juliet", "kilo", "lima", "mike", "november",
             "oscar", "papa", "quebec", "romeo", "sierra", "tango"]
    weights = [20, 18, 16, 14, 12, 10, 9, 8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1]
    words = rng.choices(vocab, weights=weights, k=5000)
    return "\n".join(words) + "\n"


def _g_server_log():
    rng = random.Random(12)
    users = ["amy", "bob", "cara", "dan", "erin", "finn", "gina", "hal"]
    doms = ["example.com", "mail.org", "corp.net"]
    lines = []
    for i in range(300):
        r = rng.random()
        if r < 0.35:
            em = "%s%d@%s" % (rng.choice(users), rng.randrange(100), rng.choice(doms))
            lines.append("2026-09-20 00:%02d:%02d INFO login user=%s src=10.0.0.%d"
                         % (rng.randrange(60), rng.randrange(60), em, rng.randrange(250)))
        elif r < 0.45:
            em = "%s@%s" % (rng.choice(users), rng.choice(doms))
            lines.append("WARN  bounce recipient=<%s> reason=mailbox_full" % em)
        else:
            lines.append("2026-09-20 00:%02d:%02d DEBUG heartbeat worker=%d ok"
                         % (rng.randrange(60), rng.randrange(60), rng.randrange(8)))
    return "\n".join(lines) + "\n"


def _g_sales_csv():
    rng = random.Random(13)
    regions = ["north", "south", "east", "west"]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "region", "amount"])
    for i in range(400):
        w.writerow([i, rng.choice(regions), rng.randrange(1, 1000)])
    return out.getvalue()


def _g_events():
    rng = random.Random(14)
    kinds = ["boot", "shutdown", "login", "logout", "error", "timeout", "retry",
             "deploy", "rollback", "backup"]
    hosts = ["web-%d" % i for i in range(10)] + ["db-%d" % i for i in range(5)]
    pool = ["%s %s" % (rng.choice(kinds), rng.choice(hosts)) for _ in range(300)]
    return "\n".join(rng.choice(pool) for _ in range(1000)) + "\n"


def _g_simple_csv():
    rng = random.Random(15)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["sku", "name", "qty", "price"])
    names = ["widget", "gadget", "sprocket", "cog", "gear", "spring"]
    for i in range(200):
        w.writerow(["SKU%04d" % i, rng.choice(names), rng.randrange(1, 50),
                    "%.2f" % rng.uniform(1, 99)])
    return out.getvalue()


def _g_raw_a():
    return "hello world   \r\nsecond line\t \r\nthird\r\n"


def _g_raw_b():
    rng = random.Random(151)
    return "".join("row %d   \r\n" % i for i in range(50))


def _g_raw_c():
    return "  leading kept? no->strip only trailing   \nplain\n"


def _g_records_jsonl():
    rng = random.Random(16)
    names = ["amy", "bob", "cara", "dan", "erin", "finn"]
    lines = []
    for i in range(150):
        lines.append(json.dumps({"id": i, "name": rng.choice(names),
                                 "score": rng.randrange(0, 101)}))
    return "\n".join(lines) + "\n"


def _g_lines_1000():
    rng = random.Random(17)
    words = ["lorem", "ipsum", "dolor", "sit", "amet"]
    return "\n".join("line %04d %s" % (i, rng.choice(words))
                     for i in range(1000)) + "\n"


def _g_matrices():
    rng = random.Random(18)
    n = 40
    A = [[rng.randrange(-9, 10) for _ in range(n)] for _ in range(n)]
    B = [[rng.randrange(-9, 10) for _ in range(n)] for _ in range(n)]
    return {"A.json": json.dumps(A), "B.json": json.dumps(B)}


def _g_groupby_jsonl():
    rng = random.Random(19)
    depts = ["eng", "ops", "sales", "hr", "fin", "legal", "infra", "data"]
    lines = []
    for _ in range(500):
        lines.append(json.dumps({"dept": rng.choice(depts),
                                 "amount": rng.randrange(10, 5000)}))
    return "\n".join(lines) + "\n"


def _g_scores_csv():
    rng = random.Random(20)
    names = ["amy", "bob", "cara", "dan", "erin", "finn", "gina", "hal",
             "iris", "jack"]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["name", "score"])
    rows = [("p%02d" % i, rng.choice(names), rng.randrange(0, 101))
            for i in range(280)]
    rows = [(n, s) for _, n, s in rows]
    rows += rows[:20]  # inject exact duplicate rows
    rng.shuffle(rows)
    for n, s in rows:
        w.writerow([n, s])
    return out.getvalue()


def _g_series():
    rng = random.Random(21)
    return "\n".join("%.4f" % rng.uniform(-50, 50) for _ in range(500)) + "\n"


def _g_values_csv():
    rng = random.Random(22)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["value"])
    for _ in range(1000):
        w.writerow(["%.3f" % rng.uniform(0, 100)])
    return out.getvalue()


# ---------------------------------------------------------------- tasks

TASKS = [
    # -- A: shell-text -----------------------------------------------------
    dict(id="A1", title="Top-10 word frequencies", category="shell-text",
         requires={"shell"}, timeout_s=60,
         fixtures={"words.txt": _g_words}, outputs=["top10.txt"],
         prompt=("Read in/words.txt (one lowercase word per line, 5000 lines). "
                 "Write out/top10.txt with the 10 most frequent words, one per "
                 "line as '<count> <word>', sorted by count descending, ties "
                 "broken by word ascending. Example line: '312 alpha'.")),
    dict(id="A2", title="Extract email addresses", category="shell-text",
         requires={"shell"}, timeout_s=60,
         fixtures={"server.log": _g_server_log}, outputs=["emails.txt"],
         prompt=("Read in/server.log. Extract every email address matching "
                 "regex [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,} "
                 "(use grep -Eo). Write the UNIQUE addresses to out/emails.txt, "
                 "one per line, sorted ascending.")),
    dict(id="A3", title="CSV column stats", category="shell-text",
         requires={"shell"}, timeout_s=60,
         fixtures={"sales.csv": _g_sales_csv}, outputs=["stats.txt"],
         prompt=("Read in/sales.csv (header id,region,amount; amount is an "
                 "integer). Using awk, write out/stats.txt with exactly three "
                 "lines: 'sum=<int>', 'count=<int>', 'avg=<avg formatted to 2 "
                 "decimals>'.")),
    dict(id="A4", title="Duplicate-line report", category="shell-text",
         requires={"shell"}, timeout_s=60,
         fixtures={"events.txt": _g_events}, outputs=["dups.txt"],
         prompt=("Read in/events.txt. Find lines occurring more than once. "
                 "Write out/dups.txt with one line per duplicated line as "
                 "'<count><TAB><line>', sorted by count descending, ties by "
                 "line ascending.")),
    # -- B: shell-file -----------------------------------------------------
    dict(id="B1", title="CSV to TSV", category="shell-file",
         requires={"shell"}, timeout_s=60,
         fixtures={"data.csv": _g_simple_csv}, outputs=["data.tsv"],
         prompt=("Convert in/data.csv to tab-separated out/data.tsv "
                 "(simple CSV, no quoted commas; sed 's/,/\\t/g' is fine). "
                 "Keep the header row.")),
    dict(id="B2", title="Normalize line endings/whitespace", category="shell-file",
         requires={"shell"}, timeout_s=60,
         fixtures={"raw/a.txt": _g_raw_a, "raw/b.txt": _g_raw_b,
                   "raw/c.txt": _g_raw_c},
         outputs=["a.txt", "b.txt", "c.txt"],
         prompt=("in/raw/ holds a.txt b.txt c.txt with CRLF line endings and "
                 "trailing whitespace. Write normalized copies to out/a.txt "
                 "out/b.txt out/c.txt: LF endings, no trailing whitespace "
                 "on any line (use sed).")),
    dict(id="B3", title="JSONL to CSV with jq", category="shell-file",
         requires={"shell"}, timeout_s=60,
         fixtures={"records.jsonl": _g_records_jsonl}, outputs=["records.csv"],
         prompt=("Read in/records.jsonl (one flat JSON object per line with "
                 "keys id, name, score). Using jq, write out/records.csv with "
                 "header 'id,name,score' followed by one CSV row per record.")),
    dict(id="B4", title="Split file into 200-line chunks", category="shell-file",
         requires={"shell"}, timeout_s=60,
         fixtures={"lines.txt": _g_lines_1000},
         outputs=["chunk_00.txt", "chunk_01.txt", "chunk_02.txt",
                  "chunk_03.txt", "chunk_04.txt"],
         prompt=("Split in/lines.txt (1000 lines) into 5 files of exactly 200 "
                 "lines: out/chunk_00.txt .. out/chunk_04.txt (use split -l 200 "
                 "-d). Concatenated chunks must equal the original.")),
    # -- C: python-compute -------------------------------------------------
    dict(id="C1", title="Sum of primes below 200000", category="python-compute",
         requires={"python"}, timeout_s=120,
         fixtures={}, outputs=["answer.txt"],
         prompt=("Compute the sum of all prime numbers strictly below 200000 "
                 "(sieve of Eratosthenes). Write the single integer to "
                 "out/answer.txt, no extra whitespace.")),
    dict(id="C2", title="40x40 matrix multiply", category="python-compute",
         requires={"python"}, timeout_s=120,
         fixtures={"A.json": lambda: _g_matrices()["A.json"],
                   "B.json": lambda: _g_matrices()["B.json"]},
         outputs=["C.json"],
         prompt=("Read in/A.json and in/B.json (each a 40x40 list of lists of "
                 "ints). Compute C = A*B (standard matrix product) in Python "
                 "and write it as JSON to out/C.json.")),
    dict(id="C3", title="fib(35)", category="python-compute",
         requires={"python"}, timeout_s=60,
         fixtures={}, outputs=["answer.txt"],
         prompt=("Compute fib(35) iteratively in Python with fib(0)=0, "
                 "fib(1)=1. Write the single integer to out/answer.txt.")),
    dict(id="C4", title="Monte-Carlo pi (seeded)", category="python-compute",
         requires={"python"}, timeout_s=120,
         fixtures={}, outputs=["pi.txt"],
         prompt=("In Python: rng = random.Random(12345); n = 200000; draw "
                 "n pairs (x, y) uniform in [0,1); count pairs with "
                 "x*x + y*y <= 1; pi = 4*count/n. Write pi formatted to 6 "
                 "decimals (e.g. 3.141592) to out/pi.txt.")),
    # -- D: python-data ----------------------------------------------------
    dict(id="D1", title="Group-by department totals", category="python-data",
         requires={"python"}, timeout_s=60,
         fixtures={"records.jsonl": _g_groupby_jsonl}, outputs=["totals.json"],
         prompt=("Read in/records.jsonl (one JSON object per line: "
                 "{dept, amount}). In Python, sum amounts per dept and write "
                 "out/totals.json as {dept: total} with keys sorted.")),
    dict(id="D2", title="Dedupe and rank CSV", category="python-data",
         requires={"python"}, timeout_s=60,
         fixtures={"scores.csv": _g_scores_csv}, outputs=["ranked.csv"],
         prompt=("Read in/scores.csv (header name,score; contains exact "
                 "duplicate rows). In Python: drop duplicate rows, sort by "
                 "score descending then name ascending, write out/ranked.csv "
                 "with the header.")),
    dict(id="D3", title="Window-5 moving average", category="python-data",
         requires={"python"}, timeout_s=60,
         fixtures={"series.txt": _g_series}, outputs=["ma.txt"],
         prompt=("Read in/series.txt (one float per line, 500 lines). In "
                 "Python compute the window-5 moving average (496 values) and "
                 "write out/ma.txt with one value per line formatted to 6 "
                 "decimals.")),
    dict(id="D4", title="10-bin histogram", category="python-data",
         requires={"python"}, timeout_s=60,
         fixtures={"values.csv": _g_values_csv}, outputs=["hist.json"],
         prompt=("Read in/values.csv (header value; floats in [0,100)). In "
                 "Python, count values in 10 bins [0,10), [10,20), ..., "
                 "[90,100] and write out/hist.json as "
                 '{"0-10": n, "10-20": n, ..., "90-100": n}.')),
]


def materialize(task, batch_in_dir):
    """Write a task's fixtures to batch_in_dir/<task_id>/ ; return in_dir."""
    import os
    in_dir = os.path.join(batch_in_dir, task["id"])
    os.makedirs(in_dir, exist_ok=True)
    for rel, gen in task["fixtures"].items():
        p = os.path.join(in_dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        data = gen()
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(p, mode) as f:
            f.write(data)
    return in_dir


def expected_outputs(task):
    """Output filenames relative to the task's out/ dir."""
    return list(task["outputs"])
