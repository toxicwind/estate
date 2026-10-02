#!/usr/bin/env python3
"""market.py -- shared market/v1 wire client for the squawk bid-market.

Implements the frozen wire (WIRE.md, t2-architect fleet seq 10091):
public channel 'market'; standard squawk frontmatter; body = human header +
'market/v1' marker line + YAML block (HMAC covers the whole body).

Both the auctioneer and bidders import this; the wire lives here, not in
two places.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

WIRE_MARKER = "market/v1"
CHANNEL = "market"
BASE = Path("/home/toxic/sovereign/killer-features/bid-market")

CHAT_CODE = Path(os.environ.get(
    "SQUAWK_CODE_DIR", "/home/toxic/sovereign/hatch/agents/ember/chat"))
RELAY_CODE = Path("/home/toxic/sovereign/hatch/agents/ember/squawk-relay")
CHAT_ROOT = Path(os.environ.get(
    "SQUAWK_CHAT_ROOT", "/home/toxic/.shingle/squawk-root"))
MARKET_DIR = CHAT_ROOT / CHANNEL
LEDGER = MARKET_DIR / "ledger.jsonl"
CALIB_FILE = BASE / "calibration.json"

MSG_TYPES = ("TASK_POST", "BID", "ASSIGN", "RESULT", "HEARTBEAT", "CANCEL")

REQUIRED = {
    "TASK_POST": ("task_id", "title", "budget", "deadline_s"),
    "BID": ("task_id", "attempt", "bidder", "confidence", "cost", "eta_s"),
    "ASSIGN": ("task_id", "attempt", "winner", "scores", "n_bids",
               "assign_ts", "result_deadline_ts"),
    "RESULT": ("task_id", "attempt", "bidder", "status"),
    "HEARTBEAT": ("task_id", "attempt", "bidder"),
    "CANCEL": ("task_id", "attempt", "reason"),
}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

_sys_path_ready = False


def _ensure_imports():
    global _sys_path_ready
    if _sys_path_ready:
        return
    for p in (str(CHAT_CODE), str(RELAY_CODE)):
        if p not in sys.path:
            sys.path.insert(0, p)
    _sys_path_ready = True


def _canonical_post():
    _ensure_imports()
    import canonical_post
    canonical_post.ensure_keys_env(CHAT_ROOT)
    return canonical_post


# ---------------------------------------------------------------- body I/O

def build_body(human: str, payload: dict) -> str:
    """Human header + marker + YAML block."""
    import yaml
    y = yaml.safe_dump(dict(payload), sort_keys=True, default_flow_style=False)
    return human.rstrip() + "\n\n" + WIRE_MARKER + "\n" + y


def parse_body(text: str):
    """Split body into (human, wire_dict|None). wire_dict None => not a wire msg."""
    lines = text.splitlines()
    try:
        idx = lines.index(WIRE_MARKER)
    except ValueError:
        return text, None
    import yaml
    try:
        wire = yaml.safe_load("\n".join(lines[idx + 1:])) or {}
    except Exception:
        return text, None
    if not isinstance(wire, dict) or wire.get("type") not in MSG_TYPES:
        return text, None
    return "\n".join(lines[:idx]).strip(), wire


def parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm, body = m.groups()
    meta = {}
    for line in fm.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body


def parse_file(path) -> dict | None:
    """Parse a market .md file. Returns None if not a wire message."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    meta, body = parse_frontmatter(text)
    human, wire = parse_body(body)
    if wire is None:
        return None
    missing = [k for k in REQUIRED.get(wire.get("type"), ()) if k not in wire]
    return {
        "path": str(path),
        "seq": int(meta.get("seq", 0) or 0),
        "sender": meta.get("from", ""),
        "ts": meta.get("ts", ""),
        "title": meta.get("title", ""),
        "msg_type": wire.get("type"),
        "task_id": str(wire.get("task_id", "")),
        "human": human,
        "wire": wire,
        "missing": missing,
    }


def ts_to_epoch(ts: str) -> float:
    # chat ts looks like 2026-09-20T06:34:09.147294+00:00
    try:
        from datetime import datetime
        return datetime.fromisoformat(ts).timestamp()
    except Exception:
        return time.time()


# ------------------------------------------------------------------ posting

def post_wire(channel: str, sender: str, title: str, human: str,
              payload: dict, msg_type: str, status: str = "market"):
    """Post a signed market/v1 message. Returns (seq, filename)."""
    cp = _canonical_post()
    body = build_body(human, dict(payload, type=msg_type))
    extra = {"wire": WIRE_MARKER,
             "msg_type": msg_type,
             "task_id": str(payload.get("task_id", ""))}
    return cp._post_message(CHAT_ROOT, channel, body=body, sender=sender,
                            title=title, extra_frontmatter=extra,
                            status=status)


def ensure_key(agent_id: str) -> Path:
    """Mint an HMAC identity key for agent_id if missing."""
    cp = _canonical_post()
    import fleet_identity
    kd = cp.resolve_key_dir(CHAT_ROOT)
    kd.mkdir(parents=True, exist_ok=True)
    kp = kd / f"{agent_id}.key"
    if not kp.exists():
        fleet_identity.keygen(agent_id, kd=kd)
    return kp


def verify_file(path) -> dict:
    """Verify HMAC on a market file; raises on bad/missing signature."""
    _ensure_imports()
    import fleet_identity
    kd = None
    env = os.environ.get("FLEET_KEYS_DIR")
    if env:
        kd = Path(env)
    return fleet_identity.verify_on_read(path, kd=kd)


# ------------------------------------------------------------------- scoring

def clamp01(x: float) -> float:
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def score_bid(confidence: float, cal: float, cost: float, budget: float,
              eta_s: float, deadline_s: float) -> float:
    """Frozen t2-architect formula; each term clamped to [0,1]."""
    conf_t = clamp01(confidence) * clamp01(cal)
    if budget and budget > 0:
        cost_t = clamp01(1.0 - cost / budget)
    else:
        cost_t = 0.0
    if deadline_s and deadline_s > 0:
        eta_t = clamp01(1.0 - eta_s / deadline_s)
    else:
        eta_t = 0.0
    return 0.5 * conf_t + 0.3 * cost_t + 0.2 * eta_t


# --------------------------------------------------------------- calibration

def load_calib() -> dict:
    try:
        return json.loads(CALIB_FILE.read_text())
    except (OSError, ValueError):
        return {}


def save_calib(cal: dict) -> None:
    CALIB_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CALIB_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cal, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, CALIB_FILE)


def get_cal(cal: dict, bidder: str) -> float:
    return float(cal.get(bidder, {}).get("cal", 1.0))


def record_outcome(cal: dict, bidder: str, ok: bool, quality: float = 1.0) -> float:
    """Update calibration per frozen rule. Returns new cal value."""
    e = cal.get(bidder, {"cal": 1.0, "done": 0, "fail": 0})
    c = float(e.get("cal", 1.0))
    if ok:
        q = clamp01(quality)
        c = 0.85 * c + 0.15 * q
        e["done"] = int(e.get("done", 0)) + 1
    else:
        c = 0.7 * c
        e["fail"] = int(e.get("fail", 0)) + 1
    e["cal"] = max(0.05, c)
    cal[bidder] = e
    return e["cal"]


# -------------------------------------------------------------------- ledger

def append_ledger(event: dict) -> None:
    MARKET_DIR.mkdir(parents=True, exist_ok=True)
    event = dict(event)
    event.setdefault("ts", time.time())
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def now_iso() -> str:
    _ensure_imports()
    import chat as _chat
    return _chat.now_iso()
