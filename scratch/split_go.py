#!/usr/bin/env python3
"""Surgically split a Go source file into multiple same-package files.

Top-level declarations (func/type/var/const incl. doc comments) are moved,
never rewritten. Decls not matching any group stay in the original file.

Usage: split_go.py <src.go> <spec.json> [--apply]
spec.json: {"new_file.go": ["NamePrefix", ...], ...}
A decl matches the first file with a prefix of its name. Methods match on
"Recv.Method" or bare "Method".
Without --apply: prints the plan (name -> target).
"""
import json, re, sys


def decl_end(lines, i):
    """Return exclusive end line index of the top-level decl starting at i."""
    n = len(lines)
    # First: find end of signature for funcs (paren depth), to catch asm stubs.
    text = lines[i]
    m = re.match(r'^(func)\s*(\([^)]*\)\s*)?([A-Za-z_][\w]*|_)?', text)
    # generic brace/paren scanner with string+comment awareness
    depth = 0
    seen_open = False
    in_str = in_raw = in_char = in_lc = in_bc = False
    j = i
    sig_closed_at = None  # (line, col) where func signature parens closed
    paren = 0
    while j < n:
        s = lines[j]
        k = 0
        while k < len(s):
            c = s[k]
            nxt = s[k + 1] if k + 1 < len(s) else ''
            if in_lc:
                break
            elif in_bc:
                if c == '*' and nxt == '/':
                    in_bc = False
                    k += 1
            elif in_str:
                if c == '\\':
                    k += 1
                elif c == '"':
                    in_str = False
            elif in_raw:
                if c == '`':
                    in_raw = False
            elif in_char:
                if c == '\\':
                    k += 1
                elif c == "'":
                    in_char = False
            else:
                if c == '/' and nxt == '/':
                    in_lc = True
                    break
                elif c == '/' and nxt == '*':
                    in_bc = True
                    k += 1
                elif c == '"':
                    in_str = True
                elif c == '`':
                    in_raw = True
                elif c == "'":
                    in_char = True
                elif c == '(':
                    paren += 1
                    depth += 1
                    seen_open = True
                elif c in '{[':
                    depth += 1
                    seen_open = True
                elif c == ')':
                    paren -= 1
                    depth -= 1
                    if m and paren == 0 and sig_closed_at is None and j == i:
                        # signature closed on first line; check for body brace
                        rest = s[k + 1:].lstrip()
                        if not rest.startswith('{'):
                            # no body on this line -> could be asm stub or
                            # multi-line signature; keep scanning
                            sig_closed_at = (j, k)
                elif c in '}]':
                    depth -= 1
            k += 1
        in_lc = False
        # asm-stub / bodyless decl: signature closed and no '{' follows
        if sig_closed_at is not None and not seen_open:
            # verify next non-empty line doesn't start with '{'
            jj = j + 1
            while jj < n and not lines[jj].strip():
                jj += 1
            if jj >= n or not lines[jj].lstrip().startswith('{'):
                return j + 1
            sig_closed_at = None  # brace on next line; keep scanning
        if seen_open and depth == 0:
            return j + 1
        if not seen_open and j > i + 8:
            # single-line decl without any opener (const x = 1 etc.)
            return i + 1
        j += 1
    return j


def decl_name(first_line):
    s = first_line.strip()
    if s.startswith('func '):
        rest = s[5:].lstrip()
        recv = None
        if rest.startswith('('):
            end = rest.find(')')
            recv = rest[1:end].strip().split()[-1].lstrip('*')
            rest = rest[end + 1:].lstrip()
        m = re.match(r'([A-Za-z_][\w]*)', rest)
        name = m.group(1) if m else '?'
        return f'{recv}.{name}' if recv else name
    m = re.match(r'(?:type|var|const)\s+(?:\(\s*)?([A-Za-z_][\w]*)?', s)
    if m and m.group(1):
        return m.group(1)
    m = re.match(r'(?:type|var|const)\s*\(', s)
    if m:
        return '(group)'
    return '(anon)'


def main():
    src = sys.argv[1]
    spec = json.load(open(sys.argv[2]))
    apply = '--apply' in sys.argv
    text = open(src).read()
    lines = text.splitlines(keepends=True)
    n = len(lines)

    # header: everything before first top-level decl
    first_decl = None
    for i, ln in enumerate(lines):
        if ln and not ln[0].isspace() and re.match(r'^(func|type|var|const)\b', ln):
            first_decl = i
            break
    if first_decl is None:
        print('no decls found')
        return
    header = lines[:first_decl]
    pkg_line = next((l for l in header if l.startswith('package ')), 'package main\n')
    # build tags must be preserved on EVERY emitted file
    build_tags = ''.join(
        l for l in header
        if l.startswith('//go:build') or l.startswith('// +build')
    )
    if build_tags and not build_tags.endswith('\n\n'):
        build_tags = build_tags.rstrip('\n') + '\n\n'
    # import blocks: capture from header
    htext = ''.join(header)
    imports = []
    for m in re.finditer(r'import\s*\(.*?\)\n?', htext, re.S):
        imports.append(m.group(0))
    for m in re.finditer(r'^import\s+"[^"]+"\n?', htext, re.M):
        imports.append(m.group(0))
    import_text = ''.join(imports)
    if not import_text.endswith('\n'):
        import_text += '\n'

    # scan decls
    decls = []
    i = first_decl
    while i < n:
        ln = lines[i]
        if ln.strip() == '' or (ln.startswith('//') or ln.startswith('/*')):
            i += 1
            continue
        if ln and not ln[0].isspace() and re.match(r'^(func|type|var|const)\b', ln):
            # attach preceding doc comment block
            start = i
            j = i - 1
            while j >= 0 and lines[j].lstrip().startswith('//'):
                start = j
                j -= 1
            end = decl_end(lines, i)
            decls.append((decl_name(ln), start, end))
            i = end
        else:
            i += 1

    order = list(spec.keys())
    buckets = {f: [] for f in order}
    buckets['__orig__'] = []
    for name, s, e in decls:
        target = '__orig__'
        for f in order:
            for p in spec[f]:
                if name == p or name.startswith(p) or name.endswith('.' + p):
                    target = f
                    break
            if target != '__orig__':
                break
        buckets[target].append((name, s, e))

    if not apply:
        for f in order + ['__orig__']:
            print(f'--- {f}: {len(buckets[f])} decls')
            for name, s, e in buckets[f]:
                print(f'    {name}  [{s + 1}-{e}]')
        return

    import os
    d = os.path.dirname(os.path.abspath(src))
    file_head = build_tags + pkg_line + '\n' + import_text + '\n'
    for f in order:
        if not buckets[f]:
            continue
        body = ''.join(''.join(lines[s:e]) for _, s, e in buckets[f])
        open(os.path.join(d, f), 'w').write(file_head + body)
        print(f'wrote {f} ({len(buckets[f])} decls)')
    # original keeps unassigned
    body = ''.join(''.join(lines[s:e]) for _, s, e in buckets['__orig__'])
    open(src, 'w').write(file_head + body)
    print(f'rewrote {src} ({len(buckets["__orig__"])} decls kept)')


main()
