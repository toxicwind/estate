#!/usr/bin/env python3
"""fleet_identity v3: HMAC-cover relay metadata (relayed_from/human).

Tampering with relayed_from/human on a v3 message invalidates the
signature; verify_on_read falls back to v2/v1 for pre-upgrade messages.
Also: chat.py signs v3 when relay metadata is present; fleet_relay drops
relay metadata that is not HMAC-covered (untrusted attribution).

Usage: python3 identity_v3.py   (runs in the squawk repo root)
"""

from pathlib import Path


def rep(src: str, old: str, new: str, name: str, count: int = 1) -> str:
    n = src.count(old)
    if n != count:
        raise SystemExit(f"EDIT {name}: expected {count}, found {n}")
    return src.replace(old, new)


root = Path("/home/toxic/squawk-relay-5f9a2c")

# ---------------------------------------------------------------- fleet_identity.py
p = root / "fleet_identity.py"
src = p.read_text(encoding="utf-8")

src = rep(
    src,
    'CANONICAL_V1 = "fleet-chat-v1"\nCANONICAL_V2 = "fleet-chat-v2"\n',
    'CANONICAL_V1 = "fleet-chat-v1"\nCANONICAL_V2 = "fleet-chat-v2"\n'
    'CANONICAL_V3 = "fleet-chat-v3"\n',
    "I1-const",
)

src = rep(
    src,
    """    lamport=None,
    parents=None,
) -> bytes:""",
    """    lamport=None,
    parents=None,
    relayed_from=None,
    human=None,
) -> bytes:""",
    "I2-sig",
)

src = rep(
    src,
    """    DAG id uses sorted set semantics -- different schemes, different rules.
    \"\"\"""",
    """    DAG id uses sorted set semantics -- different schemes, different rules.

    v3: pass relayed_from and/or human and the bytes become v3
    ("fleet-chat-v3" tag plus "relayed_from:" / "human:" lines after
    "parents:"). Relay metadata is HMAC-covered: stripping or altering
    relayed_from/human on a v3 message invalidates the signature, exactly
    like tampering with any other covered field. verify_on_read tries v3,
    then v2, then v1, so pre-upgrade messages keep verifying.
    \"\"\"""",
    "I3-doc",
)

src = rep(
    src,
    """    plamport = int(lamport) if lamport is not None else 0
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
    return ("\\n".join(lines) + "\\n").encode("utf-8")""",
    """    plamport = int(lamport) if lamport is not None else 0
    pparents = [str(x) for x in (parents or [])]
    if relayed_from is None and human is None:
        tag = CANONICAL_V2
        extra = []
    else:
        # v3: relay attribution is part of the signed payload.
        tag = CANONICAL_V3
        extra = [
            f"relayed_from: {_one_line(relayed_from or '')}",
            f"human: {_one_line(human or '')}",
        ]
    lines = [
        tag,
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
        *extra,
    ]
    return ("\\n".join(lines) + "\\n").encode("utf-8")""",
    "I4-v3branch",
)

src = rep(
    src,
    """    v2 = canonical_message(
        **base_fields, lamport=lamport_i, parents=_parse_parents(meta.get("parents"))
    )
    if verify(sender, v2, hmac_hex, kd):
        verified_version = "v2"
    elif verify(sender, canonical_message(**base_fields), hmac_hex, kd):
        # Pre-upgrade message: signed before lamport/parents were covered.
        # Safe fallback -- a v2 HMAC can never verify as v1, so stripping or
        # tampering the new fields on a v2 message is still rejected here.
        verified_version = "v1"
    else:""",
    """    v2 = canonical_message(
        **base_fields, lamport=lamport_i, parents=_parse_parents(meta.get("parents"))
    )
    # v3: relay metadata is HMAC-covered when present. A v3 HMAC can never
    # verify as v2/v1 (different tag + extra lines), so stripping or
    # altering relayed_from/human on a v3 message is rejected below.
    rf = meta.get("relayed_from")
    hm = meta.get("human")
    if (rf is not None or hm is not None) and verify(
        sender,
        canonical_message(
            **base_fields,
            lamport=lamport_i,
            parents=_parse_parents(meta.get("parents")),
            relayed_from=rf,
            human=hm,
        ),
        hmac_hex,
        kd,
    ):
        verified_version = "v3"
    elif verify(sender, v2, hmac_hex, kd):
        verified_version = "v2"
    elif verify(sender, canonical_message(**base_fields), hmac_hex, kd):
        # Pre-upgrade message: signed before lamport/parents were covered.
        # Safe fallback -- a v2 HMAC can never verify as v1, so stripping or
        # tampering the new fields on a v2 message is still rejected here.
        verified_version = "v1"
    else:""",
    "I5-verify",
)
p.write_text(src, encoding="utf-8")
print("fleet_identity.py: v3 wired (I1-I5)")

# ---------------------------------------------------------------- chat.py
p = root / "chat.py"
src = p.read_text(encoding="utf-8")
src = rep(
    src,
    """                # v2: lamport + parents are HMAC-covered (both in scope
                # under the seq lock, computed just above).
                lamport=lamport,
                parents=parents,
            ),""",
    """                # v2: lamport + parents are HMAC-covered (both in scope
                # under the seq lock, computed just above).
                lamport=lamport,
                parents=parents,
                # v3: relay metadata is HMAC-covered when present, so
                # tampering with relayed_from/human invalidates the sig.
                relayed_from=(extra_frontmatter or {}).get("relayed_from"),
                human=(extra_frontmatter or {}).get("human"),
            ),""",
    "C1-sign",
)
p.write_text(src, encoding="utf-8")
print("chat.py: v3 sign wired (C1)")

# ---------------------------------------------------------------- fleet_relay.py
p = root / "fleet_relay.py"
src = p.read_text(encoding="utf-8")
src = rep(
    src,
    '''    rec["body"] = verified.get("body", "")
    rec["hmac_version"] = verified.get("hmac_version")
''',
    '''    rec["body"] = verified.get("body", "")
    rec["hmac_version"] = verified.get("hmac_version")
    if (rec["relayed_from"] is not None or rec["human"] is not None) \\
            and rec["hmac_version"] != "v3":
        # Relay metadata present but NOT HMAC-covered: a pre-v3 message
        # carrying unsigned frontmatter, or tampering. Attribution fails
        # closed -- the fields are dropped; the signature verdict stands.
        rec["relayed_from"] = None
        rec["human"] = None
''',
    "R1-trustgate",
)
p.write_text(src, encoding="utf-8")
print("fleet_relay.py: untrusted-attribution gate wired (R1)")

print("OK: identity v3 complete")
