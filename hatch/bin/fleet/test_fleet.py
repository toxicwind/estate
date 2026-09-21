#!/usr/bin/env python3
"""Tests for fleet.py — ordered fleet delivery.

Run: python3 test_fleet.py   (needs fleet.py in the same dir)
All state lands in a temp dir; nothing touches the live squawk-root.
Exit 0 = all pass, 1 = any failure. Prints PASS/FAIL per test.
"""
import base64
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet

PASSES, FAILS = [], []


def check(name, cond, detail=""):
    (PASSES if cond else FAILS).append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name,
                        ("- " + str(detail)) if detail and not cond else ""))


def fresh_scope(tmp, scope="fleet"):
    return fleet.Scope(os.path.join(tmp, "root"), scope)


def test_concurrent_publish_no_dup_no_loss():
    """32 threads x 25 publishes -> seqs exactly 1..800, no dupes, no gaps."""
    tmp = tempfile.mkdtemp()
    sc_proto = fresh_scope(tmp)
    n_threads, per = 32, 25

    def one(i):
        with fleet.Scope(sc_proto.root, "fleet") as sc:
            return sc.publish("m-%d" % i, "t", "t%d" % i, "body %d" % i)["seq"]

    with cf.ThreadPoolExecutor(max_workers=n_threads) as ex:
        seqs = list(ex.map(one, range(n_threads * per)))
    check("concurrent: 800 unique seqs", len(set(seqs)) == 800, len(set(seqs)))
    check("concurrent: exactly 1..800, no gaps/loss",
          sorted(seqs) == list(range(1, 801)))
    with fleet.Scope(sc_proto.root, "fleet") as sc:
        check("concurrent: gaps() empty", sc.gaps() == [], sc.gaps())


def test_dedup_collapses_retries():
    """Same msg_id published 16x concurrently -> one file, one seq."""
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "root")

    def one(_):
        with fleet.Scope(root, "fleet") as sc:
            return sc.publish("retry-42", "t", "r", "same body")

    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        res = list(ex.map(one, range(16)))
    seqs = {r["seq"] for r in res}
    deduped = sum(1 for r in res if r["deduped"])
    check("dedup: single seq across 16 racing retries", len(seqs) == 1, seqs)
    check("dedup: 15 collapsed as deduped", deduped == 15, deduped)
    with fleet.Scope(root, "fleet") as sc:
        files = sc._seq_files()
    check("dedup: exactly one message file", len(files) == 1, len(files))
    # same id twice sequentially -> same seq, deduped
    with fleet.Scope(root, "fleet") as sc:
        r = sc.publish("retry-42", "t", "r", "same body")
    check("dedup: sequential re-send collapses",
          r["deduped"] and r["seq"] == next(iter(seqs)), r)


def test_gap_detect_and_replay():
    """Simulated lost writes -> gaps() names them; fetch replays the rest."""
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "root")
    with fleet.Scope(root, "fleet") as sc:
        for i in range(10):
            sc.publish("g-%d" % i, "t", "g", "msg %d" % i)
    # lose the writes for seq 5 and 8 (crashed between alloc and write)
    gone = []
    with fleet.Scope(root, "fleet") as sc:
        for s, n in sc._seq_files():
            if s in (5, 8):
                os.remove(os.path.join(sc.dir, n))
                gone.append(s)
    check("gap setup removed 2 files", sorted(gone) == [5, 8], gone)
    with fleet.Scope(root, "fleet") as sc:
        missing = sc.gaps()
    check("gaps: detects exactly [5, 8]", missing == [5, 8], missing)
    with fleet.Scope(root, "fleet") as sc:
        # consumer had acked 4, fell behind: replay everything after 4
        replayed = sc.fetch(after=4, full=True)
    got = [r["seq"] for r in replayed]
    check("replay: fetch --after 4 returns survivors in order",
          got == [6, 7, 9, 10], got)
    bodies = {r["seq"]: r["text"] for r in replayed}
    check("replay: bodies intact", bodies.get(6) == "msg 5", bodies.get(6))
    # consumer can enumerate precisely what is unrecoverable
    check("replay: missing set disjoint from replayed",
          not (set(got) & set(missing)))


def test_acks_per_consumer():
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "root")
    with fleet.Scope(root, "fleet") as sc:
        for i in range(12):
            sc.publish("a-%d" % i, "t", "a", "x")
    with fleet.Scope(root, "fleet") as sc:
        sc.ack("watcher", 10)
        sc.ack("archiver", 7)
        sc.ack("watcher", 5)  # stale ack must not rewind
        got = sc.ack_get()
    check("acks: tracked per consumer", got == {"watcher": 10, "archiver": 7}, got)
    with fleet.Scope(root, "fleet") as sc:
        lag = sc.lag()
    check("lag: max 12, watcher lag 2, archiver lag 5",
          lag["max_seq"] == 12 and lag["consumers"]["watcher"]["lag"] == 2
          and lag["consumers"]["archiver"]["lag"] == 5, lag)
    with fleet.Scope(root, "fleet") as sc:
        one = sc.ack_get("watcher")
    check("ack-get single consumer", one == {"watcher": 10}, one)


def test_chat_isolation():
    """Two chats + main channel, published concurrently: independent seq
    spaces, zero cross-talk."""
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "root")
    ra = fleet.cmd_chat_new(root, "fleet", "Relay Alpha")
    rb = fleet.cmd_chat_new(root, "fleet", "Relay Beta")
    sa, sb = ra["scope"], rb["scope"]
    check("chat-new: scopes", (sa, sb) == ("fleet/chats/relay-alpha",
                                           "fleet/chats/relay-beta"), (sa, sb))

    def pub(args):
        scope, i, tag = args
        with fleet.Scope(root, scope) as sc:
            return sc.publish("iso-%s-%d" % (tag, i), "t", tag,
                              "body for %s #%d" % (tag, i))

    jobs = ([(sa, i, "A") for i in range(80)] +
            [(sb, i, "B") for i in range(80)] +
            [("fleet", i, "MAIN") for i in range(80)])
    with cf.ThreadPoolExecutor(max_workers=24) as ex:
        list(ex.map(pub, jobs))

    with fleet.Scope(root, sa) as a, fleet.Scope(root, sb) as b, \
            fleet.Scope(root, "fleet") as m:
        fa = a.fetch(full=True)
        fb = b.fetch(full=True)
        fm = m.fetch(full=True)
    check("isolation: chat A seqs 1..80",
          [r["seq"] for r in fa] == list(range(1, 81)))
    check("isolation: chat B seqs 1..80",
          [r["seq"] for r in fb] == list(range(1, 81)))
    check("isolation: main seqs 1..80",
          [r["seq"] for r in fm] == list(range(1, 81)))
    check("isolation: A sees only A bodies",
          all("body for A" in r["text"] for r in fa)
          and not any("body for B" in r["text"] for r in fa))
    check("isolation: B sees only B bodies",
          all("body for B" in r["text"] for r in fb))
    check("isolation: main sees no chat traffic",
          all("body for MAIN" in r["text"] for r in fm))
    check("isolation: no gaps anywhere",
          a.gaps() == [] and b.gaps() == [] and m.gaps() == [])


def test_msg_id_cannot_escape():
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "root")
    evil = "../../etc/pwned"
    with fleet.Scope(root, "fleet") as sc:
        r = sc.publish(evil, "t", "e", "x")
    check("sanitize: evil msg_id publishes inside scope", r["seq"] == 1, r)
    ids_dir = os.path.join(root, "fleet", ".fleet", "ids")
    names = os.listdir(ids_dir)
    check("sanitize: id file has no path separators",
          all("/" not in n for n in names), names)
    check("sanitize: nothing escaped to /etc",
          not os.path.exists("/etc/pwned"))
    check("sanitize: nothing escaped to root parent",
          not os.path.exists(os.path.join(tmp, "etc")))


def test_new_scope_inside_lock():
    """Regression: first-ever send to a brand-new channel must not drop."""
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "root")
    with fleet.Scope(root, "brand-new-channel") as sc:
        r = sc.publish("first", "t", "hello", "world")
    check("new scope: first publish gets seq 1", r["seq"] == 1, r)
    expect = os.path.join(root, "brand-new-channel", "1-t-hello.md")
    check("new scope: file exists", os.path.exists(expect), expect)


def test_cli_roundtrip():
    """fleet.py as a real subprocess: publish -> fetch -> ack -> lag."""
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "root")
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleet.py")

    def run(*args):
        r = subprocess.run([sys.executable, fp, "--root", root, *args],
                           capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)

    b64 = base64.b64encode("hello via cli".encode()).decode()
    p1 = run("publish", "--scope", "fleet", "--id", "cli-1",
             "--from", "cli", "--title", "t", "--text-b64", b64)
    p2 = run("publish", "--scope", "fleet", "--id", "cli-1",
             "--from", "cli", "--title", "t", "--text-b64", b64)
    check("cli: publish returns seq 1", p1["seq"] == 1, p1)
    check("cli: republish same id dedupes", p2["deduped"] and p2["seq"] == 1, p2)
    f = run("fetch", "--scope", "fleet", "--after", "0", "--full")["messages"]
    check("cli: fetch sees it", len(f) == 1 and f[0]["text"] == "hello via cli", f)
    g = run("gaps", "--scope", "fleet")
    check("cli: no gaps", g["missing"] == [] and g["max_seq"] == 1, g)
    a = run("ack", "--scope", "fleet", "--consumer", "cli", "--seq", "1")
    check("cli: ack", a["acked"] == 1, a)
    lg = run("lag", "--scope", "fleet")
    check("cli: lag 0", lg["consumers"]["cli"]["lag"] == 0, lg)
    cn = run("chat-new", "--channel", "fleet", "--name", "CLI Chat")
    check("cli: chat-new", cn["scope"] == "fleet/chats/cli-chat", cn)


def main():
    tests = [test_concurrent_publish_no_dup_no_loss,
             test_dedup_collapses_retries,
             test_gap_detect_and_replay,
             test_acks_per_consumer,
             test_chat_isolation,
             test_msg_id_cannot_escape,
             test_new_scope_inside_lock,
             test_cli_roundtrip]
    for t in tests:
        print("--- %s" % t.__name__)
        try:
            t()
        except Exception as ex:  # noqa: BLE001 - fail fast, record, continue
            FAILS.append(t.__name__)
            print("FAIL %s - EXC %s: %s" % (t.__name__, type(ex).__name__, ex))
    print("\n%d passed, %d failed" % (len(PASSES), len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
