#!/usr/bin/env python3
"""Split an oversized Python file into modules per a JSON spec.

Spec format:
{
  "modules": [
    {"file": "mod.py",
     "imports": ["import os", ...],
     "items": ["decl_name", "stmt@<line>", ...]}
  ],
  "entry": {
    "docstring": true,
    "imports": [...],
    "reexports": ["name", ...],   # optional __all__ + from-imports are in imports
    "body": "if __name__ == ..."
  },
  "drop": ["stmt@<line>", ...]    # accounted-for but not emitted
}

Items are top-level function/class/assignment names, or stmt@<line> for
top-level statements (calls, if-guards). Source is moved verbatim, including
decorators and directly-preceding comment lines. In --apply mode the modules
are written next to the source and the source is rewritten as the entry shim.
Without --apply, prints a plan and reports unaccounted non-comment items.
"""
import ast
import json
import os
import sys


def include_preceding_comments(lines, start):
    # start is 1-based; walk up over contiguous comment/blank lines,
    # but stop at another code line or the top of file.
    s = start
    while s > 1:
        prev = lines[s - 2].strip()
        if prev == "" or prev.startswith("#"):
            s -= 1
        else:
            break
    return s


def scan(src):
    tree = ast.parse(src)
    lines = src.split("\n")
    nodes = {}   # name -> (start, end) 1-based inclusive
    stmts = {}   # stmt@line -> (start, end)
    order = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            for d in node.decorator_list:
                start = min(start, d.lineno)
            start = include_preceding_comments(lines, start)
            nodes[node.name] = (start, node.end_lineno)
            order.append(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    s = include_preceding_comments(lines, node.lineno)
                    nodes[t.id] = (s, node.end_lineno)
                    order.append(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            s = include_preceding_comments(lines, node.lineno)
            nodes[node.target.id] = (s, node.end_lineno)
            order.append(node.target.id)
        elif isinstance(node, ast.Expr):
            v = node.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                continue  # docstring / string expr, handled via entry
            key = "stmt@%d" % node.lineno
            stmts[key] = (node.lineno, node.end_lineno)
            order.append(key)
        elif isinstance(node, ast.If):
            key = "stmt@%d" % node.lineno
            stmts[key] = (node.lineno, node.end_lineno)
            order.append(key)
        # imports are not tracked: modules declare their own
    return nodes, stmts, order, lines, tree


def get_segment(lines, span):
    s, e = span
    return "\n".join(lines[s - 1:e])


def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    args = [a for a in args if a != "--apply"]
    if len(args) != 2:
        print("usage: split_py.py <source.py> <spec.json> [--apply]")
        sys.exit(2)
    src_path, spec_path = args
    spec = json.load(open(spec_path))
    src = open(src_path).read()
    nodes, stmts, order, lines, tree = scan(src)

    def get(name):
        if name in nodes:
            return get_segment(lines, nodes[name])
        if name in stmts:
            return get_segment(lines, stmts[name])
        raise KeyError("spec references unknown item: %s" % name)

    out_files = {}
    accounted = set(spec.get("drop", []))
    for mod in spec["modules"]:
        parts = []
        for name in mod["items"]:
            parts.append(get(name).rstrip("\n"))
            accounted.add(name)
        header = "\n".join(mod.get("imports", []))
        body = "\n\n\n".join(parts) + "\n"
        out_files[mod["file"]] = (header + "\n\n\n" + body) if header else body

    # entry shim
    entry = spec.get("entry", {})
    entry_parts = []
    if entry.get("docstring"):
        doc = ast.get_docstring(tree, clean=False)
        if doc:
            entry_parts.append('"""' + doc + '"""')
    eimports = "\n".join(entry.get("imports", []))
    if eimports:
        entry_parts.append(eimports)
    if entry.get("body"):
        entry_parts.append(entry["body"])
    out_files["__entry__"] = "\n\n\n".join(entry_parts) + "\n"

    # report unaccounted items (ignore imports, docstring expr)
    missing = []
    for name in order:
        if name in accounted:
            continue
        if name in nodes or name in stmts:
            # skip pure comment attach noise: stmts that are just strings already skipped
            missing.append(name)
    # filter: stmts that are only comments can't happen (ast skips comments)
    print("unaccounted items: %s" % (missing or "none"))
    for f, content in out_files.items():
        label = src_path if f == "__entry__" else f
        n_items = (len(entry.get("imports", [])) if f == "__entry__"
                   else len([m for m in spec["modules"] if m["file"] == f][0]["items"]))
        print("plan: %s (%d chars, %d items)" % (label, len(content), n_items))

    if apply:
        d = os.path.dirname(os.path.abspath(src_path))
        for mod in spec["modules"]:
            p = os.path.join(d, mod["file"])
            open(p, "w").write(out_files[mod["file"]])
            print("wrote", p)
        open(src_path, "w").write(out_files["__entry__"])
        print("rewrote", src_path)


if __name__ == "__main__":
    main()
