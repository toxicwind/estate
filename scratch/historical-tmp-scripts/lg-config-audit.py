#!/usr/bin/env python3
"""Config naming-convention audit for sovereign-projects.

Dimensions:
  1. env vars: ${env.X} references vs defined vars (ports.env, .secrets.example,
     profiles/default.yml) -- case convention, missing defs, dead defs.
  2. port vars: *_PORT naming families in config/ports.env vs consumers
     (pitchfork.toml, stack/services/*.sh, config/herd.yaml) -- missing,
     unused, duplicate values, inconsistent suffix families.
  3. herd.yaml: peer names, modelMap route names, model id conventions.
  4. pitchfork.toml daemon ids vs ports actually referenced.

Read-only. Prints findings; exits 0 unless --json given (then prints JSON).
Usage: python3 config_naming_audit.py /tmp/lg-wt [--json]
"""
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
AS_JSON = "--json" in sys.argv

findings = []  # (severity, dimension, message)


def note(sev, dim, msg):
    findings.append({"severity": sev, "dimension": dim, "message": msg})


# Scope: the yote sovereign config surface only. Shell-script locals in
# projects/, ops/, tools/ are NOT config naming -- exclude them.
SCOPE_DIRS = ("config", "profiles", "stack", "hatch")
SCOPE_FILES = ("pitchfork.toml",)


def in_scope(path):
    rel = os.path.relpath(path, ROOT)
    if rel in SCOPE_FILES:
        return True
    return rel.split(os.sep)[0] in SCOPE_DIRS


def files_with(root, exts):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for f in filenames:
            p = os.path.join(dirpath, f)
            if any(f.endswith(e) for e in exts) and in_scope(p):
                out.append(p)
    return out


def grep_files(root, exts, pattern):
    rx = re.compile(pattern)
    hits = []
    for f in files_with(root, exts):
        try:
            for i, line in enumerate(
                    open(f, encoding="utf-8", errors="replace"), 1):
                m = rx.findall(line)
                if m:
                    hits.append((f, i, m))
        except OSError:
            pass
    return hits


# ---- 1. env var references -------------------------------------------------
# env-undefined applies ONLY to declarative configs (yaml/toml). In .sh
# files ${VAR} is just a shell local, not a config reference -- port vars
# in .sh are covered separately by the port-var dimension.
ENV_DECL_EXTS = (".yaml", ".yml", ".toml")


def grep_env_refs(root):
    rx = re.compile(r"\$\{(?:env\.)?([A-Za-z_][A-Za-z0-9_]*)\}")
    hits = []
    for f in files_with(root, ENV_DECL_EXTS):
        try:
            for i, line in enumerate(
                    open(f, encoding="utf-8", errors="replace"), 1):
                for v in rx.findall(line):
                    hits.append((f, i, v))
        except OSError:
            pass
    return hits


env_refs = {}
for f, i, v in grep_env_refs(ROOT):
    env_refs.setdefault(v, []).append("%s:%d" % (f, i))

defined = {}
for name in ("config/ports.env", "config/ports.env.example",
             ".secrets.example", "profiles/default.yml",
             "config/herd.yaml"):
    p = os.path.join(ROOT, name)
    if not os.path.isfile(p):
        continue
    for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]", line)
        if m:
            defined.setdefault(m.group(1), []).append("%s:%d" % (name, i))

SKIP = {"HOME", "USER", "PATH", "PWD", "SHELL", "HOSTNAME", "UID"}
for v, locs in sorted(env_refs.items()):
    if v in SKIP:
        continue
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", v):
        note("warn", "env-case",
             "non-UPPER_SNAKE env reference ${env.%s} at %s" % (v, locs[0]))
    if v not in defined and v not in os.environ:
        note("error", "env-undefined",
             "${env.%s} referenced at %s but not defined in any config file"
             % (v, locs[0]))

# ---- 2. port vars -----------------------------------------------------------
ports_env = os.path.join(ROOT, "config/ports.env")
port_defs = {}
dup_values = {}
if os.path.isfile(ports_env):
    for i, line in enumerate(
            open(ports_env, encoding="utf-8", errors="replace"), 1):
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9]+)", line)
        if m:
            name, val = m.group(1), int(m.group(2))
            port_defs[name] = (val, i)
            dup_values.setdefault(val, []).append(name)

port_refs = {}
for f, i, ms in grep_files(ROOT, (".yaml", ".yml", ".toml", ".sh", ".py"),
                           r"\$\{([A-Z][A-Z0-9_]*PORT[A-Z0-9_]*)\}|\$([A-Z][A-Z0-9_]*_PORT[A-Z0-9_]*)"):
    for a, b in ms:
        v = a or b
        if v:
            port_refs.setdefault(v, []).append("%s:%d" % (f, i))

for v, locs in sorted(port_refs.items()):
    if v not in port_defs:
        note("error", "port-undefined",
             "port var $%s referenced at %s but missing from config/ports.env"
             % (v, locs[0]))

for name, (val, line) in sorted(port_defs.items()):
    if name not in port_refs and not name.endswith("_PORT"):
        continue
    if name not in port_refs:
        note("info", "port-unused",
             "%s=%d (ports.env:%d) defined but never referenced" % (name, val, line))

for val, names in sorted(dup_values.items()):
    if len(names) > 1:
        note("warn", "port-duplicate",
             "port %d assigned to multiple vars: %s" % (val, ", ".join(names)))

# suffix-family consistency: *_BACKEND_PORT vs *_HTTP_PORT vs *_GRPC_PORT
families = {}
for name in port_defs:
    base = re.sub(r"_(BACKEND|HTTP|GRPC|WS)_PORT$", "", name)
    if base != name:
        families.setdefault(base, []).append(name)
for base, members in sorted(families.items()):
    kinds = sorted(m.rsplit("_", 2)[-2] for m in members)
    if "BACKEND" in kinds and ("HTTP" in kinds or "GRPC" in kinds):
        note("warn", "port-family",
             "%s mixes BACKEND_PORT with HTTP/GRPC_PORT: %s"
             % (base, ", ".join(members)))

# literal ports in pitchfork.toml run lines (should use ${PORT} vars)
pt = os.path.join(ROOT, "pitchfork.toml")
if os.path.isfile(pt):
    for i, line in enumerate(open(pt, encoding="utf-8", errors="replace"), 1):
        for m in re.finditer(r"--port\s+(\d{4,5})", line):
            note("info", "port-literal",
                 "pitchfork.toml:%d literal --port %s (prefer ${..._PORT})"
                 % (i, m.group(1)))

# ---- 3. herd.yaml naming ----------------------------------------------------
herd = os.path.join(ROOT, "config/herd.yaml")
if os.path.isfile(herd):
    txt = open(herd, encoding="utf-8", errors="replace").read()
    peers = re.findall(r"^\s{2}([a-z0-9][a-z0-9_-]*):\s*$", txt, re.M)
    for p in peers:
        if re.search(r"[A-Z]", p):
            note("warn", "herd-peer-case", "peer name has uppercase: %s" % p)
    routes = re.findall(r"^\s{4,}([a-z0-9][a-z0-9_.-]*):\s*(?:#.*)?$", txt,
                        re.M)
    seen = {}
    for r in routes:
        seen[r] = seen.get(r, 0) + 1
    for r, n in sorted(seen.items()):
        if n > 1:
            note("warn", "herd-route-dup",
                 "route name %r defined %d times" % (r, n))
    for mid in re.findall(r"model:\s*([^\s#]+)", txt):
        if "/" not in mid and ":" not in mid and not mid.startswith("${"):
            note("info", "herd-model-id",
                 "bare model id without provider prefix: %s" % mid)

# ---- 4. pitchfork daemon ids --------------------------------------------------
if os.path.isfile(pt):
    ids = re.findall(r"\[\[?daemons?\]?\.?([a-z0-9][a-z0-9_-]*)\]?\]?", txt
                     if False else open(pt, encoding="utf-8",
                                        errors="replace").read())
    for d in ids:
        if "_" in d:
            note("warn", "daemon-id",
                 "daemon id uses underscores (fleet convention is dashes): %s"
                 % d)

out = {"root": ROOT, "counts": {}, "findings": findings}
for f in findings:
    out["counts"][f["severity"]] = out["counts"].get(f["severity"], 0) + 1

if AS_JSON:
    print(json.dumps(out, indent=2))
else:
    print("audit of %s: %d findings" % (ROOT, len(findings)))
    for sev in ("error", "warn", "info"):
        for f in findings:
            if f["severity"] == sev:
                print("[%s] %s: %s" % (sev.upper(), f["dimension"],
                                       f["message"]))
