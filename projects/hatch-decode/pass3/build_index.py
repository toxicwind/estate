#!/usr/bin/env python3
"""hatch-decode pass3 — build a persistent index of .text references.

One expensive linear pass over .text; everything else reads the index.
Index entries (JSON):
  lea: [{va, tgt}]            REX-prefixed RIP-relative lea -> any target
  abs32: [{va, imm}]          mov r/m32, imm32 with imm in .rodata range
  abs64: [{va, imm}]          movabs imm64 in .rodata range
Also records section map + binary build-id so stale indexes are detected.
"""
import json
import os
import re
import struct
import subprocess
import sys

BIN = "/opt/hatch/bin/hatch"
IDX = "ref_index.json"


def sections():
    out = subprocess.run(["readelf", "-S", "-W", BIN],
                         capture_output=True, text=True, check=True).stdout
    secs = {}
    for line in out.splitlines():
        m = re.match(
            r"\s*\[\s*\d+\]\s+(\S+)\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)",
            line)
        if m:
            secs[m.group(1)] = (int(m.group(2), 16), int(m.group(3), 16),
                                int(m.group(4), 16))
    return secs


def build_id():
    out = subprocess.run(["readelf", "-n", BIN],
                         capture_output=True, text=True).stdout
    m = re.search(r"Build ID: ([0-9a-f]+)", out)
    return m.group(1) if m else "unknown"


def main():
    if os.path.exists(IDX):
        old = json.load(open(IDX))
        if old.get("build_id") == build_id():
            print(f"index fresh ({IDX}), build {old['build_id'][:12]}")
            return
        print("binary changed since index; rebuilding")

    secs = sections()
    ro_va, ro_off, ro_sz = secs[".rodata"]
    tx_va, tx_off, tx_sz = secs[".text"]
    with open(BIN, "rb") as f:
        mm = f.read()
    text = mm[tx_off:tx_off + tx_sz]

    lea, abs32, abs64 = [], [], []
    # REX-prefixed RIP-relative lea: REX(0x40-0x4f) 8D modrm(mod=00,rm=101)
    for m in re.finditer(rb"[\x40-\x4f]\x8d", text):
        pos = m.start()
        if (text[pos + 2] & 0xC7) != 0x05:
            continue
        va = tx_va + pos
        disp = struct.unpack("<i", text[pos + 3:pos + 7])[0]
        lea.append((va, va + 7 + disp))
    # mov r/m32, imm32: C7 /0 (modrm mod=11 reg=000)
    for m in re.finditer(rb"\xc7[\xc0-\xc7]", text):
        pos = m.start()
        imm = struct.unpack("<I", text[pos + 2:pos + 6])[0]
        if ro_va <= imm < ro_va + ro_sz:
            abs32.append((tx_va + pos, imm))
    # mov reg32, imm32: B8+rd
    for m in re.finditer(rb"\xb8|\xb9|\xba|\xbb|\xbc|\xbd|\xbe|\xbf", text):
        pos = m.start()
        imm = struct.unpack("<I", text[pos + 1:pos + 5])[0]
        if ro_va <= imm < ro_va + ro_sz:
            abs32.append((tx_va + pos, imm))
    # movabs reg64, imm64: REX.W B8+rd
    for m in re.finditer(rb"\x48\xb8|\x48\xb9|\x48\xba|\x48\xbb|\x48\xbc"
                         rb"|\x48\xbd|\x48\xbe|\x48\xbf", text):
        pos = m.start()
        imm = struct.unpack("<Q", text[pos + 2:pos + 10])[0]
        if ro_va <= imm < ro_va + ro_sz:
            abs64.append((tx_va + pos, imm))

    idx = {
        "build_id": build_id(),
        "sections": {k: [hex(a), hex(b), hex(c)]
                     for k, (a, b, c) in secs.items()},
        "lea": [[hex(a), hex(b)] for a, b in lea],
        "abs32": [[hex(a), hex(b)] for a, b in abs32],
        "abs64": [[hex(a), hex(b)] for a, b in abs64],
    }
    json.dump(idx, open(IDX, "w"))
    print(f"lea={len(lea)} abs32={len(abs32)} abs64={len(abs64)} -> {IDX}")


if __name__ == "__main__":
    main()
