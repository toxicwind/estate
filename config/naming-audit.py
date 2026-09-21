#!/usr/bin/env python3
"""Config naming-convention audit for sovereign-projects (repeatable).

Usage: python3 naming-audit.py /path/to/sovereign [--json]

Dimensions:
  env-case        ${env.name} must be UPPER_SNAKE (plain ${var} shell-style OK)
  env-undefined   ${env.X} in declarative configs must be defined in
                  ports.env / .secrets.example / profiles/default.yml, or be a
                  documented secret (see docs/config-naming-conventions.md)
  port-undefined  $X_PORT referenced but missing from config/ports.env
  port-unused     defined in ports.env but never referenced
  port-duplicate  one port number under two var names (skips documented
                  deprecated aliases)
  port-family     *_BACKEND_PORT mixed with *_HTTP_PORT/*_GRPC_PORT siblings
  port-literal    literal --port N in pitchfork.toml run lines (convention:
                  literal + SSOT comment; ${} expansion proved unreliable
                  2026-09-20 toolcall-llm stoi crash)
  herd-peer-case  peer names must be kebab-case
  herd-route-dup  duplicate model alias under models:
  daemon-id       daemon ids use dashes, not underscores

Exit 0 always (report, don't fail); --json for machine consumption.
"""
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
AS_JSON = "--json" in sys.argv

# The yote sovereign config surface. Shell-script locals elsewhere are NOT
# config naming -- excluded by design.
SCOPE_DIRS = ("config", "profiles", "stack", "hatch")
SCOPE_FILES = ("pitchfork.toml",)
ENV_DECL_EXTS = (".yaml", ".yml", ".toml")


def in_scope(path):
    rel = os.path.relpath(path, ROOT)
    if rel in SCOPE_FILES:
        return True
    return rel.split(os.sep)[0] in SCOPE_DIRS


def scoped_files(exts):
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for f in filenames:
            p = os.path.join(dirpath, f)
            if f == "naming-audit.py":
                continue  # never audit the auditor's own docstrings
            if f.endswith(exts) and in_scope(p):
                out.append(p)
    return out


findings = []


def note(sev, dim, msg):
    findings.append({"severity": sev, "dimension": dim, "message": msg})


def rel(p):
    return os.path.relpath(p, ROOT)

# ---- 1. env references in declarative configs ------------------------------
env_refs = {}
rx_env = re.compile(r"\$\{env\.([A-Za-z_][A-Za-z0-9_]*)\}")
for f in scoped_files(ENV_DECL_EXTS):
    try:
        for i, line in enumerate(open(f, encoding="utf-8",
                                      errors="replace"), 1):
            for v in rx_env.findall(line):
                env_refs.setdefault(v, []).append("%s:%d" % (rel(f), i))
    except OSError:
        pass

defined = {}
yaml_macro_keys = set()  # same-file YAML anchors/macros (e.g. SRV_PORT:)
for name in ("config/ports.env", ".secrets.example", "profiles/default.yml",
             "config/herd.yaml"):
    p = os.path.join(ROOT, name)
    if not os.path.isfile(p):
        continue
    for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]", line)
        if m:
            defined.setdefault(m.group(1), []).append("%s:%d" % (name, i))
            if name.endswith((".yaml", ".yml")):
                yaml_macro_keys.add(m.group(1))

# documented secret names (values live in /home/toxic/.secrets, never here)
DOCUMENTED_SECRETS = {"HF_TOKEN", "MISTRAL_API_KEY", "MOONSHOT_API_KEY",
                      "OPENROUTER_API_KEY", "OPENROUTER_API_KEY_1",
                      "OPENROUTER_API_KEY_FREE", "FLOCK_API_KEY",
                      "GEMINI_API_KEY", "NVIDIA_API_KEY", "GITHUB_TOKEN"}

for v, locs in sorted(env_refs.items()):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", v):
        note("warn", "env-case",
             "non-UPPER_SNAKE ${env.%s} at %s" % (v, locs[0]))
    if v not in defined and v not in DOCUMENTED_SECRETS \
            and v not in yaml_macro_keys:
        note("error", "env-undefined",
             "${env.%s} at %s: not in ports.env/.secrets.example/profiles"
             % (v, locs[0]))

# ---- 2. port vars -----------------------------------------------------------
port_defs = {}
dup_values = {}
ports_env = os.path.join(ROOT, "config/ports.env")
if os.path.isfile(ports_env):
    prev_comment = ""
    for i, line in enumerate(open(ports_env, encoding="utf-8",
                                  errors="replace"), 1):
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9]+)(.*)$",
                     line)
        if m:
            name, val, rest = m.group(1), int(m.group(2)), m.group(3)
            # attach standalone comment lines directly above the definition
            # (e.g. "# NULL_G_PORT kept as deprecated alias")
            port_defs[name] = (val, i, rest + " " + prev_comment)
            dup_values.setdefault(val, []).append(name)
            prev_comment = ""
        else:
            cm = re.match(r"^\s*#\s*(.*)$", line)
            prev_comment = cm.group(1) if cm else ""

PORT_TOKEN = r"[A-Z][A-Z0-9_]*_PORT(?![A-Z])"

port_refs = {}
rx_dollar = re.compile(r"\$\{(" + PORT_TOKEN + r")}"
                       r"|\$(" + PORT_TOKEN + r")")
rx_require = re.compile(r"require_(?:port|env)\s+(" + PORT_TOKEN + r")")
rx_toml_env = re.compile(r"env\s*=\s*\{([^}]*)\}")
# daemon env tables are DEFINITION sites (pitchfork [daemons.x] env = {...})
toml_env_defs = {}
for f in scoped_files((".toml",)):
    try:
        text = open(f, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    for i, line in enumerate(text.split("\n"), 1):
        for blk in rx_toml_env.findall(line):
            for v in re.findall(r"\b(" + PORT_TOKEN + r")\b",
                                blk):
                toml_env_defs.setdefault(v, []).append("%s:%d" % (rel(f), i))
for v, locs in toml_env_defs.items():
    defined.setdefault(v, locs)
for f in scoped_files((".yaml", ".yml", ".toml", ".sh", ".py")):
    try:
        text = open(f, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    local_assigns = set(re.findall(r"^\s*(" + PORT_TOKEN + r")\s*=",
                                   text, re.M))
    if f.endswith((".yaml", ".yml")):
        # same-file YAML macro keys (SRV_PORT: ...) are local definitions
        local_assigns |= set(re.findall(
            r"^\s*(" + PORT_TOKEN + r")\s*:", text, re.M))
    for i, line in enumerate(text.split("\n"), 1):
        for a, b in rx_dollar.findall(line):
            v = a or b
            if v and v not in local_assigns:
                port_refs.setdefault(v, []).append("%s:%d" % (rel(f), i))
        for v in rx_require.findall(line):
            port_refs.setdefault(v, []).append("%s:%d" % (rel(f), i))

# consumers: os.environ.get("X_PORT") / os.getenv / ENV["X_PORT"] in .py.
# Scanned across the sovereign runtime dirs only -- projects/*/ scratch/
# are separate codebases with their own port config, not the SSOT.
CONSUMER_DIRS = ("config", "profiles", "stack", "hatch", "bridge", "tools")
rx_pyenv = re.compile(
    r"os\.environ(?:\.get)?\(\s*['\"](%s)['\"]" % PORT_TOKEN
    + r"|os\.getenv\(\s*['\"](%s)['\"]" % PORT_TOKEN
    + r"|ENV\[\s*['\"](%s)['\"]" % PORT_TOKEN)
for dirpath, dirnames, files in os.walk(ROOT):
    if ".git" in dirnames:
        dirnames.remove(".git")
    _rel = os.path.relpath(dirpath, ROOT).split(os.sep)[0]
    if _rel not in CONSUMER_DIRS and dirpath != ROOT:
        dirnames[:] = []
        continue
    for fn in files:
        if not fn.endswith(".py"):
            continue
        if fn == "naming-audit.py":
            continue  # never audit the auditor's own docstrings
        p = os.path.join(dirpath, fn)
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for i, line in enumerate(text.split("\n"), 1):
            for groups in rx_pyenv.findall(line):
                v = next(g for g in groups if g)
                port_refs.setdefault(v, []).append("%s:%d" % (rel(p), i))

for v, locs in sorted(port_refs.items()):
    if v not in port_defs:
        note("error", "port-undefined",
             "$%s at %s: missing from config/ports.env" % (v, locs[0]))

for name, (val, line, _rest) in sorted(port_defs.items()):
    if name not in port_refs:
        note("info", "port-unused",
             "%s=%d (ports.env:%d) defined but never referenced"
             % (name, val, line))

for val, names in sorted(dup_values.items()):
    if len(names) > 1:
        comments = " ".join(port_defs[n][2] for n in names).lower()
        if "deprecat" in comments or "alias" in comments \
                or "daemon-local" in comments:
            continue  # documented alias/twin, intentional
        note("warn", "port-duplicate",
             "port %d under multiple vars: %s" % (val, ", ".join(names)))

families = {}
for name in port_defs:
    base = re.sub(r"_(BACKEND|HTTP|GRPC|WS)_PORT$", "", name)
    if base != name:
        families.setdefault(base, []).append(name)
for base, members in sorted(families.items()):
    kinds = {m.rsplit("_", 2)[-2] for m in members}
    if "BACKEND" in kinds and kinds & {"HTTP", "GRPC"}:
        note("warn", "port-family",
             "%s mixes BACKEND_PORT with HTTP/GRPC_PORT: %s"
             % (base, ", ".join(members)))

pt = os.path.join(ROOT, "pitchfork.toml")
if os.path.isfile(pt):
    for i, line in enumerate(open(pt, encoding="utf-8",
                                  errors="replace"), 1):
        for m in re.finditer(r"--port\s+(\d{4,5})", line):
            if "SSOT" in line:
                continue  # convention met: literal + SSOT comment
            note("info", "port-literal",
                 "pitchfork.toml:%d literal --port %s "
                 "without SSOT comment (convention: literal + SSOT comment)"
                 % (i, m.group(1)))

# ---- 3. herd.yaml ------------------------------------------------------------
herd = os.path.join(ROOT, "config/herd.yaml")
if os.path.isfile(herd):
    lines = open(herd, encoding="utf-8", errors="replace").read().split("\n")
    section = None
    peers, routes = [], []
    seen_routes = {}
    for l in lines:
        m = re.match(r"^([a-z_]+):$", l)
        if m:
            section = m.group(1)
            continue
        if section == "peers":
            m = re.match(r"^  ([A-Za-z0-9_-]+):$", l)
            if m:
                peers.append(m.group(1))
        elif section == "models":
            m = re.match(r"^  ([A-Za-z0-9_.-]+):$", l)
            if m:
                routes.append(m.group(1))
                seen_routes[m.group(1)] = seen_routes.get(m.group(1), 0) + 1
    for p in peers:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", p):
            note("warn", "herd-peer-case", "peer not kebab-case: %s" % p)
    for r, n in sorted(seen_routes.items()):
        if n > 1:
            note("error", "herd-route-dup",
                 "model alias %r defined %d times" % (r, n))
    for r in routes:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", r):
            note("warn", "herd-route-case", "model alias not kebab/snake: %s"
                 % r)

# ---- 4. pitchfork daemon ids ---------------------------------------------------
if os.path.isfile(pt):
    for m in re.finditer(r"\[daemons\.([a-zA-Z0-9_-]+)\]",
                         open(pt, encoding="utf-8",
                              errors="replace").read()):
        d = m.group(1)
        if "_" in d:
            note("warn", "daemon-id",
                 "daemon id uses underscores (convention: dashes): %s" % d)

counts = {}
for f in findings:
    counts[f["severity"]] = counts.get(f["severity"], 0) + 1
out = {"root": ROOT, "counts": counts, "findings": findings}
if AS_JSON:
    print(json.dumps(out, indent=2))
else:
    print("naming-audit %s: %d findings "
          "(errors=%d warnings=%d info=%d)"
          % (ROOT, len(findings), counts.get("error", 0),
             counts.get("warn", 0), counts.get("info", 0)))
    for sev in ("error", "warn", "info"):
        for f in findings:
            if f["severity"] == sev:
                print("[%s] %s: %s" % (sev.upper(), f["dimension"],
                                       f["message"]))
