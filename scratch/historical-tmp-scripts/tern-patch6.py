#!/usr/bin/env python3
"""tern 2026-09-21: marker-retention fix.

The timeout handler built out_full = [PARTIAL marker] + node_summary +
part_out, then took [-OUT_CAP:]. With large partial stdout the marker
and node summary were sliced away -- the returned output was no longer
clearly marked partial. Fix: reserve headroom for the marker so it can
never be lost.
"""
P = "/home/toxic/sovereign/agents/oracle-market/bin/bidder.py"
src = open(P, encoding="utf-8").read()

old = '''            out_full = ("[PARTIAL - super-ralph timed out after %.0fs; "
                        "full evidence in partial-output.txt]\\n" % ceiling)
            if node_summary:
                out_full += node_summary + "\\n"
            out = _canon_ralph_text(out_full + part_out)[-OUT_CAP:]'''
new = '''            marker = ("[PARTIAL - super-ralph timed out after %.0fs; "
                      "full evidence in partial-output.txt]\\n" % ceiling)
            head = marker + (node_summary + "\\n" if node_summary else "")
            # 2026-09-21 (tern): the PARTIAL marker must survive even
            # with huge partial stdout -- reserve its headroom first.
            body = _canon_ralph_text(part_out)[-(OUT_CAP - len(head)):]
            out = head + body'''
assert src.count(old) == 1, "marker anchor, got %d" % src.count(old)
src = src.replace(old, new)

with open(P, "w", encoding="utf-8") as f:
    f.write(src)
print("marker fix OK")
