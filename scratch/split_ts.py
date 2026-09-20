#!/usr/bin/env python3
"""Split an oversized TypeScript file into ESM modules by moving top-level
declarations verbatim. Usage: split_ts.py <file> <spec.json> [--apply]

Spec JSON:
{
  "shebang": true,                      # keep #! line in main file
  "header_comment_lines": [1, 11],       # 1-based line range kept at top of main
  "modules": [
    {"file": "router_types.ts",
     "items": ["ChatBody", "RouteResult"],   # decl/stmt names in output order
     "imports": ["import type {...} from ...;"]},
    ...
  ],
  "main": {
    "keep": ["sessionId", "handleStream", "server", "keyed", "stmt@1360", ...],
    "imports": ["..."]
  },
  "drop": ["loadLocalRoleModels#2"]     # exact-duplicate decls to remove
}
Statement items are named stmt@<startline> (1-based, in the ORIGINAL file).
Moved decls are prefixed with `export `. Everything else is verbatim.
"""
import json
import re
import sys

KEYWORDS = ("async function", "function", "class", "const", "let",
            "type", "interface", "enum")


def strip_strings_and_comments_for_scan(text):
    # not used for parsing; parsing is done by the scanner below
    return text


def is_func_decl(first_line):
    s = first_line.strip()
    if s.startswith("export "):
        s = s[len("export "):]
    return s.startswith("function ") or s.startswith("function(") or \
        s.startswith("async function ")


def scan(text, skip_lines=None):
    """Return list of dicts: {kind: decl|stmt|comment, name, text}.
    Contiguous full-line // comments directly above a decl attach to it.
    skip_lines: optional (first, last) 1-based inclusive range to ignore.
    """
    lines = text.split("\n")
    n = len(lines)
    items = []
    i = 0
    if skip_lines:
        i = skip_lines[1]  # 0-based index of first line after the range

    def is_decl_start(ln):
        s = ln.strip()
        if s.startswith("export "):
            s = s[len("export "):]
        for kw in KEYWORDS:
            if s == kw or s.startswith(kw + " ") or s.startswith(kw + "("):
                # avoid matching e.g. "constant" (const) - require word boundary
                if kw in ("const", "let"):
                    if re.match(r"^(const|let)\b", s):
                        return True
                else:
                    return True
        return False

    def decl_name(first_line):
        s = first_line.strip()
        if s.startswith("export "):
            s = s[len("export "):]
        m = re.match(r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", s)
        if m:
            return m.group(1)
        m = re.match(r"class\s+([A-Za-z_$][\w$]*)", s)
        if m:
            return m.group(1)
        m = re.match(r"(?:const|let)\s+([A-Za-z_$][\w$]*)", s)
        if m:
            return m.group(1)
        m = re.match(r"(?:type|interface|enum)\s+([A-Za-z_$][\w$]*)", s)
        if m:
            return m.group(1)
        return "unknown"

    def decl_end(lines, i, func=False):
        # returns exclusive end line index, template/brace/paren aware.
        # func=True: the decl is a function declaration, whose header may
        # contain a return-type object literal `: {...}` before the body.
        # A `}` that closes the decl while the next non-ws char is `{`
        # closed the return type, not the body -> keep scanning.
        n = len(lines)
        j = i
        depth_brace = 0
        depth_paren = 0
        depth_brack = 0
        in_tpl = 0          # template literal nesting level
        tpl_brace = []      # brace depth at which each ${ started
        state = "code"      # code | sq | dq | tpl | lcom | bcom
        k = 0
        line = lines[j]
        started = False
        while True:
            while k < len(line):
                ch = line[k]
                nxt = line[k + 1] if k + 1 < len(line) else ""
                if state == "lcom":
                    break
                if state == "bcom":
                    if ch == "*" and nxt == "/":
                        state = "code"
                        k += 2
                        continue
                    k += 1
                    continue
                if state == "sq":
                    if ch == "\\":
                        k += 2
                        continue
                    if ch == "'":
                        state = "code"
                    k += 1
                    continue
                if state == "dq":
                    if ch == "\\":
                        k += 2
                        continue
                    if ch == '"':
                        state = "code"
                    k += 1
                    continue
                if state == "tpl":
                    if ch == "\\":
                        k += 2
                        continue
                    if ch == "`":
                        state = "code"
                        in_tpl -= 1
                        k += 1
                        continue
                    if ch == "$" and nxt == "{":
                        tpl_brace.append(depth_brace)
                        depth_brace += 1
                        state = "code"
                        k += 2
                        continue
                    k += 1
                    continue
                # state == code
                if ch == "/" and nxt == "/":
                    state = "lcom"
                    break
                if ch == "/" and nxt == "*":
                    state = "bcom"
                    k += 2
                    continue
                if ch == "/":
                    # Possible regex literal: distinguish from division by the
                    # previous significant char/word. Division follows an
                    # operand (identifier, digit, ), ], ", ', `); a regex
                    # follows an operator, opener, or keyword like return.
                    p = k - 1
                    while p >= 0 and line[p] in " \t":
                        p -= 1
                    prev = line[p] if p >= 0 else ""
                    is_regex = False
                    if prev == "" or prev in "([{,;=:!&|?>+-~":
                        is_regex = True
                    elif prev.isalnum() or prev in "_$":
                        wend = p + 1
                        wstart = wend
                        while wstart > 0 and (line[wstart - 1].isalnum() or
                                              line[wstart - 1] in "_$"):
                            wstart -= 1
                        if line[wstart:wend] in ("return", "typeof",
                                                 "instanceof", "in", "of",
                                                 "new", "delete", "void",
                                                 "throw", "yield", "await"):
                            is_regex = True
                    if is_regex:
                        # consume to closing unescaped / outside [...]
                        k += 1
                        in_class = False
                        while k < len(line):
                            rc = line[k]
                            if rc == "\\":
                                k += 2
                                continue
                            if rc == "[":
                                in_class = True
                            elif rc == "]":
                                in_class = False
                            elif rc == "/" and not in_class:
                                break
                            k += 1
                        k += 1  # closing /
                        while k < len(line) and line[k].isalpha():
                            k += 1  # flags
                        continue
                if ch == "'":
                    state = "sq"
                    k += 1
                    continue
                if ch == '"':
                    state = "dq"
                    k += 1
                    continue
                if ch == "`":
                    state = "tpl"
                    in_tpl += 1
                    k += 1
                    continue
                if ch == "{":
                    depth_brace += 1
                    started = True
                elif ch == "}":
                    depth_brace -= 1
                    if tpl_brace and depth_brace == tpl_brace[-1]:
                        tpl_brace.pop()
                        state = "tpl"
                    elif started and depth_brace == 0 and depth_paren == 0 and depth_brack == 0 and in_tpl == 0:
                        # consume rest of line (e.g. trailing ;)
                        # A `}` at depth 0 may close a TYPE annotation rather
                        # than the decl: `function f(): {...} {`,
                        # `const X: Record<..., {...}> = {...}`. Peek the next
                        # non-ws char: `{` (func body follows), `>`/`=`
                        # (type annotation continues / value follows) mean
                        # the decl is not over yet.
                        pj = j
                        pk = k + 1
                        pline = line
                        while True:
                            while pk < len(pline) and pline[pk] in " \t":
                                pk += 1
                            if pk < len(pline):
                                break
                            pj += 1
                            if pj >= n:
                                break
                            pline = lines[pj]
                            pk = 0
                        nxt = pline[pk] if pj < n else ""
                        if (func and nxt == "{") or nxt in (">", "="):
                            k += 1
                            continue
                        return j + 1
                elif ch == "(":
                    depth_paren += 1
                elif ch == ")":
                    depth_paren -= 1
                elif ch == "[":
                    depth_brack += 1
                elif ch == "]":
                    depth_brack -= 1
                elif ch == ";" and depth_brace == 0 and depth_paren == 0 and depth_brack == 0 and in_tpl == 0:
                    return j + 1
                k += 1
            j += 1
            if j >= n:
                return n
            line = lines[j]
            k = 0
            if state == "lcom":
                state = "code"

    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s.startswith("#!"):
            items.append({"kind": "shebang", "name": "shebang",
                          "text": ln + "\n"})
            i += 1
            continue
        if is_decl_start(ln):
            # attach contiguous full-line comments above
            start = i
            j = i - 1
            while j >= 0 and lines[j].strip().startswith("//"):
                # don't steal a trailing comment that belongs to previous item:
                # only attach if the comment block is directly above (no blank)
                start = j
                j -= 1
            end = decl_end(lines, i, func=is_func_decl(ln))
            text = "\n".join(lines[start:end]) + "\n"
            name = decl_name(ln)
            # disambiguate duplicates: name#2, name#3 ...
            count = sum(1 for it in items
                        if it["kind"] == "decl" and it["name"] == name) + 1
            iname = name if count == 1 else "%s#%d" % (name, count)
            items.append({"kind": "decl", "name": iname, "text": text,
                          "start": start + 1})
            i = end
            # swallow following blank lines (they re-emit via join)
            continue
        # top-level statement or standalone comment: capture to end of
        # statement (brace/semicolon aware) so `if { }` blocks stay whole
        start_line = i + 1
        if s.startswith("//"):
            end = i + 1
            while end < n and lines[end].strip().startswith("//"):
                end += 1
            items.append({"kind": "comment",
                          "name": "stmt@%d" % start_line,
                          "text": "\n".join(lines[i:end]) + "\n"})
            i = end
            continue
        if s.startswith("/*"):
            end = i
            while end < n and "*/" not in lines[end]:
                end += 1
            end = min(end + 1, n)
            items.append({"kind": "comment",
                          "name": "stmt@%d" % start_line,
                          "text": "\n".join(lines[i:end]) + "\n"})
            i = end
            continue
        end = decl_end(lines, i)
        items.append({"kind": "stmt", "name": "stmt@%d" % start_line,
                      "text": "\n".join(lines[i:end]) + "\n"})
        i = end
    return items


def main():
    src = sys.argv[1]
    spec = json.load(open(sys.argv[2]))
    apply = len(sys.argv) > 3 and sys.argv[3] == "--apply"
    text = open(src).read()
    items = scan(text, skip_lines=spec.get("skip_lines"))
    by_name = {}
    for it in items:
        by_name.setdefault(it["name"], []).append(it)

    def get(name):
        lst = by_name.get(name)
        if not lst:
            raise SystemExit("spec references unknown item: %s" % name)
        if len(lst) > 1:
            raise SystemExit("ambiguous item name (use #n): %s" % name)
        return lst[0]

    for d in spec.get("drop", []):
        it = get(d)
        it["dropped"] = True

    out_files = {}

    def add_export(text):
        # prefix the declaration keyword with `export `
        m = re.match(r"((?:async\s+)?function|class|const|let|type|interface|enum)\b",
                     text)
        if not m:
            # leading attached comments: insert export before the keyword
            m2 = re.search(r"^((?:async\s+)?function|class|const|let|type|interface|enum)\b",
                           text, re.M)
            if not m2:
                return text
            pos = m2.start()
            return text[:pos] + "export " + text[pos:]
        return "export " + text

    for mod in spec["modules"]:
        parts = []
        for name in mod["items"]:
            it = get(name)
            if it.get("dropped"):
                continue
            t = it["text"]
            if it["kind"] == "decl":
                t = add_export(t)
            parts.append(t.rstrip("\n"))
        header = "".join(imp + "\n" for imp in mod.get("imports", []))
        if header:
            header += "\n"
        out_files[mod["file"]] = header + "\n\n".join(parts) + "\n"

    # main file
    keep = spec["main"]["keep"]
    kept = []
    for name in keep:
        it = get(name)
        if it.get("dropped"):
            continue
        kept.append(it["text"].rstrip("\n"))
    accounted = set()
    for mod in spec["modules"]:
        accounted.update(mod["items"])
    accounted.update(keep)
    accounted.update(spec.get("drop", []))
    accounted.add("shebang")
    missing = [it["name"] for it in items
               if it["name"] not in accounted and not it.get("dropped")]
    # header text + shebang handled below; report anything else lost
    main_text = ""
    if spec.get("shebang"):
        main_text += "#!/usr/bin/env bun\n"
    if spec.get("header_text"):
        main_text += spec["header_text"]
    mimports = "".join(imp + "\n" for imp in spec["main"].get("imports", []))
    if mimports:
        main_text += "\n" + mimports + "\n"
    main_text += "\n\n".join(kept) + "\n"
    out_files["__main__"] = main_text

    # report unaccounted items (original import stmts are expected: they are
    # replaced by the new per-module import blocks)
    stray = [m for m in missing
             if not (m.startswith("stmt@") and
                     by_name[m][0]["kind"] == "comment")]
    print("unaccounted non-comment items: %s" % (stray or "none"))
    for f, content in out_files.items():
        label = src if f == "__main__" else f
        print("plan: %s (%d chars, %d items)" %
              (label, len(content),
               len(spec["main"]["keep"]) if f == "__main__"
               else len([m for m in spec["modules"]
                         if m["file"] == f][0]["items"])))
    if apply:
        import os
        d = os.path.dirname(src)
        for mod in spec["modules"]:
            p = os.path.join(d, mod["file"])
            open(p, "w").write(out_files[mod["file"]])
            print("wrote", p)
        open(src, "w").write(out_files["__main__"])
        print("rewrote", src)


if __name__ == "__main__":
    main()
