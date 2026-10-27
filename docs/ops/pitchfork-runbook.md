# pitchfork ops runbook — supervisor, state.toml, fleet recovery

Adversarial lessons from 2026-10-19 (full-fleet repair day). Read this before
touching the daemon fleet.

## 1. The supervisor is SYSTEMD-MANAGED — never `pitchfork supervisor start`

```ini
# ~/.config/systemd/user/pitchfork.service
ExecStart=/home/toxic/.../pitchfork supervisor run --boot
Restart=on-failure
```

- The canonical supervisor is `systemctl --user start pitchfork.service`
  (**with `--boot`** — that flag is what respawns every `boot_start`/`auto`
  daemon).
- **NEVER** `pitchfork supervisor start`/`stop` manually: it spawns a SECOND,
  non-boot supervisor that orphans the fleet (observed: 67+ daemons went
  "stopped" the instant a manual supervisor replaced the systemd one).
- Recovery: `pkill -f "pitchfork supervisor run"; systemctl --user start
  pitchfork.service` — the systemd unit takes over and --boot respawns
  everything (verified: 29+ live children under one CGroup on 2026-10-19).

## 2. State file — `~/.local/state/pitchfork/state.toml` is a SHADOW config

This file is the supervisor's persisted daemon registry and it **outlives**
toml edits and supervisor restarts:

- Editing `pitchfork.d/*.toml` while the supervisor runs does NOT update a
  running daemon's captured `cmd`/`run` — the old command (old ports, old
  paths, capital-E daemon ids like `Estate-exporter`) keeps executing.
- Symptom: "port X is already in use by process 'unknown' (PID: 0)" after
  moving a daemon to a new port — the state file still says the old port.
- Cache poisoning example (2026-10-19): 86 stale daemon blocks (dead ids,
  retired `var/reconciliation/flicker` paths, old ports) were purged.

**Correct edit procedure (no supervisor race):**
```
pitchfork supervisor stop        # via systemctl? NO — see §1: use systemctl --user stop pitchfork.service
systemctl --user stop pitchfork.service
python3 - <<'EOF'
import re, tomllib
p = "/home/toxic/.local/state/pitchfork/state.toml"
src = open(p).read()
# remove one daemon block + its nested subtables
for name in ["estate/some-daemon"]:
    m = re.search(rf'(\[daemons\."{re.escape(name)}"\].*?)(?=\n\[daemons\.|\Z)', src, re.S)
    if m: src = src.replace(m.group(0), "")
    src = re.sub(rf'\[daemons\."{re.escape(name)}"\.[a-z_]+\](.*?)(?=\n\[|\Z)', "", src, flags=re.S)
open(p, "w").write(src)
tomllib.load(open(p, "rb"))   # assert valid
EOF
systemctl --user start pitchfork.service   # --boot re-registers from tomls
```

If the state file is beyond salvage (corrupt, orphaned subtables):
`cat > state.toml <<EOF\n[meta]\nversion = 1\nEOF` — every daemon re-registers
fresh from pitchfork.toml + pitchfork.d/*.toml on next boot. Verified safe
2026-10-19.

## 3. Port-collision class (kitty-mcp vs node_exporter, 2026-10-19)

Two pitchfork daemons claimed :25211: `node_exporter` (SSOT
`NODE_EXPORTER_PORT=25211`) and `kitty-mcp` (`KITTY_MCP_SOCKET=tcp:...25211`).
Which one binds is launch-order luck; when node_exporter won, kitty's
`--listen-on tcp:127.0.0.1:25211` became invalid and **any process that
observed kitty's env** (e.g. `kappa -s <session>` resuming) printed:

```
Errors parsing configuration
In final effective configuration:
Invalid listen_on=tcp:127.0.0.1:25211, ignoring
```

Fix (applied): node_exporter moved to the free `:25231` (SSOT + both toml
declarations + state). **Lesson:** SSOT ports must be unique across daemons —
audit with `grep -rn "port = " pitchfork.d/*.toml | awk -F= '{print $2}' |
sort | uniq -d`.

## 4. `pitchfork start` CLI quirks

- `pitchfork start <name>` WAITS for readiness (can be 60-300s for model
  loads); the estate 2s shim will murder it. Use `--delay 1` to fire-and-
  return, then verify with `pitchfork status`.
- `--force` restarts an already-running daemon.
- `pitchfork disable` marks daemons `available  disabled` — corpse-mark
  configs whose targets are gone (kimi-code, kimi-audit-dash, bedrock-ui,
  boundless, refusal-watchdog, sorry-watchdog, forge, forge-agent) instead of
  deleting them (additive-only doctrine).

## 5. Fleet verify after any change

```bash
systemctl --user status pitchfork.service --no-pager | grep -c "log-sink"  # expected ~90+ children
pitchfork list | awk '{print $2}' | sort | uniq -c   # expect: mostly running, 0 unexpected errored
for p in 25100 25121 25127 25148 25155 25193; do curl -s -o /dev/null -w "$p:%{http_code} " http://127.0.0.1:$p/health; done; echo
```
## 6. kitty is NOT a daemon (2026-10-19)

`estate/kitty-mcp` was a contract instance giving the thresher kitty MCP
server a stable `KITTY_MCP_SOCKET=tcp:127.0.0.1:25211`. Problem: kitty is a
**user terminal**, not a service — every supervisor cycle respawned it and it
popped terminal windows on the desktop. Decommissioned 2026-10-19:
`pitchfork disable estate/kitty-mcp`; the socket binding is only needed while
an MCP client actively drives kitty, and the kitty-mcp-server bun instances
self-heal.
