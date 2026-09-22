#!/usr/bin/env python3
"""Post a super-ralph task directly with exec_mode set."""
import importlib.util, json, sys, time
from pathlib import Path

BIN = Path("/home/toxic/sovereign/agents/oracle-market/bin")
sys.path.insert(0, str(BIN))

_spec = importlib.util.spec_from_file_location("bidder", BIN / "bidder.py")
bidder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bidder)
import sealed as sealed_mod
import mechanism as mech


def load_control_hmac_key():
    p = mech.control_key_path()
    master = p.read_text(encoding="utf-8").strip()
    return sealed_mod.hkdf(bytes.fromhex(master), sealed_mod.CTL_INFO)


ctl_hmac = load_control_hmac_key()
poster = bidder.SeqPoster(bidder.CHANNEL, "bid-market", "ralph-pathfinder")

task_id = "probe-ralph-fix-004"
payload_text = (
    "NON-SIMPLE task. Steps: (1) Confirm the model backend is reachable. "
    "(2) Create probe-result.txt in the workdir with the model name and UTC timestamp. "
    "(3) Report completion with the artifact path. "
    "This tests the FIXED single-loop SuperRalph framework."
)
body = {
    "task_id": task_id,
    "title": "super-ralph path probe 4: verify single-loop fix",
    "payload": payload_text,
    "tags": ["probe"],
    "capabilities": ["super-ralph"],
    "exec_mode": "super-ralph",
    "acceptance": [
        "probe-result.txt exists in the workdir",
        "probe-result.txt names the model that answered",
    ],
    "bid_window_ms": 15000,
    "timeout_ms": 1800000,
    "posted_ts": time.time(),
}
ctl_ts = int(time.time())
ctl_sig = sealed_mod.sign_control(
    ctl_hmac, "task_post", task_id,
    sealed_mod.ctl_body_sha256(body), ctl_ts)
canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
name = poster.post("task_post", f"task-{task_id}", canon, task_id=task_id,
                   raw_body=True,
                   extra_fm={"ctl_sig": ctl_sig, "ctl_ts": ctl_ts},
                   note="task posted: super-ralph probe 4 [single-loop fix test]")
print(f"posted {name}")
