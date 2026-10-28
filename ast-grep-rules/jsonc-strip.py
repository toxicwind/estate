#!/usr/bin/env python3
"""Strip single-line (//) and block (/* */) comments from JSONC files.

Usage:
  python3 jsonc-strip.py input.jsonc          # stdout
  python3 jsonc-strip.py input.jsonc -o out.json  # file output

Why: ast-grep --lang json uses tree-sitter-json which does NOT support
comments. tree-sitter-jsonc exists upstream but ast-grep doesn't bundle it.
This preprocessor strips comments so ast-grep can scan JSONC files.

DO NOT use ast-grep --lang jsonc — it will fail. Use:
  python3 jsonc-strip.py file.jsonc | ast-grep run --lang json --pattern '...'
"""

import argparse
import re
import sys


def strip_jsonc(text: str) -> str:
    """Remove // line comments and /* block */ comments outside strings."""
    out = []
    i = 0
    in_string = False
    escape = False
    while i < len(text):
        c = text[i]
        if escape:
            out.append(c)
            escape = False
            i += 1
            continue
        if in_string:
            if c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            out.append(c)
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt == "/":
                # skip to end of line
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            if nxt == "*":
                # skip block comment
                i += 2
                while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2  # skip */
                continue
        out.append(c)
        i += 1
    return "".join(out)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Strip JSONC comments for ast-grep")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    args = p.parse_args()
    src = open(args.input).read()
    result = strip_jsonc(src)
    if args.output:
        open(args.output, "w").write(result)
    else:
        sys.stdout.write(result)
