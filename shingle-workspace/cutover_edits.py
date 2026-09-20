#!/usr/bin/env python3
"""Mise-native cutover edits for /home/toxic/sovereign (2026-09-14).
Idempotent string replacements. Run on awrawr-pc via the bridge.
"""
import sys

SOV = "/home/toxic/sovereign"

def patch(path, old, new, count=1):
    with open(path) as f:
        content = f.read()
    found = content.count(old)
    if found != count:
        print(f"FAIL: {path}: expected {count} occurrence(s), found {found} of: {old[:70]!r}")
        sys.exit(1)
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print(f"OK: {path}: {old[:50]!r}...")

# ── 1. coyote-loop.py: secrets + model via env, never argv ──────────────
PY = f"{SOV}/src/coyote/coyote-loop.py"
patch(PY,
      'p.add_argument("--api-key", default="sk-hal-local")',
      'p.add_argument("--api-key", default=os.environ.get("COYOTE_API_KEY", "sk-hal-local"))')
patch(PY,
      'p.add_argument("--model", "-m", default="kimi-auto")',
      'p.add_argument("--model", "-m", default=os.environ.get("COYOTE_MODEL", "kimi-auto"))')

# ── 2. coyote.sh: export key/model, drop --api-key from argv ─────────────
SH = f"{SOV}/stack/services/coyote.sh"
patch(SH,
      'PORT="$COYOTE_PORT"\n',
      'PORT="$COYOTE_PORT"\n'
      '# Secret hygiene: key travels via env, never argv (invisible to ps).\n'
      'export COYOTE_API_KEY="${COYOTE_API_KEY:-sk-hal-local}"\n'
      'export COYOTE_MODEL="${COYOTE_MODEL:-kimi-auto}"\n')
patch(SH,
      '  --base-url "http://127.0.0.1:25100" \\\n  --api-key "sk-hal-local" \\\n  --model "kimi-auto" \\\n',
      '  --base-url "http://127.0.0.1:25100" \\\n  --model "${COYOTE_MODEL}" \\\n')

# ── 3. pitchfork.toml ────────────────────────────────────────────────────
PF = f"{SOV}/pitchfork.toml"
patch(PF,
      "# SOVEREIGN PITCHFORK CONFIG \u2014 GENERATED from config/ports.env + service definitions\n# DO NOT EDIT DIRECTLY \u2014 Run: bun run scripts/generate.ts",
      "# SOVEREIGN PITCHFORK CONFIG \u2014 MISE-NATIVE (cutover 2026-09-14)\n# Owned directly: edit this file. scripts/generate.ts is retired for\n# service definitions; do not regenerate from it.")
# boot_start for the 13 daemons that must come up at supervisor boot
for daemon in ["herd", "qdrant", "redis", "kafka", "dnsmasq", "coyote",
               "tau-code", "prometheus", "grafana", "mesh-hub",
               "nginx", "nim-proxy", "matter-server"]:
    if daemon in ("nim-proxy", "matter-server"):
        continue  # added below with boot_start included
    marker = f"[daemons.{daemon}]\n"
    with open(PF) as f:
        content = f.read()
    start = content.index(marker)
    # insert boot_start after the retry line within this daemon block
    retry_at = content.index("retry = true", start)
    # make sure we are still inside this daemon's block (before next [daemons. or [groups.)
    next_section = content.find("\n[", start + 1)
    if not (start < retry_at < next_section):
        print(f"FAIL: {PF}: retry line misplaced for {daemon}")
        sys.exit(1)
    eol = content.index("\n", retry_at) + 1
    content = content[:eol] + "boot_start = true\n" + content[eol:]
    with open(PF, "w") as f:
        f.write(content)
    print(f"OK: {PF}: boot_start -> {daemon}")

# groups: drop dangling build-server, add the three peripheral daemons
for group in ("all", "sovereign-core"):
    patch(PF,
          f'[groups.{group}]\ndaemons = ["herd", "qdrant", "redis", "kafka", "coyote", "yote", "search-api", "search-ui", "mesh-hub", "axiom", "rust-web", "hf-downloader", "null-g-proxy", "kimi-audit-dash", "mcp-gateway", "byte-vision", "hindsight", "prometheus", "grafana", "tau", "tau-code", "kimi-code", "mesh", "dnsmasq", "build-server"]',
          f'[groups.{group}]\ndaemons = ["herd", "qdrant", "redis", "kafka", "coyote", "yote", "search-api", "search-ui", "mesh-hub", "axiom", "rust-web", "hf-downloader", "null-g-proxy", "kimi-audit-dash", "mcp-gateway", "byte-vision", "hindsight", "prometheus", "grafana", "tau", "tau-code", "kimi-code", "mesh", "dnsmasq", "nginx", "nim-proxy", "matter-server"]')

# new daemon definitions before [groups.core]
new_daemons = '''[daemons.nim-proxy]
run = "exec docker run --rm --name nim-proxy -p 127.0.0.1:8000:8000 -v nim-proxy-data:/data -e DATA_DIR=/data ghcr.io/miztertea/nim-proxy:latest"
dir = "."
mise = false
retry = true
ready_cmd = "ss -ltn 'sport = :8000' | grep -q LISTEN"
boot_start = true
env = {
  NIM_PROXY_PORT = "8000",
}
auto = ["start"]

[daemons.matter-server]
run = "exec docker run --rm --name matter-server --net host -v /home/toxic/.matter_data:/data -v /run/dbus:/run/dbus:ro -e BLUETOOTH_ADAPTER=0 -e STORAGE_PATH=/data -e LOG_LEVEL=info ghcr.io/matter-js/matterjs-server:stable --storage-path /data --bluetooth-adapter 0"
dir = "."
mise = false
retry = true
ready_cmd = "ss -ltn 'sport = :5580' | grep -q LISTEN"
boot_start = true
env = {
  MATTER_SERVER_PORT = "5580",
}
auto = ["start"]

'''
patch(PF, "[groups.core]\n", new_daemons + "[groups.core]\n")

# ── 4. mise.toml ─────────────────────────────────────────────────────────
MT = f"{SOV}/mise.toml"
patch(MT,
      "# SOVEREIGN MISE CONFIG \u2014 GENERATED from config/ports.env + service definitions\n# DO NOT EDIT DIRECTLY \u2014 Run: bun run scripts/generate.ts",
      "# SOVEREIGN MISE CONFIG \u2014 MISE-NATIVE (cutover 2026-09-14)\n# Owned directly: edit this file. scripts/generate.ts is retired for\n# service definitions; do not regenerate from it.")
patch(MT, 'pitchfork = "2.16.0"', 'pitchfork = "2.25.0"')
# group syntax: start/restart take --group, not a positional group name
patch(MT, 'up = "pitchfork start -q core"', 'up = "pitchfork start -q --group core"')
patch(MT, '"up:all" = "pitchfork start -q all"', '"up:all" = "pitchfork start -q --group all"')
patch(MT, 'restart = "pitchfork restart -q core"', 'restart = "pitchfork restart -q --group core"')
# kafka health: TCP, not HTTP (binary protocol port)
patch(MT,
      '"health-kafka" = "curl -sf --max-time 5 http://127.0.0.1:25144/health"',
      '"health-kafka" = "bash -c \'exec 3<>/dev/tcp/127.0.0.1/25144\'"')
# [vars] before [tasks]
patch(MT,
      "\n[tasks]\n",
      '\n[vars]\n# Canonical ports for natively-managed peripheral daemons\n# (shell service scripts still source config/ports.env via stack/lib-ports.sh)\nNGINX_PORT = "62200"\nNIM_PROXY_PORT = "8000"\nMATTER_SERVER_PORT = "5580"\n\n[tasks]\n')
# per-daemon tasks for the newly managed daemons
patch(MT,
      '"up-mesh" = "pitchfork start -q mesh"\n',
      '"up-mesh" = "pitchfork start -q mesh"\n'
      '"up-nginx" = "pitchfork start -q nginx"\n'
      '"up-nim-proxy" = "pitchfork start -q nim-proxy"\n'
      '"up-matter-server" = "pitchfork start -q matter-server"\n')
patch(MT,
      '"down-mesh" = "pitchfork stop mesh"\n',
      '"down-mesh" = "pitchfork stop mesh"\n'
      '"down-nginx" = "pitchfork stop nginx"\n'
      '"down-nim-proxy" = "pitchfork stop nim-proxy"\n'
      '"down-matter-server" = "pitchfork stop matter-server"\n')
patch(MT,
      '"restart-mesh" = "pitchfork restart -q mesh"\n',
      '"restart-mesh" = "pitchfork restart -q mesh"\n'
      '"restart-nginx" = "pitchfork restart -q nginx"\n'
      '"restart-nim-proxy" = "pitchfork restart -q nim-proxy"\n'
      '"restart-matter-server" = "pitchfork restart -q matter-server"\n')
patch(MT,
      '"health-mesh" = "curl -sf --max-time 5 http://127.0.0.1:25127/health"\n',
      '"health-mesh" = "curl -sf --max-time 5 http://127.0.0.1:25127/health"\n'
      '"health-nginx" = "bash -c \'exec 3<>/dev/tcp/127.0.0.1/62200\'"\n'
      '"health-nim-proxy" = "bash -c \'exec 3<>/dev/tcp/127.0.0.1/8000\'"\n'
      '"health-matter-server" = "bash -c \'exec 3<>/dev/tcp/127.0.0.1/5580\'"\n'
      '# Project doctor: mise/direnv boundary check (scripts/env-boundary-check.sh)\n'
      '"doctor-project" = "./scripts/env-boundary-check.sh /home/toxic/sovereign"\n')

print("ALL EDITS APPLIED")
