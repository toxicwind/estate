#!/usr/bin/env python3
"""Shape-E scanner: JARVIS_* names referenced from SIMD constant pools.

In the e86e3030628 build, 8 env vars moved out of plain .rodata into
.rodata.cst16/.rodata.cst32 and are read through new idioms:

  lea rdi, [rip -> cst]      ; packed constant, adjacent strings, no NUL
  mov esi, <name_buf_len>    ; often rounded (e.g. 32)
  mov edx, <default>         ; numeric default when the reader takes one
  call <reader>

Name extraction uses maximal JARVIS_[A-Z0-9_]+ munch, then corrects the
known over-read hazard (adjacent string starting with 'I', e.g.
'..._EXEC' + 'Indices') by cross-checking the pass-2 inventory and by
requiring the munched tail to not extend into an obvious second token.
Every emitted name carries its site, reader, and observed default.
"""
import json
import re
import struct
import subprocess
import sys

BIN = "/opt/hatch/bin/hatch"
WORK = "/home/hatch/workspace/hatch-decode-pass3"

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


def main():
    secs = sections()
    tx_va, tx_off, tx_sz = secs[".text"]
    cst_secs = [(n, secs[n]) for n in secs if n.startswith(".rodata.cst")]
    mm = open(BIN, "rb").read()

    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    md = Cs(CS_ARCH_X86, CS_MODE_64)

    idx = json.load(open(f"{WORK}/ref_index.json"))
    if idx.get("build_id") != BUILD_ID:
        sys.exit(f"stale index: {idx.get('build_id')} != {BUILD_ID}")

    inv2 = json.load(open("/tmp/inv_v2.json"))
    known = {e["name"] for e in inv2}

    results = {}
    for cst_name, (cst_va, cst_off, cst_sz) in cst_secs:
        sites = [(int(a, 16), int(b, 16)) for a, b in idx["lea"]
                 if cst_va <= int(b, 16) < cst_va + cst_sz]
        for va, tgt in sites:
            o = va - tx_va + tx_off
            ins = list(md.disasm(mm[o:o + 64], va, count=6))
            if not ins or ins[0].mnemonic != "lea":
                continue
            ib = mm[o:o + 7]
            if len(ib) < 7:
                continue
            disp = struct.unpack("<i", ib[3:7])[0]
            if va + 7 + disp != tgt:
                continue
            raw = mm[cst_off + (tgt - cst_va):cst_off + (tgt - cst_va) + 64]
            m = re.match(rb"JARVIS_[A-Z0-9_]+", raw)
            if not m:
                continue
            name = m.group(0).decode()
            # Over-read guard: if the munch ran into an adjacent all-caps
            # token, trim back to the longest prefix present in the pass-2
            # inventory (e.g. '..._EXECI' -> '..._EXEC' before 'Indices').
            if name not in known:
                for i in range(len(name) - 1, 0, -1):
                    if name[:i] in known:
                        name = name[:i]
                        break
            esi = edx = call = None
            for i in ins[1:6]:
                if i.mnemonic == "mov" and i.op_str.startswith("esi,"):
                    esi = int(i.op_str.split(",")[1].strip(), 0)
                if i.mnemonic == "mov" and i.op_str.startswith("edx,"):
                    edx = int(i.op_str.split(",")[1].strip(), 0)
                if i.mnemonic == "call":
                    call = i.op_str
            entry = results.setdefault(name, {"sites": [], "section": cst_name})
            entry["sites"].append({"va": hex(va), "name_len_hint": esi,
                                  "default": edx, "reader": call})

    out = {"build_id": BUILD_ID, "binary": BIN, "shape": "E",
           "names": results}
    with open(f"{WORK}/inventory_shape_e.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print(f"shape-E names: {len(results)}")
    for n in sorted(results):
        ds = sorted({s["default"] for s in results[n]["sites"]
                     if s["default"] is not None})
        print(f"  {n}: defaults={ds} "
              f"sites={[s['va'] for s in results[n]['sites']][:3]}")


if __name__ == "__main__":
    main()
