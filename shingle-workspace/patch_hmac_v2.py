#!/usr/bin/env python3
"""Coordinator patch 15: HMAC canonical v2 -- sign lamport + parents.

Gap: lamport:/parents: were added to posts after the v1 canonical HMAC
format, so a file editor could alter them without invalidating the HMAC.

v2: canonical_message(..., lamport=N, parents=[...]) appends
    "lamport: N" and "parents: [a, b]" lines and tags the bytes
    "fleet-chat-v2". Called WITHOUT lamport/parents it emits the exact v1
    bytes (fleet_dag's msg_id scheme depends on v1 stability -- unchanged).
verify_on_read: tries v2 first, falls back to v1 for pre-upgrade messages.
    The fallback is safe: a v2 HMAC can never verify as v1, so stripping
    or tampering the new fields is always rejected.
cmd_post: signs v2 (lamport + parents are in scope under the seq lock).
sign_archive_file: migrates to v2 when the file carries the fields.
"""
from pathlib import Path

BASE = Path("/home/toxic/.shingle/chat")

# --- 1. fleet_identity.py ---
p = BASE / "fleet_identity.py"
src = p.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

rep(
    'CANONICAL_VERSION = "fleet-chat-v1"',
    '''CANONICAL_V1 = "fleet-chat-v1"
CANONICAL_V2 = "fleet-chat-v2"
# Back-compat alias: the v1 tag keeps its old name wherever it was imported.
CANONICAL_VERSION = CANONICAL_V1''',
)

rep(
    """    canonical_message(*, seq, sender, to, reply_to, channel, ts, status,
                      title, body) -> bytes""",
    """    canonical_message(*, seq, sender, to, reply_to, channel, ts, status,
                      title, body, lamport=None, parents=None) -> bytes
        v1 when lamport/parents are omitted (default); v2 covers them when
        given. verify_on_read tries v2, then v1 for pre-upgrade messages.""",
)

rep(
    '''def canonical_message(
    *,
    seq,
    sender,
    to,
    reply_to,
    channel,
    ts,
    status,
    title,
    body,
) -> bytes:
    """Build the canonical byte string that gets HMAC-signed.

    Field order is fixed; every line ends with \\\\n including the last.
    The body is covered only via its SHA-256 digest (see module docstring).
    """
    digest = hashlib.sha256(_norm_body(body).encode("utf-8")).hexdigest()
    lines = [
        CANONICAL_VERSION,
        f"seq: {int(seq)}",
        f"from: {_one_line(sender)}",
        f"to: {_one_line(to)}",
        f"reply_to: {_one_line(reply_to or '')}",
        f"channel: {_one_line(channel)}",
        f"ts: {_one_line(ts)}",
        f"status: {_one_line(status)}",
        f"title: {_one_line(title)}",
        f"body-sha256: {digest}",
    ]
    return ("\\n".join(lines) + "\\n").encode("utf-8")''',
    '''def _parse_parents(raw: object) -> list[str]:
    """Parse a 'parents: [a, b]' frontmatter value back to a list.

    Inverse of the canonical v2 rendering below; tolerant of spacing.
    Parent ids are hex, so neither commas nor brackets can appear inside one.
    """
    s = str(raw or "").strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [p.strip() for p in s.split(",") if p.strip()]


def canonical_message(
    *,
    seq,
    sender,
    to,
    reply_to,
    channel,
    ts,
    status,
    title,
    body,
    lamport=None,
    parents=None,
) -> bytes:
    """Build the canonical byte string that gets HMAC-signed.

    Field order is fixed; every line ends with \\\\n including the last.
    The body is covered only via its SHA-256 digest (see module docstring).

    v1 vs v2: omit lamport/parents (the default) and the bytes are the exact
    v1 form ("fleet-chat-v1", no new lines) -- fleet_dag's msg_id scheme
    hashes these bytes, so v1 stability is load-bearing. Pass lamport and
    parents and the bytes become v2 ("fleet-chat-v2" tag plus "lamport:" /
    "parents:" lines after "body-sha256:"). Parents render in file order
    (NOT sorted): the HMAC must match the file's bytes exactly, whereas the
    DAG id uses sorted set semantics -- different schemes, different rules.
    """
    digest = hashlib.sha256(_norm_body(body).encode("utf-8")).hexdigest()
    if lamport is None and parents is None:
        lines = [
            CANONICAL_V1,
            f"seq: {int(seq)}",
            f"from: {_one_line(sender)}",
            f"to: {_one_line(to)}",
            f"reply_to: {_one_line(reply_to or '')}",
            f"channel: {_one_line(channel)}",
            f"ts: {_one_line(ts)}",
            f"status: {_one_line(status)}",
            f"title: {_one_line(title)}",
            f"body-sha256: {digest}",
        ]
        return ("\\n".join(lines) + "\\n").encode("utf-8")
    plamport = int(lamport) if lamport is not None else 0
    pparents = [str(x) for x in (parents or [])]
    lines = [
        CANONICAL_V2,
        f"seq: {int(seq)}",
        f"from: {_one_line(sender)}",
        f"to: {_one_line(to)}",
        f"reply_to: {_one_line(reply_to or '')}",
        f"channel: {_one_line(channel)}",
        f"ts: {_one_line(ts)}",
        f"status: {_one_line(status)}",
        f"title: {_one_line(title)}",
        f"body-sha256: {digest}",
        f"lamport: {plamport}",
        f"parents: [{', '.join(pparents)}]",
    ]
    return ("\\n".join(lines) + "\\n").encode("utf-8")''',
)

# verify_on_read: v2 first, v1 fallback for pre-upgrade messages.
rep(
    '''    canonical = canonical_message(
        seq=meta.get("seq", "0"),
        sender=sender,
        to=meta.get("to", ""),
        reply_to=meta.get("reply_to", ""),
        channel=meta.get("channel", ""),
        ts=meta.get("ts", ""),
        status=meta.get("status", ""),
        title=meta.get("title", ""),
        body=body,
    )
    if not verify(sender, canonical, hmac_hex, kd):
        raise FleetIdentityError(
            f"message {path.name}: REJECTED -- hmac mismatch for agent '{sender}' "
            f"(seq {meta.get('seq', '?')}: forged or tampered)"
        )''',
    '''    base_fields = dict(
        seq=meta.get("seq", "0"),
        sender=sender,
        to=meta.get("to", ""),
        reply_to=meta.get("reply_to", ""),
        channel=meta.get("channel", ""),
        ts=meta.get("ts", ""),
        status=meta.get("status", ""),
        title=meta.get("title", ""),
        body=body,
    )
    # v2: lamport + parents are covered. Unparseable/missing values degrade
    # to the v2 defaults for this attempt; a genuine v2 signature still has
    # to match, otherwise we fall through to the v1 check below.
    try:
        lamport_i = int(str(meta.get("lamport", "") or "0").strip())
    except (TypeError, ValueError):
        lamport_i = 0
    v2 = canonical_message(
        **base_fields, lamport=lamport_i, parents=_parse_parents(meta.get("parents"))
    )
    if verify(sender, v2, hmac_hex, kd):
        verified_version = "v2"
    elif verify(sender, canonical_message(**base_fields), hmac_hex, kd):
        # Pre-upgrade message: signed before lamport/parents were covered.
        # Safe fallback -- a v2 HMAC can never verify as v1, so stripping or
        # tampering the new fields on a v2 message is still rejected here.
        verified_version = "v1"
    else:
        raise FleetIdentityError(
            f"message {path.name}: REJECTED -- hmac mismatch for agent '{sender}' "
            f"(seq {meta.get('seq', '?')}: forged or tampered)"
        )
    meta = dict(meta)
    meta.pop("hmac", None)
    meta["body"] = body  # verified body (ciphertext on priv-* channels)
    meta["hmac_version"] = verified_version
    return meta''',
)

# Remove the old tail of verify_on_read (now subsumed by the v2/v1 block above,
# which returns directly).
rep(
    '''    meta = dict(meta)
    meta.pop("hmac", None)
    meta["body"] = body  # verified body (ciphertext on priv-* channels)
    return meta
''',
    "",
)

# sign_archive_file: migrate to v2 when the file carries the fields.
rep(
    '''    canonical = canonical_message(
        seq=meta.get("seq", "0"),
        sender=sender,
        to=meta.get("to", ""),
        reply_to=meta.get("reply_to", ""),
        channel=meta.get("channel", ""),
        ts=meta.get("ts", ""),
        status=meta.get("status", ""),
        title=meta.get("title", ""),
        body=body,
    )
    sig = sign(sender, canonical, kd)''',
    '''    # Migration signs the current (v2) form when the file carries
    # lamport/parents, else the legacy v1 form -- matching what
    # verify_on_read will check.
    try:
        lamport_i = int(str(meta.get("lamport", "") or "0").strip())
    except (TypeError, ValueError):
        lamport_i = 0
    if "lamport" in meta or "parents" in meta:
        canonical = canonical_message(
            seq=meta.get("seq", "0"),
            sender=sender,
            to=meta.get("to", ""),
            reply_to=meta.get("reply_to", ""),
            channel=meta.get("channel", ""),
            ts=meta.get("ts", ""),
            status=meta.get("status", ""),
            title=meta.get("title", ""),
            body=body,
            lamport=lamport_i,
            parents=_parse_parents(meta.get("parents")),
        )
    else:
        canonical = canonical_message(
            seq=meta.get("seq", "0"),
            sender=sender,
            to=meta.get("to", ""),
            reply_to=meta.get("reply_to", ""),
            channel=meta.get("channel", ""),
            ts=meta.get("ts", ""),
            status=meta.get("status", ""),
            title=meta.get("title", ""),
            body=body,
        )
    sig = sign(sender, canonical, kd)''',
)
p.write_text(src, encoding="utf-8")
print("patch applied:", p)

# --- 2. chat.py cmd_post: sign v2 ---
p = BASE / "chat.py"
src = p.read_text(encoding="utf-8")
old = """        sig = fleet_identity.sign(
            sender,
            fleet_identity.canonical_message(
                seq=seq,
                sender=sender,
                to=to,
                reply_to=reply,
                channel=channel,
                ts=timestamp,
                status=status,
                title=title,
                body=body,
            ),
        )"""
new = """        sig = fleet_identity.sign(
            sender,
            fleet_identity.canonical_message(
                seq=seq,
                sender=sender,
                to=to,
                reply_to=reply,
                channel=channel,
                ts=timestamp,
                status=status,
                title=title,
                body=body,
                # v2: lamport + parents are HMAC-covered (both in scope
                # under the seq lock, computed just above).
                lamport=lamport,
                parents=parents,
            ),
        )"""
assert src.count(old) == 1
src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("patch applied:", p)
