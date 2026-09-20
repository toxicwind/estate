import pathlib
p = pathlib.Path('/home/toxic/fc-ci-fix-2721520964/tests/test_chat.py')
src = p.read_text()
old = '''    def test_read_preserves_sequence_order_and_advances_cursor(self):
        """Unread messages are rendered in sequence order and advance the cursor."""
        channel = self._channel("general")
        # Post through the real (HMAC-signing) path, then scramble filenames
        # so on-disk order disagrees with sequence order. The read path must
        # still render by seq and verify signatures (unsigned hand-written
        # files are rejected by verify_on_read).
        chat.cmd_post(self.root, self._post_args(sender="bob", to="alice", title="First"))
        chat.cmd_post(self.root, self._post_args(sender="bob", to="alice", title="Second"))
        first, second = sorted(channel.glob("*.md"))
        first.rename(channel / "tmp-swap.md")
        second.rename(first)
        (channel / "tmp-swap.md").rename(second)

        output = io.StringIO()'''
new = '''    def _write_signed(self, channel, filename, seq, sender, to, title, body="body"):
        """Hand-write a message file with a valid v1 HMAC.

        Lets tests control on-disk layout (e.g. seq-out-of-order filenames)
        while satisfying verify_on_read's fail-closed signature check.
        """
        ts = "2026-09-14T00:00:00+00:00"
        canon = fleet_identity.canonical_message(
            seq=seq, sender=sender, to=to, reply_to="", channel="general",
            ts=ts, status="discussion", title=title, body=body,
        )
        hmac = fleet_identity.sign(sender, canon)
        (channel / filename).write_text(
            f"---\\nseq: {seq}\\nfrom: {sender}\\nto: {to}\\nchannel: general\\n"
            f"ts: {ts}\\nstatus: discussion\\ntitle: {title}\\n"
            f"hmac: {hmac}\\n---\\n{body}\\n",
            encoding="utf-8",
        )

    def test_read_preserves_sequence_order_and_advances_cursor(self):
        """Unread messages are rendered in sequence order and advance the cursor."""
        channel = self._channel("general")
        # Written out of order on disk; the read path must still render by
        # seq (parsed from the filename) and verify each signature.
        self._write_signed(channel, "0002-bob-second.md", 2, "bob", "alice", "Second")
        self._write_signed(channel, "0001-bob-first.md", 1, "bob", "alice", "First")

        output = io.StringIO()'''
assert old in src, 'read-order test not found'
src = src.replace(old, new, 1)
# ensure fleet_identity is imported
if 'import fleet_identity' not in src:
    src = src.replace('import chat', 'import chat\nimport fleet_identity', 1)
p.write_text(src)
print('read-order test rewritten with signed messages')
