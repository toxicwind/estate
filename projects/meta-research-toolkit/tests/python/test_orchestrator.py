import pytest
import tempfile
from pathlib import Path
from src.python.fsbus_orchestrator import init_bus, submit, claim, finish, count_attempts, reap_expired


@pytest.fixture
def bus(tmp_path):
    import src.python.fsbus_orchestrator as mod
    mod.BUS = tmp_path / "fsbus"
    mod.INBOX = mod.BUS / "inbox"
    mod.CLAIMED = mod.BUS / "claimed"
    mod.OUTBOX = mod.BUS / "outbox"
    mod.DEAD = mod.BUS / "dead"
    mod.MANIFEST = mod.BUS / "manifest.jsonl"
    init_bus()
    return mod


def test_submit_creates_task(bus):
    tid = bus.submit({"payload": "x"})
    assert (bus.INBOX / f"{tid}.json").exists()


def test_claim_is_exclusive(bus):
    bus.submit({"payload": "y"})
    a = bus.claim("w1")
    b = bus.claim("w2")
    assert a is not None
    assert b is None  # exclusive


def test_finish_moves_to_outbox(bus):
    tid = bus.submit({"payload": "z"})
    bus.claim("w1")
    bus.finish(tid, "w1", True, {"r": 1})
    assert (bus.OUTBOX / f"{tid}.json").exists()
    assert not (bus.CLAIMED / f"{tid}.w1.json").exists()


def test_retry_bounded(bus):
    tid = bus.submit({"payload": "fail"})
    for _ in range(4):
        job = bus.claim("w1")
        if job is None:
            break
        tid2, _ = job
        bus.finish(tid2, "w1", False, {}, error="err")
    # After MAX_ATTEMPTS (3), should be in dead
    assert (bus.DEAD / f"{tid}.json").exists()
