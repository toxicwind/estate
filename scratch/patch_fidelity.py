#!/usr/bin/env python3
"""Coordinator patch 10: backfill fidelity.

1. fleet_log.append: accept optional fidelity fields (msg_hmac, to, title,
   reply_to, status, lamport, parents) so a log record can reconstruct a
   byte-identical, HMAC-verifiable message file.
2. fleet_gossip._recovered_text: prefer the record's original frontmatter and
   restore the hmac: line when msg_hmac is present; legacy -recovered
   fallback only for old records without it.
"""
from pathlib import Path

BASE = Path("/home/toxic/.shingle/chat")

# --- 1. fleet_log.py ---
p = BASE / "fleet_log.py"
src = p.read_text(encoding="utf-8")

old_sig = """    ts: Optional[str] = None,
    key: Optional[_KeyType] = None,
    fsync: bool = True,
) -> int:"""
new_sig = """    ts: Optional[str] = None,
    key: Optional[_KeyType] = None,
    fsync: bool = True,
    # Fidelity fields (optional): carried so anti-entropy backfill can
    # reconstruct a byte-identical, HMAC-verifiable message file.
    msg_hmac: Optional[str] = None,
    to: Optional[str] = None,
    title: Optional[str] = None,
    reply_to: Optional[str] = None,
    status: Optional[str] = None,
    lamport: Optional[int] = None,
    parents: Optional[list] = None,
) -> int:"""
assert src.count(old_sig) == 1, "fleet_log sig anchor"
src = src.replace(old_sig, new_sig, 1)

old_rec = '''    rec = {
        "seq": seq,
        "ts": ts if ts is not None else _now_iso(),
        "agent": agent,
        "type": type,
        "body": body,
    }'''
new_rec = '''    rec = {
        "seq": seq,
        "ts": ts if ts is not None else _now_iso(),
        "agent": agent,
        "type": type,
        "body": body,
    }
    # Optional fidelity fields: stored verbatim when provided.
    if msg_hmac is not None:
        if not isinstance(msg_hmac, str):
            raise FleetLogError("msg_hmac must be str")
        rec["msg_hmac"] = msg_hmac
    for label, val in (("to", to), ("title", title), ("reply_to", reply_to),
                       ("status", status)):
        if val is not None:
            if not isinstance(val, str):
                raise FleetLogError(f"{label} must be str")
            rec[label] = val
    if lamport is not None:
        if not isinstance(lamport, int) or isinstance(lamport, bool):
            raise FleetLogError("lamport must be int")
        rec["lamport"] = lamport
    if parents is not None:
        if not isinstance(parents, list):
            raise FleetLogError("parents must be a list")
        rec["parents"] = [str(x) for x in parents]'''
assert src.count(old_rec) == 1, "fleet_log rec anchor"
src = src.replace(old_rec, new_rec, 1)
p.write_text(src, encoding="utf-8")
print("fleet_log.py patched")

# --- 2. fleet_gossip.py ---
p = BASE / "fleet_gossip.py"
src = p.read_text(encoding="utf-8")

old_fn = '''def _recovered_text(channel: str, seq: int, rec: dict) -> tuple:
    """Render the recovered message file.  Content is a pure function of
    the log record -- no wall-clock -- so repeated backfills are
    byte-identical and idempotent.

    # backfill-fidelity: the log record carries only seq/ts/agent/type/
    body.  `to` defaults to "all", `status` is the honest marker
    "recovered", and `title` is derived from the record's type.  If
    fleet_log ever records optional to/title/reply_to fields, prefer
    them here and drop the -recovered suffixing.
    """
    agent = _one_line(rec.get("agent", "unknown"))
    rtype = _one_line(rec.get("type", "chat"))
    title = _one_line(f"{rtype}-recovered")
    fname = f"{seq:04d}-{_slugify(agent)}-{_slugify(title)}.md"
    fm = [
        "---",
        f"seq: {seq}",
        f"from: {agent}",
        "to: all",
        f"channel: {_one_line(channel)}",
        f"ts: {_one_line(rec.get('ts', ''))}",
        "status: recovered",
        f"title: {title}",
        "recovered_from: log.jsonl",
        "---",
        "",
    ]
    body = rec.get("body", "")
    if not isinstance(body, str):
        body = str(body)
    return fname, "\\n".join(fm) + body.rstrip("\\n") + "\\n"
'''
new_fn = '''def _recovered_text(channel: str, seq: int, rec: dict) -> tuple:
    """Render the recovered message file.  Content is a pure function of
    the log record -- no wall-clock -- so repeated backfills are
    byte-identical and idempotent.

    Fidelity: when the log record carries the original frontmatter fields
    plus ``msg_hmac`` (written by chat.py cmd_post), the recovered file is
    byte-identical to the lost original -- same status/title, same hmac:
    line -- so it passes HMAC verification on the read path.
    ``recovered_from: log.jsonl`` is NOT part of the HMAC canonical form,
    so the marker never breaks verification.  Records predating the
    fidelity fields fall back to the honest "-recovered" rendering, which
    is deliberately unverifiable (fail closed on the read path).
    """
    agent = _one_line(rec.get("agent", "unknown"))
    body = rec.get("body", "")
    if not isinstance(body, str):
        body = str(body)
    body = body.rstrip("\\n") + "\\n"
    if rec.get("msg_hmac"):
        to = _one_line(rec.get("to", "all"))
        title = _one_line(rec.get("title", ""))
        status = _one_line(rec.get("status", "discussion"))
        reply_to = rec.get("reply_to")
        lamport = rec.get("lamport", 0)
        parents = rec.get("parents") or []
        fname = f"{seq:04d}-{_slugify(agent)}-{_slugify(title)}.md"
        fm = [
            "---",
            f"seq: {seq}",
            f"from: {agent}",
            f"to: {to}",
        ]
        if reply_to:
            fm.append(f"reply_to: {_one_line(reply_to)}")
        fm += [
            f"channel: {_one_line(channel)}",
            f"ts: {_one_line(rec.get('ts', ''))}",
            f"status: {status}",
            f"title: {title}",
            f"lamport: {lamport}",
            f"parents: [{', '.join(str(x) for x in parents)}]",
            "recovered_from: log.jsonl",
            f"hmac: {rec['msg_hmac']}",
            "---",
            "",
        ]
        return fname, "\\n".join(fm) + body
    # Legacy fallback: pre-fidelity records. Honest marker, unverifiable.
    rtype = _one_line(rec.get("type", "chat"))
    title = _one_line(f"{rtype}-recovered")
    fname = f"{seq:04d}-{_slugify(agent)}-{_slugify(title)}.md"
    fm = [
        "---",
        f"seq: {seq}",
        f"from: {agent}",
        "to: all",
        f"channel: {_one_line(channel)}",
        f"ts: {_one_line(rec.get('ts', ''))}",
        "status: recovered",
        f"title: {title}",
        "recovered_from: log.jsonl",
        "---",
        "",
    ]
    return fname, "\\n".join(fm) + body
'''
assert src.count(old_fn) == 1, "fleet_gossip fn anchor"
src = src.replace(old_fn, new_fn, 1)
p.write_text(src, encoding="utf-8")
print("fleet_gossip.py patched")
