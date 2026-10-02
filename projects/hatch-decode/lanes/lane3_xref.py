#!/usr/bin/env python3
"""L3: fast-xref — byte-scan .text for RIP-relative LEAs targeting each JARVIS_*
string, then disassemble a small window with capstone for context.
Answers: which instructions (and hence which code regions) read each var.
No full disassembly; C-speed regex scan."""
import re, struct, subprocess, json, sys

BIN = "/opt/hatch/bin/hatch"

def sections():
    out = subprocess.run(["readelf", "-S", "-W", BIN],
                         capture_output=True, text=True).stdout
    secs = {}
    for m in re.finditer(
            r'\[\s*\d+\]\s+(\S+)\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)',
            out):
        secs[m.group(1)] = (int(m.group(2), 16), int(m.group(3), 16),
                            int(m.group(4), 16))
    return secs

def main():
    secs = sections()
    with open(BIN, "rb") as f:
        data = f.read()

    def va_of(off):
        for name, (vaddr, foff, size) in secs.items():
            if foff <= off < foff + size:
                return vaddr + (off - foff), name
        return None, None

    var_offs = {}
    for m in re.finditer(rb'JARVIS_[A-Z_0-9]+', data):
        var_offs.setdefault(m.group(0).decode(), []).append(m.start())
    print(f"vars: {len(var_offs)}", file=sys.stderr)

    text_va, text_off, text_size = secs[".text"]
    text = data[text_off:text_off + text_size]

    # REX.W LEA r64,[RIP+disp32]: 48 8D modrm(disp32); modrm mod=00 rm=101
    pat = re.compile(rb'\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....')
    xrefs = {}  # target va -> [insn va]
    for m in pat.finditer(text):
        disp = struct.unpack_from('<i', m.group(0), 3)[0]
        insn_va = text_va + m.start()
        xrefs.setdefault(insn_va + 7 + disp, []).append(insn_va)
    print(f"LEA candidates: {sum(len(v) for v in xrefs.values())}",
          file=sys.stderr)

    result = {}
    for var, offs in sorted(var_offs.items()):
        hits = []
        for off in offs:
            va, _ = va_of(off)
            if va and va in xrefs:
                for insn in xrefs[va]:
                    hits.append({"string_va": hex(va),
                                 "xref_insn_va": hex(insn)})
        if hits:
            result[var] = hits

    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_64
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        for hits in result.values():
            for h in hits:
                iva = int(h["xref_insn_va"], 16)
                start = max(text_va, iva - 64)
                end = iva + 40
                code = data[text_off + (start - text_va):
                            text_off + (end - text_va)]
                lines = []
                for i in md.disasm(code, start):
                    mark = ">>>" if i.address == iva else "   "
                    lines.append(f"{mark} {i.address:016x}: "
                                 f"{i.mnemonic:10s} {i.op_str}")
                h["window"] = "\n".join(lines)
    except ImportError as e:
        print(f"capstone missing: {e}", file=sys.stderr)

    with open("../findings/lane3_xrefs.json", "w") as f:
        json.dump(result, f, indent=1)
    print(f"vars with xrefs: {len(result)}/{len(var_offs)}")

if __name__ == "__main__":
    main()
