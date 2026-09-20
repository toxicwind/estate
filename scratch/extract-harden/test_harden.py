#!/usr/bin/env python3
"""Local verification of the three hardening modules before deployment."""
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, "/home/hatch/workspace/extract-harden")
os.environ["FLEET_KEYS_DIR"] = tempfile.mkdtemp(prefix="fleetkeys_")

import fleet_identity as fi
import fleet_wait as fw
import fleet_watch as fwt

PASS = []
FAIL = []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" -- {extra}" if extra and not cond else ""))


# ---------- fleet_identity ----------
fi.keygen("agent-a")
fi.keygen("8a756bd0")
try:
    fi.keygen("agent-a")
    check("keygen refuses clobber", False)
except fi.FleetIdentityError:
    check("keygen refuses clobber", True)
try:
    fi.keygen("../evil")
    check("keygen rejects traversal", False)
except fi.FleetIdentityError:
    check("keygen rejects traversal", True)
try:
    fi.keygen("_hidden")
    check("keygen rejects reserved prefix", False)
except fi.FleetIdentityError:
    check("keygen rejects reserved prefix", True)

canon = fi.canonical_message(seq=7, sender="agent-a", to="all", reply_to=None,
                             channel="ops", ts="2026-09-14T05:00:00+00:00",
                             status="discussion", title="hello",
                             body="line1\nline2\n")
sig = fi.sign("agent-a", canon)
check("sig is 64 hex", len(sig) == 64 and all(c in "0123456789abcdef" for c in sig))
check("verify ok", fi.verify("agent-a", canon, sig))
check("verify tampered body", not fi.verify("agent-a", canon[:-1] + b"X", sig))
check("verify wrong agent", not fi.verify("8a756bd0", canon, sig))
check("verify unknown agent -> False", not fi.verify("ghost", canon, sig))
check("verify bad hex -> False", not fi.verify("agent-a", canon, "zz"))
try:
    fi.sign("ghost", canon)
    check("sign unknown agent raises", False)
except fi.FleetIdentityError:
    check("sign unknown agent raises", True)

# Build a message file byte-identical to base cmd_post output, with hmac last.
tmpd = tempfile.mkdtemp(prefix="chatroot_")
chan = os.path.join(tmpd, "ops")
os.makedirs(os.path.join(chan, ".cursors"))
seq, sender, to, channel = 7, "agent-a", "all", "ops"
ts, status, title = "2026-09-14T05:00:00+00:00", "discussion", "hello"
body = "line1\nline2\n"
fm = ["---", f"seq: {seq}", f"from: {sender}", f"to: {to}",
      f"channel: {channel}", f"ts: {ts}", f"status: {status}", f"title: {title}"]
canon2 = fi.canonical_message(seq=seq, sender=sender, to=to, reply_to=None,
                              channel=channel, ts=ts, status=status, title=title, body=body)
fm.append(f"hmac: {fi.sign(sender, canon2)}")
fm += ["---", ""]
msgpath = os.path.join(chan, "0007-agent-a-hello.md")
with open(msgpath, "w", encoding="utf-8") as f:
    f.write("\n".join(fm) + body.rstrip() + "\n")
meta = fi.verify_on_read(msgpath)
check("verify_on_read ok", meta.get("from") == "agent-a" and meta.get("seq") == "7"
      and "hmac" not in meta)

# Tamper with body -> must fail closed naming the agent
with open(msgpath, "a", encoding="utf-8") as f:
    f.write("tampered\n")
try:
    fi.verify_on_read(msgpath)
    check("tamper detected", False)
except fi.FleetIdentityError as e:
    check("tamper detected", "agent-a" in str(e), str(e))

# Unsigned file -> fail closed naming the claimant
unsigned = os.path.join(chan, "0008-agent-a-nope.md")
with open(unsigned, "w", encoding="utf-8") as f:
    f.write("---\nseq: 8\nfrom: agent-a\nto: all\nchannel: ops\nts: x\nstatus: discussion\ntitle: nope\n---\n\nbody\n")
try:
    fi.verify_on_read(unsigned)
    check("unsigned rejected", False)
except fi.FleetIdentityError as e:
    check("unsigned rejected", "agent-a" in str(e) and "no 'hmac'" in str(e), str(e))

# Forged 'from' (attacker re-labels someone else's signed file) -> fail
forged = os.path.join(chan, "0009-forged.md")
with open(msgpath.replace("tampered", ""), "rb") as f:
    data = f.read()
open(msgpath, "wb").write(data.split(b"tampered\n")[0])  # restore original
with open(msgpath, "rb") as f:
    orig = f.read().decode()
with open(forged, "w", encoding="utf-8") as f:
    f.write(orig.replace("from: agent-a", "from: 8a756bd0"))
try:
    fi.verify_on_read(forged)
    check("forged from rejected", False)
except fi.FleetIdentityError as e:
    check("forged from rejected", "8a756bd0" in str(e), str(e))

# sign-archive migration on the unsigned file
check("sign-archive signs", fi.sign_archive_file(unsigned) is True)
check("sign-archive idempotent", fi.sign_archive_file(unsigned) is False)
meta2 = fi.verify_on_read(unsigned)
check("migrated file verifies", meta2.get("from") == "agent-a")

# CLI smoke
import subprocess
r = subprocess.run([sys.executable, "/home/hatch/workspace/extract-harden/fleet_identity.py",
                    "verify-file", msgpath], capture_output=True, text=True)
check("cli verify-file ok", r.returncode == 0 and r.stdout.startswith("OK"), r.stderr[:200])

# ---------- fleet_wait ----------
start = time.monotonic()
res = fw.wait_for_new_messages(chan, 999, 0.6)
check("wait timeout -> []", res == [] and 0.5 <= time.monotonic() - start < 2.0,
      f"elapsed={time.monotonic()-start:.2f}")


def poster():
    time.sleep(0.4)
    p = os.path.join(chan, "0010-agent-a-late.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("---\nseq: 10\nfrom: agent-a\n---\n\nx\n")


t = threading.Thread(target=poster)
t.start()
start = time.monotonic()
res = fw.wait_for_new_messages(chan, 9, 10)
elapsed = time.monotonic() - start
t.join()
check("inotify wait returns new msg fast", len(res) == 1 and res[0].name.startswith("0010")
      and elapsed < 3.0, f"elapsed={elapsed:.2f} n={len(res)}")

# poll fallback directly (takes an absolute deadline, like the real caller)
start = time.monotonic()
res = fw._wait_poll(chan, 999, start + 0.6)
check("poll fallback timeout", res == [] and 0.5 <= time.monotonic() - start < 2.0)

# seq parsing edge: unicode superscript must NOT parse (base parity)
check("seq rejects superscript", fw._seq_from_name("²-agent-x.md") is None)
check("seq parses 0007", fw._seq_from_name("0007-agent-a-hello.md") == 7)
check("wait timeout=0 single scan", fw.wait_for_new_messages(chan, 999, 0) == [])

# ---------- fleet_watch ----------
root = tempfile.mkdtemp(prefix="watchroot_")
check("watch missing index yields nothing", list(fwt.watch_channels(root)) == [])
fwt.note_channel(root, "ops")
fwt.note_channel(root, "alerts")
got = list(fwt.watch_channels(root, 0))
check("watch yields 2 channels", [n for _, n in got] == ["ops", "alerts"], str(got))
off = got[-1][0]
check("resume from offset yields nothing new", list(fwt.watch_channels(root, off)) == [])
fwt.note_channel(root, "third")
got2 = list(fwt.watch_channels(root, off))
check("resume picks up new", [n for _, n in got2] == ["third"] and got2[0][0] > off)
for bad in ["../x", "a/b", "a:b", ".hidden", "_priv", "has\ttab", ""]:
    try:
        fwt.note_channel(root, bad)
        check(f"note_channel rejects {bad!r}", False)
    except fwt.FleetWatchError:
        pass
check("note_channel rejects bad names", True)
lines = open(os.path.join(root, ".channels-index"), encoding="utf-8").read().splitlines()
check("index lines tab-separated", all(l.count("\t") == 1 for l in lines) and len(lines) == 3)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILURES:", FAIL)
    sys.exit(1)
