import sys, os, random, shutil
sys.path.insert(0, "/home/toxic/.shingle/chat")
import fleet_presence as fp

root = "/tmp/presence-test"
shutil.rmtree(root, ignore_errors=True)
os.makedirs(root)

# --- heartbeats / incarnation ---
h1 = fp.heartbeat(root, "alice")
h2 = fp.heartbeat(root, "alice")
assert h2["incarnation"] == h1["incarnation"] + 1 == 1, (h1, h2)
assert fp.heartbeat_age(root, "alice") < 5
assert fp.is_alive(root, "alice") == "alive"
assert fp.is_alive(root, "ghost") == "dead"

# --- views ---
v = fp.update_view(root, "alice", "bob", rng=random.Random(42))
assert "bob" in v and "alice" not in v, v
fp._write_view(root, "bob", ["carol", "dave", "erin"])
v2 = fp.update_view(root, "alice", "bob", rng=random.Random(7))
assert "bob" in v2 and "carol" in v2, v2
assert len(v2) <= fp.VIEW_K
fp._write_view(root, "alice", [])
r1 = fp.update_view(root, "alice", "bob", rng=random.Random(123))
fp._write_view(root, "alice", [])
r2 = fp.update_view(root, "alice", "bob", rng=random.Random(123))
assert r1 == r2, (r1, r2)  # seeded rng => deterministic
print("view:", r1)

# --- SWIM states via _now patching ---
orig = fp._now
base = orig()
fp._now = lambda: base + 30
assert fp.is_alive(root, "alice") == "alive"
fp._now = lambda: base + 61
assert fp.is_alive(root, "alice") == "suspect"
w = fp.suspect(root, "bob", "alice", "no heartbeat for a while")
assert w is True
m = fp.suspect_marks(root, "alice")
assert m and m["by"] == "bob" and m["reason"] == "no heartbeat for a while"
fp._now = lambda: base + 301
assert fp.is_alive(root, "alice") == "dead"
# fresh heartbeat refutes mark
fp._now = orig
fp.heartbeat(root, "alice")
assert fp.is_alive(root, "alice") == "alive"
# suspect() refuses on fresh heartbeat
assert fp.suspect(root, "bob", "alice", "should not write") is False
# alive_agents map
fp.heartbeat(root, "bob")
agents = fp.alive_agents(root)
assert agents == {"alice": "alive", "bob": "alive"}, agents
print("alive_agents:", agents)
# peer_sample filters liveness
fp._write_view(root, "alice", ["bob", "ghost", "carol"])
fp.heartbeat(root, "carol")
targets = fp.peer_sample(root, "alice", count=5, rng=random.Random(1))
assert targets == ["bob", "carol"], targets
print("targets:", targets)
# unsafe names rejected
for bad in ["../x", "/etc", ".hidden", "a/b"]:
    try:
        fp.heartbeat(root, bad)
        raise AssertionError("accepted %r" % bad)
    except ValueError:
        pass
shutil.rmtree(root, ignore_errors=True)
print("ALL PRESENCE TESTS PASS")
