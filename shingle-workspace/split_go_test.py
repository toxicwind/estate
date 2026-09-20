#!/usr/bin/env python3
"""Split an oversized Go test file into smaller files by test function.

Usage: split_go_test.py <source_test.go> <spec.json> [--apply]

Spec format:
{
  "groups": [
    {"file": "foo_test.go", "funcs": ["TestA", "TestB", ...], "helpers": ["helperFn"]},
    ...
  ]
}

Each output file gets: package clause + pruned import block (only imports
whose package qualifier is referenced in that file's functions) + the
grouped functions moved verbatim. Without --apply, prints a plan.
"""
import json
import os
import re
import sys


def parse_go_test(src):
    lines = src.split("\n")
    # package clause
    m = re.match(r"\s*package\s+(\w+)", src)
    package = m.group(1)
    # import block: find `import (` ... `)`
    imp_start = src.index("import (")
    depth = 0
    imp_end = None
    for i, ch in enumerate(src[imp_start:]):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                imp_end = imp_start + i + 1
                break
    import_block = src[imp_start:imp_end]
    # parse individual imports: [alias] "path", preserving blank-line groups
    imports = []  # (name, path, raw, group)
    group = 0
    last_end = 0
    for im in re.finditer(r'(?:(\w+)\s+)?\"([^\"]+)\"', import_block):
        alias, path = im.group(1), im.group(2)
        between = import_block[last_end:im.start()]
        if "\n\n" in between:
            group += 1
        last_end = im.end()
        if alias in ("_", "."):
            name = alias  # keep blank/dot as-is, always retain
        else:
            name = alias or path.rsplit("/", 1)[-1]
        imports.append((name, path, im.group(0), group))
    # top-level funcs: ^func Name(
    funcs = {}
    order = []
    for m in re.finditer(r"^func\s+(\w+)\s*\(", src, re.M):
        fname = m.group(1)
        start = m.start()
        # include preceding comment lines
        while start > 0:
            prev_end = src.rfind("\n", 0, start - 1)
            prev_line = src[prev_end + 1:start - 1].strip()
            if prev_line == "" or prev_line.startswith("//"):
                start = prev_end + 1
            else:
                break
        # find func end via brace matching
        brace = src.index("{", m.end())
        depth = 0
        instr = False
        inchar = False
        incomment = None
        i = brace
        while i < len(src):
            ch = src[i]
            nxt = src[i + 1] if i + 1 < len(src) else ""
            if incomment == "//":
                if ch == "\n":
                    incomment = None
            elif incomment == "/*":
                if ch == "*" and nxt == "/":
                    incomment = None
                    i += 1
            elif instr:
                if ch == "\\":
                    i += 1
                elif ch == '"':
                    instr = False
            elif inchar:
                if ch == "\\":
                    i += 1
                elif ch == "'":
                    inchar = False
            else:
                if ch == "/" and nxt == "/":
                    incomment = "//"
                elif ch == "/" and nxt == "*":
                    incomment = "/*"
                elif ch == '"':
                    instr = True
                elif ch == "'":
                    inchar = True
                elif ch == "`":
                    # raw string: skip to closing backtick
                    j = src.index("`", i + 1)
                    i = j
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
            i += 1
        funcs[fname] = src[start:i + 1]
        order.append(fname)
    return package, imports, funcs, order


def used_imports(func_bodies, imports):
    used = set()
    text = "\n".join(func_bodies)
    # strip strings/comments crudely for qualifier detection
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r'"(?:[^"\\]|\\.)*"', "", text)
    text = re.sub(r"//[^\n]*", "", text)
    for name, path, raw, grp in imports:
        if name in ("_", "."):
            used.add((raw, grp))
            continue
        if re.search(r"(?<![\w])" + re.escape(name) + r"\.", text):
            used.add((raw, grp))
    # testing is always needed for *testing.T params; ensure it
    for name, path, raw, grp in imports:
        if path == "testing":
            used.add((raw, grp))
    return used


def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    args = [a for a in args if a != "--apply"]
    if len(args) != 2:
        print("usage: split_go_test.py <source_test.go> <spec.json> [--apply]")
        sys.exit(2)
    src_path, spec_path = args
    spec = json.load(open(spec_path))
    src = open(src_path).read()
    package, imports, funcs, order = parse_go_test(src)

    seen = set()
    out_files = {}
    for g in spec["groups"]:
        bodies = []
        for fn in g["funcs"] + g.get("helpers", []):
            if fn not in funcs:
                raise KeyError("spec references unknown func: %s" % fn)
            bodies.append(funcs[fn].strip("\n"))
            seen.add(fn)
        used = used_imports(bodies, imports)
        # preserve original import order and blank-line groups
        by_raw = {}
        for name, path, raw, grp in imports:
            by_raw[raw] = grp
        ordered = [(raw, by_raw[raw]) for _, _, raw, _ in imports
                   if (raw, by_raw[raw]) in used]
        imp_block_lines = []
        last_grp = None
        for raw, grp in ordered:
            if last_grp is not None and grp != last_grp:
                imp_block_lines.append("")
            imp_block_lines.append("\t" + raw)
            last_grp = grp
        header = "package %s\n\nimport (\n%s\n)" % (
            package, "\n".join(imp_block_lines))
        out_files[g["file"]] = header + "\n\n" + "\n\n".join(bodies) + "\n"

    missing = [f for f in order if f not in seen]
    print("unaccounted funcs: %s" % (missing or "none"))
    for f, content in out_files.items():
        print("plan: %s (%d chars)" % (f, len(content)))

    if apply:
        d = os.path.dirname(os.path.abspath(src_path))
        src_abs = os.path.abspath(src_path)
        # write new files first, then remove the original
        for f, content in out_files.items():
            p = os.path.join(d, f)
            open(p, "w").write(content)
            print("wrote", p)
        if src_abs not in [os.path.join(d, f) for f in out_files]:
            os.remove(src_abs)
            print("removed", src_abs)


if __name__ == "__main__":
    main()
