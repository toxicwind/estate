#!/usr/bin/env python3
"""hatch-decode pass3 — inventory scanner v2 (index-driven).

Reads ref_index.json (build_index.py). For each lea -> .rodata:
  disassemble <=6 insns; insn[0] must be lea; scan insn[1..5] for
  `mov r32, imm` immediates. The LENGTH is the imm L such that
  rodata[tgt : tgt+L] fully matches ^JARVIS_[A-Z0-9_]+$. Any other
  imm in the window is recorded as a candidate default.
Also:
  shape C: static &str {ptr,len} in .data.rel.ro
  shape B: abs32/abs64 loads; prefix-match against voted (name,len)
  shape D: lea -> .rodata with no length imm; prefix-match voted names
Call targets are resolved (direct rel32) to cluster reader families.

Outputs: inventory_pass3.json, sites_pass3.json
"""
import json
import re
import struct
import subprocess

BIN = "/opt/hatch/bin/hatch"
NAME_RE = re.compile(rb"^JARVIS_[A-Z0-9_]+$")


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


def main():
    idx = json.load(open("ref_index.json"))
    secs = sections()
    ro_va, ro_off, ro_sz = secs[".rodata"]
    tx_va, tx_off, tx_sz = secs[".text"]
    dr_va, dr_off, dr_sz = secs[".data.rel.ro"]

    mm = open(BIN, "rb").read()

    def file_off(va, s_va, s_off, s_sz):
        return va - s_va + s_off if s_va <= va < s_va + s_sz else None

    def ro_at(va, n):
        o = file_off(va, ro_va, ro_off, ro_sz)
        return mm[o:o + n] if o is not None else b""

    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    md = Cs(CS_ARCH_X86, CS_MODE_64)

    def disasm(va, n=6):
        o = file_off(va, tx_va, tx_off, tx_sz)
        if o is None:
            return []
        return list(md.disasm(mm[o:o + 96], va, count=n))

    inv = {}
    sites = []

    def rec(name, va, shape, length=None, default=None, reader=None, tgt=None):
        e = inv.setdefault(name, {"sites": [], "lengths": [], "shapes": [],
                                  "defaults": [], "readers": []})
        e["sites"].append(hex(va))
        for key, val in (("lengths", length), ("defaults", default),
                         ("readers", reader), ("shapes", shape)):
            if val is not None and val not in e[key]:
                e[key].append(val)
        sites.append({"name": name, "va": hex(va), "shape": shape,
                      "tgt": hex(tgt) if tgt else None,
                      "length": length, "default": default,
                      "reader": reader})

    IMM_RE = re.compile(r"^(e[a-z]{2}|r[a-z0-9]{2,3}|[a-z]{2,3}),\s*"
                        r"(0x[0-9a-f]+|\d+)$")

    def call_target(ins):
        m = re.match(r"^(0x[0-9a-f]+)$", ins.op_str)
        if ins.mnemonic == "call" and m:
            return hex(int(m.group(1), 16))
        return (ins.mnemonic + " " + ins.op_str) if ins.mnemonic == "call" \
            else None

    n_lea_ro = 0
    for va_s, tgt_s in idx["lea"]:
        va, tgt = int(va_s, 16), int(tgt_s, 16)
        if not (ro_va <= tgt < ro_va + ro_sz):
            continue
        ins = disasm(va)
        if not ins or ins[0].mnemonic != "lea":
            continue
        n_lea_ro += 1
        imms = []
        reader = None
        for i in ins[1:6]:
            if i.mnemonic == "mov":
                m = IMM_RE.match(i.op_str)
                if m:
                    imms.append(int(m.group(2), 0))
            if reader is None:
                reader = call_target(i)
        # the length is the imm that slices a full name
        name = length = default = None
        for imm in imms:
            if 7 < imm < 120:
                raw = ro_at(tgt, imm)
                if NAME_RE.match(raw):
                    name, length = raw.decode(), imm
                    break
        if name is None:
            # shape D candidate: prefix-match will run later
            sites.append({"name": None, "va": hex(va), "shape": "D?",
                          "tgt": hex(tgt), "length": None,
                          "default": None, "reader": reader,
                          "prefix": ro_at(tgt, 60).decode("latin1")})
            continue
        for imm in imms:
            if imm != length and default is None:
                default = imm
        rec(name, va, "A", length, default, reader, tgt)

    # shape C: static &str in .data.rel.ro
    datarel = mm[dr_off:dr_off + dr_sz]
    for off in range(0, dr_sz - 16, 8):
        ptr, ln = struct.unpack("<QQ", datarel[off:off + 16])
        if ro_va <= ptr < ro_va + ro_sz and 7 < ln < 120:
            raw = ro_at(ptr, ln)
            if NAME_RE.match(raw):
                rec(raw.decode(), dr_va + off, "C", ln, None, None, ptr)

    # shape B: absolute loads; prefix-match voted names (packed runs)
    voted = {n: e["lengths"][0] for n, e in inv.items() if e["lengths"]}

    def prefix_match(tgt):
        raw = ro_at(tgt, 120)
        for n, ln in voted.items():
            if raw[:ln] == n.encode():
                return n, ln
        return None, None

    for key in ("abs32", "abs64"):
        for va_s, tgt_s in idx[key]:
            va, tgt = int(va_s, 16), int(tgt_s, 16)
            n, ln = prefix_match(tgt)
            if n:
                rec(n, va, "B", ln, None, None, tgt)

    # shape D: resolve the D? sites via voted prefix match
    for s in sites:
        if s["shape"] == "D?" and s["name"] is None:
            n, ln = prefix_match(int(s["tgt"], 16))
            if n:
                s["shape"] = "D"
                rec(n, int(s["va"], 16), "D", ln, None, s["reader"],
                    int(s["tgt"], 16))
            else:
                s["shape"] = "D_unresolved"

    json.dump(inv, open("inventory_pass3.json", "w"), indent=1, sort_keys=True)
    json.dump(sites, open("sites_pass3.json", "w"), indent=1)
    shapes = {}
    for e in inv.values():
        for sh in e["shapes"]:
            shapes[sh] = shapes.get(sh, 0) + 1
    print(f"verified lea->rodata: {n_lea_ro}")
    print(f"distinct names: {len(inv)}  shapes: {shapes}")
    unresolved = [s for s in sites if s["shape"] == "D_unresolved"]
    print(f"D_unresolved: {len(unresolved)}")


if __name__ == "__main__":
    main()
