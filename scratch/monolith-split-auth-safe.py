#!/usr/bin/env python3
"""Surgical splitter for tau/engine/packages/ai/src/auth-storage.ts (7359 lines).

Moves whole declaration regions VERBATIM into src/auth/*.ts modules.
auth-storage.ts keeps the AuthStorage class + in-memory types + re-exports.
No rewriting: only relocation + import/export bookkeeping.
"""
import re, os, sys

SRC = "/home/toxic/sovereign/tau/engine/packages/ai/src"
PATH = os.path.join(SRC, "auth-storage.ts")
lines = open(PATH).read().split("\n")

def rng(a, b):
    return "\n".join(lines[a - 1:b])

KEYWORDS = set("""const let var function class interface type enum return if else for
while new typeof extends implements import export from as readonly private public
protected static async await true false null undefined this super void never unknown
any string number boolean object symbol bigint infer keyof in of delete instanceof
switch case default break continue do try catch finally throw with debugger declare
abstract override satisfies asserts global namespace module require get set constructor Array Map Set WeakMap Promise JSON Math Date Object Number String Boolean Error AbortSignal AbortController URL TextEncoder TextDecoder crypto fetch console process __dirname""".split())

# (module filename, [(start,end)], title)
MODULES = [
    ("auth/storage-contract.ts",
     [(109, 646)],
     "Credential and storage contract types (ApiKeyCredential, OAuthCredential, AuthCredentialStore, AuthStorageOptions, ...)."),
    ("auth/usage-metrics.ts",
     [(81, 87), (660, 684), (747, 844), (1030, 1156)],
     "Usage ranking/metrics: plan classification, ranking strategies, usage-limit and usage-health types."),
    ("auth/usage-cache-impl.ts",
     [(686, 718), (1157, 1279)],
     "In-memory usage cache implementation (AuthStorageUsageCache + entry parsing/racing helpers)."),
    ("auth/oauth-refresh-support.ts",
     [(88, 103), (719, 743), (845, 1028)],
     "OAuth refresh support: bearer fingerprinting, refresh timeouts, OAuth access/identity and reset-credit types."),
]

DECL_RE = re.compile(r'^(export\s+)?(const|let|var|function|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)', re.M)
EXPORT_LIST_RE = re.compile('export\\s*\\{([^}]*)\\}\\s*(?:from\\s*["\\\'][^"\\\']*["\\\'])?\\s*;?', re.M)
IMPORT_RE = re.compile(r'import\s+(type\s+)?([\s\S]*?)\s+from\s*["\']([^"\']+)["\']\s*;')

def parse_imports(head_text):
    out = []  # (is_type_stmt, spec, [(name, is_type)])
    for m in IMPORT_RE.finditer(head_text):
        tstmt = bool(m.group(1))
        clause, spec = m.group(2).strip(), m.group(3)
        names = []
        if clause.startswith("* as"):
            names.append((clause[4:].strip(), False))
        elif clause.startswith("{"):
            inner = clause[1:clause.rfind("}")]
            for part in inner.split(","):
                part = part.strip()
                if not part:
                    continue
                tm = re.match(r'type\s+(\w+)(?:\s+as\s+(\w+))?$', part)
                if tm:
                    names.append((tm.group(2) or tm.group(1), True))
                    continue
                am = re.match(r'(\w+)\s+as\s+(\w+)$', part)
                if am:
                    names.append((am.group(2), False))
                    continue
                names.append((part, tstmt))
        else:
            names.append((clause, False))
        out.append((tstmt, spec, names))
    return out

def declared_names(text):
    d = {}
    for m in DECL_RE.finditer(text):
        exported = bool(m.group(1))
        kind, name = m.group(2), m.group(3)
        d[name] = (kind in ("interface", "type"), exported, kind)
    for m in EXPORT_LIST_RE.finditer(text):
        for part in m.group(1).split(","):
            part = part.strip()
            if not part:
                continue
            am = re.match(r'(\w+)\s+as\s+(\w+)$', part)
            name = am.group(2) if am else part.split()[0]
            d.setdefault(name, (False, True, "reexport"))
    return d

def code_only(s):
    out = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            j = s.find("\n", i)
            out.append("\n")
            i = n if j < 0 else j + 1
        elif c == "/" and i + 1 < n and s[i + 1] == "*":
            j = s.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in ("\"", "'"):
            q = c
            j = i + 1
            while j < n and s[j] != q:
                j += 2 if s[j] == "\\" else 1
            i = j + 1
        elif c == chr(96):
            j = i + 1
            buf = []
            while j < n:
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == chr(96):
                    break
                if s[j] == "$" and j + 1 < n and s[j + 1] == "{":
                    k = j + 2
                    d = 1
                    while k < n and d:
                        if s[k] == "{":
                            d += 1
                        elif s[k] == "}":
                            d -= 1
                        k += 1
                    buf.append(s[j + 2:k - 1])
                    j = k
                    continue
                j += 1
            out.append(" " + " ".join(buf) + " ")
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)

IDENT_RE = re.compile(r'\b[A-Za-z_$][\w$]*\b')

def referenced_names(text):
    return set(IDENT_RE.findall(code_only(text))) - KEYWORDS

def add_exports(body):
    out = []
    for line in body.split("\n"):
        m = DECL_RE.match(line)
        if m and not m.group(1):
            line = "export " + line
        out.append(line)
    return "\n".join(out)

def rewrite_spec(spec):
    if spec.startswith("./auth/"):
        return "./" + spec[len("./auth/"):]
    if spec.startswith("./"):
        return "../" + spec[2:]
    return spec

# ---- gather original import table ----
head = rng(1, 103)
orig_imports = parse_imports(head)
name_to_import = {}
for tstmt, spec, names in orig_imports:
    for n, it in names:
        name_to_import[n] = (tstmt or it, spec)  # (is_type, spec)

# ---- collect moved declarations ----
moved = {}  # name -> (module_rel_from_src, is_type, was_exported)
mod_bodies = {}
for fname, ranges, title in MODULES:
    body = "\n\n".join(rng(a, b).strip("\n") for a, b in ranges)
    mod_bodies[fname] = body
    for name, (is_type, was_exported, kind) in declared_names(body).items():
        if name in moved:
            print("DUPLICATE MOVED NAME: %s" % name)
            sys.exit(1)
        moved[name] = (fname, is_type, was_exported)

# ---- build each module ----
for fname, ranges, title in MODULES:
    body = mod_bodies[fname]
    decls = declared_names(body)
    refs = referenced_names(body) - set(decls)
    need = {}  # name -> (is_type, spec)
    for r in refs:
        if r in name_to_import:
            it, spec = name_to_import[r]
            need[r] = (it, rewrite_spec(spec))
        elif r in moved and moved[r][0] != fname:
            need[r] = (moved[r][1], "./" + os.path.basename(moved[r][0])[:-3])
        elif r in moved:
            pass
        # else: global / declared-later-in-same-region handled by decls
    missing = [r for r in refs if r not in name_to_import and r not in decls and not (r in moved and moved[r][0] != fname)]
    groups = {}
    for r, (it, spec) in sorted(need.items()):
        groups.setdefault((spec, it), []).append(r)
    imp_lines = []
    for (spec, it), names in sorted(groups.items()):
        kw = "import type " if it else "import "
        imp_lines.append("%s{ %s } from %s;" % (kw, ", ".join(names), '"%s"' % spec))
    header = ("/**\n * %s\n *\n * Extracted verbatim from auth-storage.ts (surgical split 2026-09-14).\n"
              " * Re-exported through auth-storage.ts; import from there.\n */\n" % title)
    content = header + ("\n".join(imp_lines) + "\n\n" if imp_lines else "\n") + add_exports(body) + "\n"
    dest = os.path.join(SRC, fname)
    open(dest, "w").write(content)
    print("wrote %s (%d lines, %d imports)" % (dest, content.count("\n"), len(imp_lines)))
    if missing:
        print("  WARNING unresolved refs: %s" % ", ".join(sorted(missing)))

# ---- rebuild auth-storage.ts ----
keep_ranges = [(1, 103), (649, 659), (744, 746), (1280, len(lines))]
kept = "\n\n".join(rng(a, b).strip("\n") for a, b in keep_ranges)
kept_decls = declared_names(kept)
kept_refs = referenced_names(kept) - set(kept_decls)
need_imp = {}
for r in kept_refs:
    if r in name_to_import:
        continue  # already imported in head
    if r in moved:
        need_imp[r] = moved[r]
    # else global

groups = {}
for r, (modf, is_type, was_exp) in sorted(need_imp.items()):
    spec = "./" + modf[:-3]
    groups.setdefault((spec, is_type), []).append(r)
imp_lines = []
for (spec, it), names in sorted(groups.items()):
    kw = "import type " if it else "import "
    imp_lines.append("%s{ %s } from %s;" % (kw, ", ".join(names), '"%s"' % spec))

reexp_lines = []
for fname, ranges, title in MODULES:
    body = mod_bodies[fname]
    for name, (is_type, was_exported, kind) in sorted(declared_names(body).items()):
        if was_exported:
            kw = "export type " if is_type else "export "
            reexp_lines.append("%s{ %s } from %s;" % (kw, name, '"./%s"' % fname[:-3]))

anchor = 'export { isSqliteBusyError, isSqliteCorruptionError, SqliteAuthCredentialStore } from "./auth/sqlite-credential-store";'
assert anchor in kept, "anchor export line missing"
insert = "\n".join(imp_lines)
reexp = "\n".join(reexp_lines)
kept = kept.replace(anchor, anchor + ("\n\n" + insert if insert else "") + "\n\n// Re-exports of the extracted modules above (public surface unchanged).\n" + reexp)

# docblock touch: note the split
kept = kept.replace(
    " * - re-exported SqliteAuthCredentialStore: concrete SQLite-backed implementation\n */",
    " * - re-exported SqliteAuthCredentialStore: concrete SQLite-backed implementation\n *\n * Supporting declarations were extracted verbatim into ./auth/ modules\n * (storage-contract, usage-metrics, usage-cache-impl, oauth-refresh-support)\n * and are re-exported here; the public surface is unchanged.\n */")

open(PATH, "w").write(kept + "\n")
print("rewrote %s (%d lines)" % (PATH, kept.count("\n") + 1))
print("auth-storage.ts new imports: %d, re-exports: %d" % (len(imp_lines), len(reexp_lines)))
