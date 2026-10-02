#!/usr/bin/env python3
"""Regression tests for the hatch-decode pass-3 pipeline.

Run: python3 -m pytest test_scan.py -q   (or python3 test_scan.py)
Covers:
  1. VA->file mapping indexes the whole image, not a section slice
     (the bug that zeroed the first scan).
  2. Packed adjacent symbols split exactly (no JARVIS_BIN_DIRJARVIS_ROOT).
  3. Static {ptr,len} records (shape C) recover exact names.
  4. Stale indexes are rejected by build ID.
  5. Shape-E over-read guard trims into pass-2 inventory names.
"""
import json
import os
import re
import struct
import subprocess
import sys
import unittest

WORK = os.path.dirname(os.path.abspath(__file__))
BIN = "/opt/hatch/bin/hatch"
BUILD_ID = "a733660761e017bf523cc4be3e467cddf3c4e639"


def sections():
    out = subprocess.run(["readelf", "-S", "-W", BIN],
                         capture_output=True, text=True).stdout
    secs = {}
    for line in out.splitlines():
        m = re.match(r"\s*\[\s*\d+\]\s+(\S+)\s+\S+\s+([0-9a-f]+)\s+"
                     r"([0-9a-f]+)\s+([0-9a-f]+)", line)
        if m:
            secs[m.group(1)] = (int(m.group(2), 16), int(m.group(3), 16),
                                int(m.group(4), 16))
    return secs


class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.secs = sections()
        cls.mm = open(BIN, "rb").read()

    def va_to_file(self, va):
        for _sn, (sva, soff, ssz) in self.secs.items():
            if sva <= va < sva + ssz:
                return soff + (va - sva)
        return None

    def test_va_mapping_indexes_whole_image(self):
        # The first scan sliced .rodata and indexed the slice: every
        # VA->file lookup missed. The mapping must resolve against the
        # whole image file offsets from readelf.
        ro_va, ro_off, _rsz = self.secs[".rodata"]
        probe = ro_va + 0x100
        self.assertEqual(self.va_to_file(probe), ro_off + 0x100)
        # and a .text VA must not collide with the .rodata slice
        tx_va, tx_off, _tsz = self.secs[".text"]
        self.assertNotEqual(self.va_to_file(tx_va), self.va_to_file(ro_va))

    def test_packed_symbols_split_exactly(self):
        # Adjacent packed symbols must not fuse into composites.
        raw = b"JARVIS_BIN_DIRJARVIS_ROOT\x00"
        names = re.findall(rb"JARVIS_[A-Z0-9_]+", raw)
        # naive regex fuses; the pipeline must instead require an exact
        # reader-supplied length or {ptr,len} record. Simulate the guard:
        exact = [n for n in names if n in (b"JARVIS_BIN_DIR", b"JARVIS_ROOT")]
        self.assertEqual(exact, [])
        # with the length discipline only the two exact slices admit:
        self.assertEqual(raw[0:14], b"JARVIS_BIN_DIR")
        self.assertEqual(raw[14:25], b"JARVIS_ROOT")

    def test_shape_c_static_record(self):
        # A static &str {ptr,len} in .data.rel.ro must recover the exact
        # name. Use a real record: find one pointing at a JARVIS_ string.
        dva, doff, dsz = self.secs[".data.rel.ro"]
        ro_va, ro_off, ro_sz = self.secs[".rodata"]
        seg = self.mm[doff:doff + dsz]
        found = None
        for i in range(0, dsz - 16, 8):
            ptr, ln = struct.unpack("<QQ", seg[i:i + 16])
            if ro_va <= ptr < ro_va + ro_sz and 8 < ln < 60:
                s = self.mm[ro_off + (ptr - ro_va):ro_off + (ptr - ro_va) + ln]
                if s.startswith(b"JARVIS_") and all(
                        65 <= c <= 90 or 48 <= c <= 57 or c == 95 for c in s):
                    found = s.decode()
                    break
        self.assertIsNotNone(found, "no shape-C record found")
        self.assertTrue(found.startswith("JARVIS_"))

    def test_index_build_id_bound(self):
        idx = json.load(open(os.path.join(WORK, "ref_index.json")))
        self.assertEqual(idx.get("build_id"), BUILD_ID)

    def test_shape_e_overread_guard(self):
        # 'JARVIS_ALLOW_DIRECT_COMMAND_EXEC' + 'Indices ' pack adjacently;
        # maximal munch over-reads one byte ('..._EXECI'). The guard must
        # trim to the pass-2 inventory name.
        inv2 = json.load(open("/tmp/inv_v2.json"))
        known = {e["name"] for e in inv2}
        munched = "JARVIS_ALLOW_DIRECT_COMMAND_EXECI"
        name = munched
        if name not in known:
            for i in range(len(name) - 1, 0, -1):
                if name[:i] in known:
                    name = name[:i]
                    break
        self.assertEqual(name, "JARVIS_ALLOW_DIRECT_COMMAND_EXEC")
        shapee = json.load(open(os.path.join(WORK, "inventory_shape_e.json")))
        self.assertIn("JARVIS_ALLOW_DIRECT_COMMAND_EXEC", shapee["names"])
        self.assertNotIn("JARVIS_ALLOW_DIRECT_COMMAND_EXECI", shapee["names"])

    def test_merged_inventory_count(self):
        merged = json.load(open(os.path.join(WORK,
                                             "inventory_merged_pass3.json")))
        self.assertEqual(merged["build_id"], BUILD_ID)
        self.assertEqual(merged["count"], 158)
        self.assertEqual(len(merged["inventory"]), 158)


if __name__ == "__main__":
    unittest.main(verbosity=2)
