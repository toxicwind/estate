#!/usr/bin/env python3
"""canonical_post: signed-post adapter over the CANONICAL squawk chat tree.

The relay forwarder must sign with the same code every reader verifies.
The stale mesh checkout (SQUAWK_CODE=/home/toxic/squawk) signs a v3
canonical form (relayed_from/human HMAC-covered) that the canonical
fleet_identity (v1/v2 only) rejects -> every relayed message fail-closed
fleet reads. This adapter exposes the mesh chat_commands._post_message
call signature but signs the canonical v2 form: relay metadata
(relayed_from/human/relay_key) is still written as frontmatter (dedup
and attribution depend on it) but is NOT HMAC-covered -- exactly what
canonical verify_on_read checks.

Import after inserting the canonical chat dir at sys.path[0]:
    sys.path.insert(0, os.environ["SQUAWK_CODE_DIR"])  # .../ember/chat
    import canonical_post
"""
import os
import sys
from pathlib import Path

import chat as _chat
import fleet_crdt
import fleet_e2ee
import fleet_identity
import fleet_log
import fleet_time


def resolve_key_dir(root):
    """Keys dir: $FLEET_KEYS_DIR > <root>/keys > canonical default.

    Mirrors the old mesh fleet_relay.resolve_key_dir preference so the
    forwarder keeps finding the relay key next to the chat root.
    """
    env = os.environ.get("FLEET_KEYS_DIR")
    if env:
        return Path(env)
    cand = Path(root) / "keys"
    if cand.is_dir():
        return cand
    return fleet_identity.keys_dir()


def ensure_keys_env(root):
    """Make FLEET_KEYS_DIR resolve for any import-time readers.

    Never overrides an explicit setting.
    """
    if "FLEET_KEYS_DIR" not in os.environ:
        os.environ["FLEET_KEYS_DIR"] = str(resolve_key_dir(root))


def _post_message(root: Path, channel: str, *, body: str, sender: str,
                  to: str = "all", reply=None, status: str = "discussion",
                  title: str = "", extra_frontmatter: dict | None = None,
                  key_dir=None) -> tuple[int, str]:
    """The shared signed/sequenced post path -- canonical v2 edition.

    Sequence lock, DAG parents, Lamport tick, priv-* E2EE, HMAC-SHA256
    (v2: lamport+parents covered; relay metadata NOT covered), .md write,
    log.jsonl append, CRDT op -- everything canonical cmd_post does, in
    one place, plus extra_frontmatter lines rendered after the standard
    fields (before hmac), exactly like the old mesh path did.

    Returns (seq, filename).
    """
    d = _chat.require_channel(root, channel)
    sender = _chat._frontmatter_value(sender)
    to = _chat._frontmatter_value(to or "all")
    reply = _chat._frontmatter_value(reply) if reply else None
    channel = _chat._frontmatter_value(channel)
    timestamp = _chat._frontmatter_value(_chat.now_iso())
    status = _chat._frontmatter_value(status)
    title = _chat._frontmatter_value(title)
    lock = _chat._acquire_lock(d)
    try:
        seq = _chat._next_seq(d)
        # Fleet DAG: parent ids, computed under the seq lock (race-free).
        parents = _chat._dag_parents(d, seq, reply)
        # Fleet Lamport: tick the senders clock; readers sort causally.
        lamport = fleet_time.tick(root, sender)
        # Fleet E2EE: for priv-* channels, encrypt the body BEFORE signing
        # and persisting. The HMAC covers the ciphertext.
        if channel.startswith(fleet_e2ee.PRIV_PREFIX):
            try:
                body = fleet_e2ee.encrypt_message(channel, body)
            except Exception as e:
                _chat.die(f"cannot encrypt for private channel {channel!r}: {e}")
        fname = f"{seq:04d}-{_chat.slugify(sender)}-{_chat.slugify(title)}.md"
        fm = [
            "---",
            f"seq: {seq}",
            f"from: {sender}",
            f"to: {to}",
        ]
        if reply is not None:
            fm.append(f"reply_to: {reply}")
        # Fleet identity: HMAC-sign the canonical v2 message bytes.
        # sign() raises FleetIdentityError when the sender has no key ->
        # the post fails closed. Relay metadata is frontmatter only;
        # covering it (v3) is what broke fleet reads -- never do that here.
        sig = fleet_identity.sign(
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
                lamport=lamport,
                parents=parents,
            ),
            kd=key_dir,
        )
        if extra_frontmatter:
            for _rk, _rv in extra_frontmatter.items():
                fm.append(f"{_rk}: {_chat._frontmatter_value(_rv)}")
        fm += [
            f"channel: {channel}",
            f"ts: {timestamp}",
            f"status: {status}",
            f"title: {title}",
            f"lamport: {lamport}",
            f"parents: [{', '.join(parents)}]",
            f"hmac: {sig}",
            "---",
            "",
        ]
        (d / fname).write_text("\n".join(fm) + body.rstrip() + "\n", encoding="utf-8")
        # Fleet log: parallel append-only JSONL index. Never fails the post.
        try:
            fleet_log.append(
                root,
                channel,
                seq=seq,
                agent=sender,
                type="message",
                body=body,
                ts=timestamp,
                # Fidelity fields: let anti-entropy backfill reconstruct a
                # byte-identical, HMAC-verifiable message file.
                msg_hmac=sig,
                to=to,
                title=title,
                reply_to=reply,
                status=status,
                lamport=lamport,
                parents=parents,
            )
        except Exception as e:  # noqa: BLE001 -- the index must not break posts
            print(f"(warning: log.jsonl append failed: {e})", file=sys.stderr)
    finally:
        _chat._release_lock(lock)
    # Fleet CRDT: the post is a commutative operation.
    _chat._record_op(root, channel, fleet_crdt.POST, sender, lamport, {"seq": seq})
    print(f"posted #{seq} -> {channel}/{fname}")
    return seq, fname
