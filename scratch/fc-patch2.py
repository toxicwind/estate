import pathlib
p = pathlib.Path('/home/toxic/fc-ci-fix-2721520964/tests/test_chat.py')
src = p.read_text()
old = '''    def test_read_preserves_sequence_order_and_advances_cursor(self):
        """Unread messages are rendered in sequence order and advance the cursor."""
        channel = self._channel("general")
        (channel / "0002-bob-second.md").write_text(
            "---\\nseq: 2\\nfrom: bob\\nto: alice\\ntitle: Second\\n---\\nbody\\n",
            encoding="utf-8",
        )
        (channel / "0001-bob-first.md").write_text(
            "---\\nseq: 1\\nfrom: bob\\nto: alice\\ntitle: First\\n---\\nbody\\n",
            encoding="utf-8",
        )

        output = io.StringIO()'''
new = '''    def test_read_preserves_sequence_order_and_advances_cursor(self):
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
assert old in src, 'read-order test not found'
p.write_text(src.replace(old, new, 1))
print('read-order test rewritten')
