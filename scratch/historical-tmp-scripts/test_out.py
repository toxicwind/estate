#!/usr/bin/env python3
"""Tests for seq_alloc: monotonic allocation across deletions, concurrency.

Run: python3 -m pytest tests/test_seq_alloc.py -q   (or plain python3)
"""
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import seq_alloc


def _msg(root: Path, channel: str, seq: int, sender: str = "tester") -> Path:
    d = root / channel
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{seq}-{sender}-msg.md"
    p.write_text("---\nseq: %d\nfrom: %s\n---\nhello\n" % (seq, sender))
    return p


class TestSeqAlloc(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
    def test_fresh_channel_starts_above_disk(self):
        for s in (3, 7, 12):
            _msg(self.root, "fleet", s)
        self.assertEqual(seq_alloc.alloc_seq(self.root, "fleet"), 13)

    def test_monotonic_across_deletion(self):
        # the 2026-09-21 regression: files deleted, allocator must NOT
        # reuse the dead numbers.
        for s in range(1, 7):
            _msg(self.root, "fleet", s)
        self.assertEqual(seq_alloc.alloc_seq(self.root, "fleet"), 7)
        # delete the top files (simulating the 12811-12816 loss)
        for s in (5, 6, 7):
            p = self.root / "fleet" / f"{s}-tester-msg.md"
            if p.exists():
                p.unlink()
        # disk max is now 4; allocator must still go above 7
        self.assertEqual(seq_alloc.alloc_seq(self.root, "fleet"), 8)
        self.assertEqual(seq_alloc.alloc_seq(self.root, "fleet"), 9)

    def test_wiped_high_file_falls_back_to_disk(self):
        for s in (1, 2, 3):
            _msg(self.root, "fleet", s)
        self.assertEqual(seq_alloc.alloc_seq(self.root, "fleet"), 4)
        (self.root / ".seqhigh-fleet").unlink()
        # operator wiped the mark: safe fallback is disk+1 (old behavior),
        # never below what is on disk.
        self.assertEqual(seq_alloc.alloc_seq(self.root, "fleet"), 4)

    def test_seed_floor(self):
        for s in (1, 2):
            _msg(self.root, "fleet", s)
        # floor above everything ever seen (e.g. 12816 observed live but
        # since deleted from disk)
        self.assertEqual(seq_alloc.seed_high(self.root, "fleet", 12816), 12816)
        self.assertEqual(seq_alloc.read_high(self.root, "fleet"), 12816)
        self.assertEqual(seq_alloc.alloc_seq(self.root, "fleet"), 12817)
        # seeding below the mark never lowers it
        self.assertEqual(seq_alloc.seed_high(self.root, "fleet", 5), 12817)

    def test_disk_high_ignores_non_messages(self):
        d = self.root / "fleet"
        d.mkdir(parents=True, exist_ok=True)
        (d / "_meta.json").write_text("{}")
        (d / "log.jsonl").write_text("{}\n")
        (d / "notes.md").write_text("no seq prefix")
        (d / "repair.sh-20260921T172410Z.md").write_text("x")
        _msg(self.root, "fleet", 65)  # placeholder name replaced below
        (d / "65-tester-msg.md").unlink()
        (d / "0065-tester-msg.md").write_text("---\nseq: 65\n---\nx\n")
        self.assertEqual(seq_alloc.disk_high(d), 65)
        self.assertEqual(seq_alloc.alloc_seq(self.root, "fleet"), 66)

    def test_concurrent_alloc_unique_and_ordered(self):
        for s in range(1, 4):
            _msg(self.root, "fleet", s)
        got = []
        lock = threading.Lock()

        def worker(n):
            for _ in range(n):
                s = seq_alloc.alloc_seq(self.root, "fleet")
            with lock:
                    got.append(s)

        threads = [threading.Thread(target=worker, args=(10,))
for _ in range(16)]
        for t in threads:
            t.tart()
        for t in threads:
            t.join()
        self.assertEqual(len(got), 160)
        self.assertEqual(len(set(got)), 160, "duplicate seq allocated!")
        self.assertEqual(sorted(got), list(range(4, 164)))

    def test_cli_entrypoint(self):
        import subprocess

        out = subprocesrç'Vâ€¢·7—2æW†V7WF&ÆRÂ7G"…F‚‡6WöÆÆö2åõöf–ÆUõò’’Â7G"‡6VÆbç&ö÷B’Â&fÆVWB%ÒÀ¢6GW&Uö÷WGWCÕG'VRÂFW‡CÕG'VRÂF–ÖV÷WCÓ3À¢¢6VÆbæ76W'DWVÂ†÷WBç&WGW&æ6öFRÂÂ÷WBç7FFW'"¢6VÆbæ76W'DWVÂ†÷WBç7FF÷WBç7G&—‚’Â#"¢÷WBÒ7V'&ö6W72ç'Vâ€¢·7—2æW†V7WF&ÆRÂ7G"…F‚‡6WöÆÆö2åõöf–ÆUõò’’À¢"Ò×6VVB"Â7G"…Í•±˜¹É½½Ğ¤°€‰™±••Ğˆ°€ˆĞÄ‰t°(€€€€€€€€€€€…ÁÑÕÉ•}½ÕÑÁÕĞõQÉÕ”°Ñ•áĞõQÉÕ”°Ñ¥µ•½ÕĞôÌÀ°(€€€€€€€€¤(€€€€€€€Í•±˜¹…ÍÍ•ÉÑÅÕ…°¡½ÕĞ¹É•ÑÕÉ¹½‘”°€À°½ÕĞ¹ÍÑ‘•ÉÈ¤(€€€€€€€Í•±˜¹…ÍÍ•ÉÑÅÕ…°¡½ÕĞ¹ÍÑ‘½ÕĞ¹ÍÑÉ¥À ¤°€ˆĞÄˆ¤(()¥˜}}¹…µ•}|€ôô€‰}}µ…¥¹}|ˆè(€€€Õ¹¥ÑÑ•ÍĞ¹µ…¥¸¡Ù•É‰½Í¥ÑäôÈ¤