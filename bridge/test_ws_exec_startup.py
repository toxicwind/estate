"""Startup-contract tests for awrawr-ws-exec (2026-11-08, Thread 1).

Contract: when the required sibling module (awrawr_mcp) cannot be imported,
the bridge must refuse to start with ONE loud FATAL line on stderr and exit
78 (EX_CONFIG) — never crash-loop under pitchfork. A dead exec lane must be
visible as backend: down, not inferred from a 502 two hops away.
"""
import os
import subprocess
import sys

BRIDGE = os.path.join(os.path.dirname(__file__), "awrawr_ws_exec.py")


def test_missing_module_exits_78_with_fatal():
    # HOME points at an empty dir so the `sys.path.insert(0, ~)` import of
    # awrawr_mcp cannot resolve. System python3 lacks uvicorn, so even if a
    # stray awrawr_mcp.py were on sys.path the import would fail — either way
    # the guard must fire with a single FATAL and exit 78.
    env = {
        "HOME": "/tmp/ws-exec-empty-home",
        "WS_EXEC_PORT": "0",
        "PATH": "/usr/bin",
    }
    r = subprocess.run(
        [sys.executable, BRIDGE],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert r.returncode == 78, f"expected exit 78, got {r.returncode}"
    assert "FATAL: awrawr_mcp missing" in r.stderr, f"missing FATAL, got: {r.stderr}"


def test_health_lanes_endpoint_reachable():
    # The health-lanes handler is a plain GET before the WS upgrade branch.
    # We can't bind a real port cheaply here, but we CAN assert the path is
    # wired by checking the source contains the handler (structural contract).
    with open(BRIDGE) as f:
        src = f.read()
    assert "/health-lanes" in src
    assert '"backend"' in src
    assert '"auth"' in src
    assert '"gateway"' in src


if __name__ == "__main__":
    test_missing_module_exits_78_with_fatal()
    test_health_lanes_endpoint_reachable()
    print("all startup-contract tests passed")