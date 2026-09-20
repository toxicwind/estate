#!/usr/bin/env python3
"""port-audit.py — diff the port SSOT (config/ports.env) against live listeners.

Finds the failure modes where services that should be well-behaved cause
conflicts because port assignment is not dynamic:

  1. SSOT DOUBLE-BOOKED — two unrelated names assigned the same port in
     config/ports.env (intentional aliases in ALIAS_GROUPS are exempt).
  2. LIVE BUT UNREGISTERED — a listener inside the sovereign ranges
     (25xxx, 83xx) that the SSOT knows nothing about.
  3. SQUATTERS — an SSOT port held by a process that is not the registered
     owner. Proven live 2026-09-20 via strace: kimi-code did a blind
     port-walk (tried requested port, then port+1, +2, ...) with no knowledge
     of the SSOT, so a duplicate instance walked onto ANTIGRAVITY_GATEWAY_PORT
     (25128) and probed shep's 25127 on the way. Kimi launch paths are now
     guarded with --no-port-walk (see scripts/kimi-no-port-walk-check.sh).
  4. EXPECTED BUT DARK — SSOT ports with nothing listening (informational;
     many daemons are optional).

Holder attribution reads /proc/<pid>/cmdline so generic runtimes
(python3, bun, node) are identified by the script they actually run, not
just the interpreter name.

Exit 1 when real double-books or squatters are found, else 0.
Run on demand or from an event-driven watcher — never on a timer.

Usage: bin/port-audit.py [--ssot PATH] [--json]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SSOT = REPO_ROOT / "config" / "ports.env"

# Intentional multi-name ports: same service, historic/renamed vars.
# {port: ({var names}, reason)}
ALIAS_GROUPS: dict[int, tuple[set[str], str]] = {
    25100: (
        {"LLAMA_SWAP_PORT", "HERD_PORT"},
        "herd.sh launches the llama-swap binary; HERD_PORT is the live name",
    ),
    25127: (
        {"MCPPROXY_GO_PORT", "SHEP_PORT"},
        "shep is the live mesh gateway on the historic mcpproxy-go port",
    ),
    25133: (
        {"QDRANT_PORT", "QDRANT_HTTP_PORT"},
        "one qdrant, two historic names",
    ),
    25107: (
        {"NULL_G_PROXY_PORT", "NULL_G_PORT"},
        "NULL_G_PORT is the deprecated alias",
    ),
    25201: (
        {"RUST_WEB_PORT", "RUST_WEB_BACKEND_PORT"},
        "rust-web daemon (sovereign_web binary); two historic names",
    ),
}

# port -> cmdline fragments identifying a legitimate holder.
# Checked against the full /proc/<pid>/cmdline, so interpreter-only
# process names (python3, bun, node) resolve to the real service.
KNOWN_HOLDERS: dict[int, set[str]] = {
    25199: {"valkey-server"},          # valkey is the redis replacement
    25114: {"sovereign-github-search"},  # next-server serving the ghas frontend
    25152: {"qwen3.5-9b"},            # toolcall-llm llama-server model
    25122: {"llama-server"},          # beellama backend
    25108: {"sovereign_web"},         # multi-port binary: watchdog + rust web
    25201: {"sovereign_web"},
    25127: {"shep"},                  # live mesh gateway
    25146: {"whatsapp-mcp"},          # whatsapp-mcp owns 25146 (ZEDRA_HOST_PORT retired)
    25198: {"awrawr_mcp"},            # MCP bridge
    25151: {"oracle"},                # oracle-core daemon
    25202: {"gemini-mcp"},            # gemini-mcp (moved off 8378, 2026-09-20)
    25100: {"llama-swap", "herd.sh"}, # herd launcher runs the llama-swap binary
    25126: {"kimi-code"},             # guarded with --no-port-walk
    25135: {"squawk"},                # squawk feed — verify only
    25147: {"squawk"},                # squawk ws — verify only
    25120: {"sovereign-chat", "chat.ts", "gateway.ts"},  # mcp gateway (live: chat.ts)
    8379: {"awrawr_ws_exec"},         # bridge exec-ws backend — verify only
}

# Verify-only: report state, never suggest re-pointing or killing.
PROTECTED_PORTS = {25135, 25147, 8379}

# Infra ports outside the sovereign ranges; not our registry's business.
INFRA_IGNORE = {
    22, 53, 443, 631, 2222, 5037, 5355, 5432, 59818, 9090, 9749, 10200,
    20241, 42445, 43161, 57889, 58050, 58051, 60955,
}


def in_sovereign_range(port: int) -> bool:
    return 25000 <= port <= 25299 or 8300 <= port <= 8399


def in_dynamic_pool(port: int) -> bool:
    """llama-swap dynamic backend pool (herd.yaml startPort)."""
    return 25001 <= port <= 25099


def parse_ssot(path: Path) -> tuple[dict[int, list[str]], list[str]]:
    """Return ({port: [VAR, ...]}, warnings)."""
    by_port: dict[int, list[str]] = {}
    warnings: list[str] = []
    seen_vars: dict[str, int] = {}
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*[\"']?([^\"'#\s]+)", line)
        if not m:
            continue
        name, val = m.group(1), m.group(2)
        if not name.endswith("_PORT") and name not in ("NGINX_PORT", "DNSMASQ_PORT"):
            continue
        if name in seen_vars:
            warnings.append(
                f"{path}:{lineno}: {name} redefined "
                f"(first at line {seen_vars[name]})"
            )
        seen_vars[name] = lineno
        try:
            port = int(val)
        except ValueError:
            warnings.append(f"{path}:{lineno}: {name} has non-numeric value {val!r}")
            continue
        by_port.setdefault(port, []).append(name)
    return by_port, warnings


def proc_cmdline(pid: int) -> str:
    """Full command line for a pid, space-joined; empty on failure."""
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\0", b" ").decode("utf-8", "replace").strip()


def proc_cwd(pid: int) -> str:
    """Working directory of a pid; empty on failure."""
    try:
        return str(Path(f"/proc/{pid}/cwd").resolve())
    except OSError:
        return ""


def live_listeners() -> dict[int, list[dict]]:
    """Return {port: [{name, pid, cmdline}, ...]} for listening TCP sockets."""
    out = subprocess.run(
        ["ss", "-tlnp"], capture_output=True, text=True, check=False
    ).stdout
    listeners: dict[int, list[dict]] = {}
    for line in out.splitlines():
        m = re.search(r":(\d+)\s", line)
        if not m:
            continue
        port = int(m.group(1))
        for name, pid in re.findall(r'\(\("([^"]+)",pid=(\d+)', line):
            pid_i = int(pid)
            listeners.setdefault(port, []).append(
                {
                    "name": name,
                    "pid": pid_i,
                    "cmdline": proc_cmdline(pid_i),
                    "cwd": proc_cwd(pid_i),
                }
            )
    return listeners


def var_tokens(var: str) -> set[str]:
    return {t.lower() for t in re.split(r"[_\d]+", var) if t}


def proc_tokens(text: str) -> set[str]:
    return {t.lower() for t in re.split(r"[^a-z0-9]+", text) if t}


def token_match(holder: dict, var_names: list[str]) -> bool:
    """Heuristic fallback: do name/cmdline/cwd tokens look like the SSOT var?"""
    ht = proc_tokens(f"{holder['name']} {holder['cmdline']} {holder['cwd']}")
    for var in var_names:
        vt = var_tokens(var)
        if any(
            t in h or h in t
            for t in vt
            for h in ht
            if len(t) > 1 and len(h) > 1
        ):
            return True
    return False


def holder_ok(port: int, holders: list[dict], var_names: list[str]) -> bool:
    """True when a holder is a known fragment match or token heuristic hit."""
    fragments = KNOWN_HOLDERS.get(port, set())
    for h in holders:
        hay = f"{h['name']} {h['cmdline']} {h['cwd']}".lower()
        if fragments and any(f.lower() in hay for f in fragments):
            return True
        if token_match(h, var_names):
            return True
    return False


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--ssot", default=str(DEFAULT_SSOT))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    ssot, warnings = parse_ssot(Path(args.ssot))
    live = live_listeners()

    double_booked: dict[int, list[str]] = {}
    for port, names in ssot.items():
        if len(names) < 2:
            continue
        alias, _ = ALIAS_GROUPS.get(port, (set(), ""))
        if set(names) <= alias:
            continue  # intentional alias, not a conflict
        double_booked[port] = names

    unregistered: dict[int, list[dict]] = {}
    for port, holders in live.items():
        if not in_sovereign_range(port):
            continue
        if port in ssot or port in INFRA_IGNORE or in_dynamic_pool(port):
            continue
        unregistered[port] = holders

    squatters: list[dict] = []
    for port, names in sorted(ssot.items()):
        holders = live.get(port, [])
        if not holders:
            continue
        if port in PROTECTED_PORTS:
            continue  # verify-only; never flag
        if holder_ok(port, holders, names):
            continue
        squatters.append(
            {
                "port": port,
                "registered": names,
                "holders": [
                    f"{h['name']} (pid {h['pid']}): {h['cmdline'][:100]}"
                    for h in holders
                ],
            }
        )

    dark = sorted(p for p in ssot if p not in live)
    pool_live = sorted(p for p in live if in_dynamic_pool(p))

    report = {
        "double_booked": {str(p): n for p, n in sorted(double_booked.items())},
        "alias_groups": {
            str(p): {"vars": sorted(v), "reason": r}
            for p, (v, r) in sorted(ALIAS_GROUPS.items())
        },
        "unregistered_live_ports": {
            str(p): [f"{h['name']} (pid {h['pid']}): {h['cmdline'][:100]}"
                     for h in holders]
            for p, holders in sorted(unregistered.items())
        },
        "squatters": squatters,
        "protected_ports": {
            str(p): [f"{h['name']} (pid {h['pid']})"
                     for h in live.get(p, [])]
            for p in sorted(PROTECTED_PORTS)
        },
        "dynamic_pool_live": pool_live,
        "expected_but_dark_count": len(dark),
        "expected_but_dark": dark,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if double_booked:
            print("DOUBLE-BOOKED (same port, 2+ unrelated SSOT names):")
            for p, names in sorted(double_booked.items()):
                print(f"  :{p} -> {', '.join(names)}")
        if unregistered:
            print("LIVE BUT UNREGISTERED (in sovereign range, not in SSOT):")
            for p, holders in sorted(unregistered.items()):
                who = ", ".join(
                    f"{h['name']} (pid {h['pid']}): {h['cmdline'][:80]}"
                    for h in holders
                )
                print(f"  :{p} -> {who}")
        if squatters:
            print("SQUATTERS (SSOT port held by non-owner):")
            for s in squatters:
                print(f"  :{s['port']} registered={','.join(s['registered'])}")
                for h in s["holders"]:
                    print(f"      holder: {h}")
        if warnings:
            print("WARNINGS:")
            for w in warnings:
                print(f"  {w}")
        print(f"Expected-but-dark SSOT ports: {len(dark)} (informational)")
        if pool_live:
            print(f"Dynamic pool live: {pool_live} (informational)")
        if not double_booked and not squatters and not unregistered:
            print("OK: no conflicts.")

    return 1 if (double_booked or squatters) else 0


if __name__ == "__main__":
    sys.exit(main())
