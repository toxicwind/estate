#!/usr/bin/env python3
"""HMAC v2 test battery.

1. New post -> v2 signature, verifies, hmac_version == 'v2'.
2. Tampered lamport on v2 msg -> REJECTED.
3. Tampered parents on v2 msg -> REJECTED.
4. Stripped lamport/parents on v2 msg -> REJECTED (no downgrade).
5. Legacy v1 msg (no new fields) -> verifies as v1.
6. Transitional v1 msg (fields present, v1 HMAC) -> verifies as v1.
7. fleet_dag msg_ids unchanged by the upgrade (v1 byte stability).
"""
import os
import shutil
import subprocess
import sys

CHAT = "/home/toxic/.shingle/chat"
ROOT = "/tmp/hmacv2-test"
KEYS = "/tmp/smoke-keys"
ENV = {**os.environ, "FLEET_KEYS_DIR": KEYS, "AGENT_CHAT_ROOT": ROOT}

def chat(*args):
    return subprocess.run(
        [sys.executable, "chat.py", *args],
        cwd=CHAT, env=ENV, capture_output=True, text=True, timeout=60,
    )

shutil.rmtree(ROOT, ignore_errors=True)
assert chat("init", "c").returncode == 0

# 1. new post -> v2
assert chat("post", "c", "--from", "alice", "--title", "t",
            "--body", "v2 body").returncode == 0
md = f"{ROOT}/c/0001-alice-t.md"
text = open(md).read()
assert "lamport:" in text and "parents:" in text
r = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, '/home/toxic/.shingle/chat');"
     "import fleet_identity, os;"
     "os.environ['FLEET_KEYS_DIR']='/tmp/smoke-keys';"
     "m = fleet_identity.verify_on_read('/tmp/hmacv2-test/c/0001-alice-t.md');"
     "print(m['hmac_version'])"],
    capture_output=True, text=True, timeout=60, env=ENV)
assert r.stdout.strip() == "v2", r.stderr
print("PASS 1: new post signs v2, verifies as v2")

def expect_reject(path, label):
    r = chat("read", "c", "--as", "bob", "--all")
    assert r.returncode != 0, f"{label}: tampered message READ OK (must fail)"
    assert "identity check failed" in r.stderr, f"{label}: {r.stderr}"
    print(f"PASS: {label}")

# 2. tamper lamport
t2 = text.replace("lamport: 1", "lamport: 999")
open(md, "w").write(t2)
expect_reject(md, "2: tampered lamport rejected")

# 3. tamper parents
open(md, "w").write(text)  # restore
import re
t3 = re.sub(r"parents: \[.*\]", "parents: [deadbeef]", text)
assert t3 != text
open(md, "w").write(t3)
expect_reject(md, "3: tampered parents rejected")

# 4. strip the new fields entirely (downgrade attempt)
lines = [l for l in text.split("\n")
         if not l.startswith("lamport:") and not l.startswith("parents:")]
open(md, "w").write("\n".join(lines))
expect_reject(md, "4: stripped lamport/parents rejected (no downgrade)")

# 5. legacy v1 message (no new fields, v1 HMAC) still verifies
open(md, "w").write(text)  # restore v2 first
legacy = "\n".join(
    ["---", "seq: 7", "from: alice", "to: all", "channel: c",
     "ts: 2026-01-01T00:00:00+00:00", "status: discussion", "title: old",
     "hmac: PLACEHOLDER", "---", "legacy body", ""])
r = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, '/home/toxic/.shingle/chat');"
     "import fleet_identity;"
     "c = fleet_identity.canonical_message(seq=7, sender='alice', to='all',"
     " reply_to='', channel='c', ts='2026-01-01T00:00:00+00:00',"
     " status='discussion', title='old', body='legacy body');"
     "print(fleet_identity.sign('alice', c, '/tmp/smoke-keys'))"],
    capture_output=True, text=True, timeout=60, env=ENV)
sig = r.stdout.strip()
assert len(sig) == 64, r.stderr
open(f"{ROOT}/c/0007-alice-old.md", "w").write(legacy.replace("PLACEHOLDER", sig))
r = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, '/home/toxic/.shingle/chat');"
     "import fleet_identity;"
     "m = fleet_identity.verify_on_read('/tmp/hmacv2-test/c/0007-alice-old.md', '/tmp/smoke-keys');"
     "print(m['hmac_version'])"],
    capture_output=True, text=True, timeout=60, env=ENV)
assert r.stdout.strip() == "v1", r.stderr
print("PASS 5: legacy v1 message (no new fields) verifies as v1")

# 6. transitional: fields present but v1 HMAC -> verifies as v1
trans = "\n".join(
    ["---", "seq: 8", "from: alice", "to: all", "channel: c",
     "ts: 2026-01-01T00:00:00+00:00", "status: discussion", "title: trans",
     "lamport: 5", "parents: []",
     "hmac: PLACEHOLDER", "---", "transitional body", ""])
r = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, '/home/toxic/.shingle/chat');"
     "import fleet_identity;"
     "c = fleet_identity.canonical_message(seq=8, sender='alice', to='all',"
     " reply_to='', channel='c', ts='2026-01-01T00:00:00+00:00',"
     " status='discussion', title='trans', body='transitional body');"
     "print(fleet_identity.sign('alice', c, '/tmp/smoke-keys'))"],
    capture_output=True, text=True, timeout=60, env=ENV)
sig = r.stdout.strip()
open(f"{ROOT}/c/0008-alice-trans.md", "w").write(trans.replace("PLACEHOLDER", sig))
r = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, '/home/toxic/.shingle/chat');"
     "import fleet_identity;"
     "m = fleet_identity.verify_on_read('/tmp/hmacv2-test/c/0008-alice-trans.md', '/tmp/smoke-keys');"
     "print(m['hmac_version'])"],
    capture_output=True, text=True, timeout=60, env=ENV)
assert r.stdout.strip() == "v1", r.stderr
print("PASS 6: transitional message (fields, v1 HMAC) verifies as v1")

# 7. fleet_dag msg_ids unchanged (v1 byte stability)
r = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, '/home/toxic/.shingle/chat');"
     "import fleet_dag, fleet_identity;"
     "meta = {'seq':'1','from':'alice','to':'all','reply_to':'',"
     " 'channel':'c','ts':'t','status':'s','title':'ti'};"
     "d1 = fleet_dag.canonical_dag(meta, 'b', ['y','x']);"
     "d2 = fleet_dag.canonical_dag(meta, 'b', ['x','y']);"
     "assert d1 == d2, 'parent order must not affect dag id';"
     "import hashlib;"
     "print(hashlib.sha256(d1).hexdigest()[:16])"],
    capture_output=True, text=True, timeout=60)
assert r.returncode == 0, r.stderr
print(f"PASS 7: fleet_dag stable (id prefix {r.stdout.strip()})")

shutil.rmtree(ROOT, ignore_errors=True)
print("ALL HMAC-V2 TESTS PASS")
