#!/usr/bin/env python3
"""Coordinator patch 14: wire fleet_e2ee into chat.py + fleet_delta.py.

Post:   priv-* bodies are Fernet-encrypted BEFORE HMAC signing. Disk
        (.md + log.jsonl) sees only ciphertext; the HMAC covers the
        ciphertext, so tampering breaks both layers.
Read:   HMAC is verified first (on ciphertext), then the body is
        decrypted for display. Fail closed on missing/wrong key.
Init:   priv-* channels provision their symmetric key at creation
        (leader-side); no key -> no private channel.
Digest: priv-* snippets are decrypted for the agent's own triage view
        (Fernet is authenticated, so this is safe); "(undecryptable)"
        on failure, never a raw token shown as content.
"""
from pathlib import Path

BASE = Path("/home/toxic/.shingle/chat")

# --- 1. fleet_identity.verify_on_read: return the verified body ---
p = BASE / "fleet_identity.py"
src = p.read_text(encoding="utf-8")
old = '''    """Verify a message file's hmac frontmatter field. Fail CLOSED.

    Returns the parsed frontmatter dict (with 'hmac' removed) when the
    signature checks out. Raises FleetIdentityError -- always naming the
    agent -- for: missing hmac field, unknown/empty sender, missing or
    malformed key, or digest mismatch (forgery/tampering).
    """'''
new = '''    """Verify a message file's hmac frontmatter field. Fail CLOSED.

    Returns the parsed frontmatter dict (with 'hmac' removed) plus the
    verified 'body' when the signature checks out. On priv-* channels the
    body is the ciphertext -- decrypt it only after this returns.
    Raises FleetIdentityError -- always naming the
    agent -- for: missing hmac field, unknown/empty sender, missing or
    malformed key, or digest mismatch (forgery/tampering).
    """'''
assert src.count(old) == 1, "identity docstring anchor"
src = src.replace(old, new, 1)
old = '''    meta = dict(meta)
    meta.pop("hmac", None)
    return meta'''
new = '''    meta = dict(meta)
    meta.pop("hmac", None)
    meta["body"] = body  # verified body (ciphertext on priv-* channels)
    return meta'''
assert src.count(old) == 1, "identity return anchor"
src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("fleet_identity.py: verify_on_read returns body")

# --- 2. chat.py ---
p = BASE / "chat.py"
src = p.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

rep(
    "import fleet_ephemeral\nimport fleet_gossip\nimport fleet_identity\n",
    "import fleet_e2ee\nimport fleet_ephemeral\nimport fleet_gossip\nimport fleet_identity\n",
)

# 2a. cmd_init: provision the channel key BEFORE any channel state exists.
rep(
    '''    if meta_path.exists():
        raise AgentChatError(f"channel '{a.channel}' already exists")
    members = [m.strip() for m in (a.members or "").split(",") if m.strip()]''',
    '''    if meta_path.exists():
        raise AgentChatError(f"channel '{a.channel}' already exists")
    # Fleet E2EE: priv-* channels get their symmetric key at creation.
    # Leader-side provisioning; members receive the key out of band.
    # Fail closed: no key, no private channel -- and this happens before
    # _meta.json is written, so a failed init leaves no half-made channel.
    if a.channel.startswith(fleet_e2ee.PRIV_PREFIX):
        try:
            fleet_e2ee.ensure_channel_key(a.channel)
        except Exception as e:
            die(f"cannot provision key for private channel '{a.channel}': {e}")
    members = [m.strip() for m in (a.members or "").split(",") if m.strip()]''',
)

# 2b. cmd_post: encrypt BEFORE signing, inside the seq lock.
rep(
    '''        # Fleet Lamport: tick the sender's clock; readers sort causally.
        lamport = fleet_time.tick(root, sender)
        fname = f"{seq:04d}-{slugify(a.sender)}-{slugify(a.title)}.md"''',
    '''        # Fleet Lamport: tick the sender's clock; readers sort causally.
        lamport = fleet_time.tick(root, sender)
        # Fleet E2EE: for priv-* channels, encrypt the body BEFORE signing
        # and persisting. What hits disk (.md + log.jsonl) is ciphertext;
        # the HMAC covers the ciphertext, so tampering breaks both layers.
        # Readers verify first, then decrypt for display. No key (or no
        # crypto lib) -> the post fails closed, never plaintext.
        if channel.startswith(fleet_e2ee.PRIV_PREFIX):
            try:
                body = fleet_e2ee.encrypt_message(channel, body)
            except Exception as e:
                die(f"cannot encrypt for private channel '{channel}': {e}")
        fname = f"{seq:04d}-{slugify(a.sender)}-{slugify(a.title)}.md"''',
)

# 2c. _print_message: decrypt priv-* bodies after verification.
rep(
    '''def _print_message(path: Path):
    print("=" * 70)
    try:
        print(path.read_text(encoding="utf-8").rstrip())
    except (OSError, UnicodeError) as e:
        print(f"(could not read message {path.name}: {e})")
    print()''',
    '''def _print_message(path: Path, meta: dict | None = None):
    """Print one message file. When the verified frontmatter `meta` is given
    and the channel is priv-*, the (already HMAC-verified) ciphertext body is
    decrypted for display. Fail closed: a missing/wrong channel key is a
    hard error, never a silent ciphertext dump or a skip."""
    print("=" * 70)
    try:
        text = path.read_text(encoding="utf-8").rstrip()
    except (OSError, UnicodeError) as e:
        print(f"(could not read message {path.name}: {e})")
        print()
        return
    if meta is not None and str(meta.get("channel", "")).startswith(
        fleet_e2ee.PRIV_PREFIX
    ):
        channel = meta["channel"]
        try:
            plaintext = fleet_e2ee.decrypt_message(channel, meta.get("body", ""))
        except Exception as e:
            die(
                f"cannot decrypt message {path.name} "
                f"in private channel '{channel}': {e}"
            )
        # Splice the plaintext in place of the ciphertext body: the body is
        # everything after the closing '---' line of the frontmatter.
        lines = text.split("\\n")
        try:
            close = lines.index("---", 1)
        except ValueError:
            close = len(lines) - 1
        text = "\\n".join(lines[: close + 1] + [plaintext.rstrip()])
    print(text)
    print()''',
)

# 2d. The three render call sites pass their verified meta.
for old_call in (
    "        _print_message(p)\n        shown += 1",
    "                _print_message(p)\n                delivered = True",
    "        _sender_cleared(meta)\n        _print_message(p)\n    if not files:",
):
    assert src.count(old_call) == 1, f"callsite anchor: {old_call[:50]!r}"
src = src.replace(
    "        _print_message(p)\n        shown += 1",
    "        _print_message(p, meta)\n        shown += 1",
    1,
)
src = src.replace(
    "                _print_message(p)\n                delivered = True",
    "                _print_message(p, meta)\n                delivered = True",
    1,
)
src = src.replace(
    "        _sender_cleared(meta)\n        _print_message(p)\n    if not files:",
    "        _sender_cleared(meta)\n        _print_message(p, meta)\n    if not files:",
    1,
)
print("ok: three _print_message call sites pass meta")
p.write_text(src, encoding="utf-8")
print("patch applied:", p)

# --- 3. fleet_delta.py: decrypt priv-* snippets in the digest ---
p = BASE / "fleet_delta.py"
src = p.read_text(encoding="utf-8")

def rep2(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

rep2(
    "import chat  # noqa: E402  -- reuse base primitives, do not re-implement",
    "import chat  # noqa: E402  -- reuse base primitives, do not re-implement\n"
    "import fleet_e2ee  # noqa: E402  -- decrypt priv-* digest snippets",
)

rep2(
    '''def _body_snippet(path: Path, limit: int = DIGEST_BODY_LIMIT) -> str:
    """First `limit` chars of the message body (text after the frontmatter),
    whitespace-collapsed. The base has no body extractor, so this one lives
    here. Bodies on priv-* channels are ciphertext (fleet_e2ee); the snippet
    stays opaque, never a plaintext leak."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return "(unreadable)"
    lines = text.splitlines()
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                body_start = i + 1
                break
    body = " ".join(" ".join(lines[body_start:]).split())
    if len(body) > limit:
        return body[:limit] + "..."
    return body''',
    '''def _body_snippet(
        path: Path, limit: int = DIGEST_BODY_LIMIT, channel: str = ""
    ) -> str:
    """First `limit` chars of the message body (text after the frontmatter),
    whitespace-collapsed. The base has no body extractor, so this one lives
    here. On priv-* channels the stored body is ciphertext (fleet_e2ee): it
    is Fernet-decrypted for the agent's own triage view (Fernet is
    authenticated encryption, so decrypting is tamper-safe); on any decrypt
    failure the snippet reads "(undecryptable)" -- ciphertext is never shown
    as if it were content, and plaintext never leaks to disk."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return "(unreadable)"
    lines = text.splitlines()
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                body_start = i + 1
                break
    body = "\\n".join(lines[body_start:])
    if channel.startswith(fleet_e2ee.PRIV_PREFIX):
        try:
            body = fleet_e2ee.decrypt_message(channel, body.strip())
        except Exception:
            return "(undecryptable)"
    body = " ".join(body.split())
    if len(body) > limit:
        return body[:limit] + "..."
    return body''',
)

rep2(
    "            snippet = _body_snippet(path)",
    "            snippet = _body_snippet(path, channel=channel)",
)
p.write_text(src, encoding="utf-8")
print("patch applied:", p)
