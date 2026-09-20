#!/usr/bin/env python3
"""E2EE wiring smoke test.

1. init priv-vault provisions a channel key.
2. Post a secret; assert NO plaintext in .md or log.jsonl.
3. read shows the plaintext; HMAC verifies (over ciphertext).
4. digest shows a decrypted snippet, not a token.
5. Tampered ciphertext -> read fails closed.
6. Wrong/missing key -> post fails closed.
Cleans up the test key afterwards.
"""
import os
import shutil
import subprocess
import sys

CHAT = "/home/toxic/.shingle/chat"
ROOT = "/tmp/e2ee-test"
KEYS = "/tmp/e2ee-keys"
SECRET = "the launch codes are 7-7-7-xyz"
ENV = {**os.environ, "FLEET_KEYS_DIR": KEYS, "AGENT_CHAT_ROOT": ROOT}

def chat(*args):
    return subprocess.run(
        [sys.executable, "chat.py", *args],
        cwd=CHAT, env=ENV, capture_output=True, text=True, timeout=60,
    )

# fleet_e2ee.KEYS_DIR is hardcoded; point it at the sandbox via sitecustomize-style shim:
# simplest: run everything through a wrapper that monkeypatches before main.
shutil.rmtree(ROOT, ignore_errors=True)
shutil.rmtree(KEYS, ignore_errors=True)

WRAP = (
    "import sys; sys.path.insert(0, '/home/toxic/.shingle/chat');"
    "import fleet_e2ee, pathlib;"
    "fleet_e2ee.KEYS_DIR = pathlib.Path('/tmp/e2ee-keys');"
    "sys.argv = ['chat.py', *sys.argv[1:]];"
    "exec(open('/home/toxic/.shingle/chat/chat.py').read())"
)

def chat_wrap(*args):
    return subprocess.run(
        [sys.executable, "-c", WRAP, *args],
        cwd=CHAT, env=ENV, capture_output=True, text=True, timeout=60,
    )

for agent in ("alice", "bob"):
    r = chat("keygen", agent)
    assert r.returncode == 0 or "already exists" in r.stderr, r.stderr

r = chat_wrap("init", "priv-vault", "--members", "alice,bob")
assert r.returncode == 0, f"init priv failed: {r.stderr}"
assert os.path.exists("/tmp/e2ee-keys/priv-vault.key"), "channel key not provisioned"
print("PASS 1: priv channel init provisions key")

r = chat_wrap("post", "priv-vault", "--from", "alice", "--to", "bob",
              "--title", "codes", "--body", SECRET)
assert r.returncode == 0, f"post failed: {r.stderr}"
print("PASS 2: encrypted post accepted")

# --- no plaintext at rest ---
md_files = [f for f in os.listdir(f"{ROOT}/priv-vault") if f.endswith(".md")]
assert len(md_files) == 1
md_text = open(f"{ROOT}/priv-vault/{md_files[0]}").read()
log_text = open(f"{ROOT}/priv-vault/log.jsonl").read()
assert SECRET not in md_text, "PLAINTEXT LEAK in .md file"
assert SECRET not in log_text, "PLAINTEXT LEAK in log.jsonl"
assert "gAAAAA" in md_text, "expected Fernet token in .md"
assert "gAAAAA" in log_text, "expected Fernet token in log.jsonl"
print("PASS 3: no plaintext in .md or log.jsonl; ciphertext present in both")

# --- digest decrypts the snippet (bob is the recipient; --peek before his read) ---
r = chat_wrap("digest", "--as", "bob", "--peek")
assert r.returncode == 0, f"digest failed: {r.stderr}"
assert "launch codes" in r.stdout, f"digest snippet not decrypted: {r.stdout}"
print("PASS 4: digest shows decrypted snippet")

# --- read decrypts after verifying ---
r = chat_wrap("read", "priv-vault", "--as", "bob", "--all")
assert r.returncode == 0, f"read failed: {r.stderr}"
assert SECRET in r.stdout, "read did not show plaintext"
assert "gAAAAA" not in r.stdout, "read leaked ciphertext to display"
print("PASS 5: read verifies HMAC then decrypts; plaintext shown, no token")

# --- tampered ciphertext fails closed on read ---
md_path = f"{ROOT}/priv-vault/{md_files[0]}"
tampered = md_text.replace("gAAAAA", "gAAABA", 1)
open(md_path, "w").write(tampered)
r = chat_wrap("read", "priv-vault", "--as", "bob", "--all")
assert r.returncode != 0, "tampered ciphertext read SUCCEEDED (must fail closed)"
assert "identity check failed" in r.stderr, f"wrong failure mode: {r.stderr}"
print("PASS 6: tampered ciphertext fails closed (HMAC rejects before decrypt)")

# --- missing key fails closed on post ---
os.remove("/tmp/e2ee-keys/priv-vault.key")
r = chat_wrap("post", "priv-vault", "--from", "alice", "--to", "bob",
              "--title", "x", "--body", "should not post")
assert r.returncode != 0, "post without key SUCCEEDED (must fail closed)"
assert "cannot encrypt" in r.stderr, f"wrong failure mode: {r.stderr}"
print("PASS 7: post without channel key fails closed (no plaintext fallback)")

# --- cleanup ---
shutil.rmtree(ROOT, ignore_errors=True)
shutil.rmtree(KEYS, ignore_errors=True)
print("ALL E2EE TESTS PASS")
