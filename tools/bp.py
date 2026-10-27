#!/usr/bin/env python3
"""bp.py — budget printer: threshold-sampling mitigation for command logs.

Pools (of BP_BUDGET total screen chars):
  62% general | 30% error reserve | 8% meta

Sections start with '####' lines. Each section gets 25% of the remaining
general pool; unused allowance returns to the pool. Error lines (ERR
regex) draw from the error reserve so they always survive, like
low-probability tokens in threshold sampling.

Env:
  BP_BUDGET  total screen chars (default 8000)
  BP_WIDTH   max line width (default 240)
"""
import os
import re
import sys

BUDGET = int(os.environ.get("BP_BUDGET", "8000"))
WIDTH = int(os.environ.get("BP_WIDTH", "240"))

GENERAL = 0.62
ERROR_RESERVE = 0.30
META = 0.08

ERR_RE = re.compile(
    r"\b(errors?|errored|failed|fatal|panic|refused|denied|eaddrinuse|"
    r"not found|missing|traceback|exception|crashed|killed|timed out)\b",
    re.I,
)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b")
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
HEX_RE = re.compile(r"\b0x[0-9a-f]{6,}\b", re.I)
DEC_RE = re.compile(r"\b\d{4,}\b")
LONGNUM_RE = re.compile(r"\b\d{7,}\b")


def shape(line):
    """Strip noise so identical-looking lines dedupe to one entry."""
    s = ANSI_RE.sub("", line.rstrip("\n"))
    s = TS_RE.sub("<TS>", s)
    s = UUID_RE.sub("<UUID>", s)
    s = HEX_RE.sub("<HEX>", s)
    s = LONGNUM_RE.sub("<NUM>", s)
    s = DEC_RE.sub("<N>", s)
    return s


def is_meta(line):
    st = line.strip()
    return st.startswith("####") or st.startswith("===") or st.startswith("--")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    text = open(src, errors="replace").read() if src else sys.stdin.read()
    lines = text.splitlines()
    if not lines:
        print("bp: empty input", file=sys.stderr)
        return 0

    general_budget = int(BUDGET * GENERAL)
    error_budget = int(BUDGET * ERROR_RESERVE)
    meta_budget = int(BUDGET * META)

    out = []
    used = 0
    errors_used = 0
    metas_used = 0

    # section-aware: each '####' section gets 25% of the remaining general pool
    section_allow = None
    section_used = 0
    general_remaining = general_budget

    seen = set()
    for raw in lines:
        shaped = shape(raw)
        key = shaped.strip()
        if not key:
            continue

        if is_meta(raw):
            if metas_used + len(shaped) + 1 > meta_budget:
                continue
            metas_used += len(shaped) + 1
            out.append(shaped[:WIDTH])
            used += len(shaped) + 1
            if raw.strip().startswith("####"):
                # 25% of remaining general pool for this section
                section_allow = int(general_remaining * 0.25)
                section_used = 0
            continue

        if ERR_RE.search(shaped):
            cost = len(shaped) + 1
            if errors_used + cost > error_budget:
                continue
            errors_used += cost
            out.append(shaped[:WIDTH])
            used += cost
            continue

        # general pool
        if key in seen:
            continue
        seen.add(key)
        cost = len(shaped) + 1
        if section_allow is not None:
            if section_used + cost > section_allow:
                continue
            section_used += cost
        elif used + cost > general_budget + errors_used + metas_used:
            continue
        out.append(shaped[:WIDTH])
        used += cost

    sys.stdout.write("\n".join(out) + "\n")
    sys.stderr.write(
        "bp: budget=%d width=%d general=%d error=%d meta=%d "
        "lines=%d shown=%d\n"
        % (BUDGET, WIDTH, general_budget, error_budget, meta_budget,
           len(lines), len(out))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
