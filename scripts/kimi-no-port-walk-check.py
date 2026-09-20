#!/usr/bin/env python3
"""SSOT launch-guard check: a guarded kimi-code launch against an occupied
port must exit non-zero and must NOT bind port+1 (no silent port-walk).

Event-driven: the dummy listener signals readiness via socket, the child is
reaped with waitpid (Popen.wait), and the port-walk probe is a single
connect attempt. The only timeout is a fail-fast ceiling, never a poll loop.

Usage: kimi-no-port-walk-check.py [binary] [port]
  binary defaults to the deployed daemon dist; port defaults to 25299.
Exits 0 when the guard holds, 1 when it does not.
"""
from __future__ import annotations

import socket
import subprocess
import sys

BIN = sys.argv[1] if len(sys.argv) > 1 else (
    "/home/toxic/projects/sovereign-projects/tau/vendors/kimi-code"
    "/apps/kimi-code/dist/main.mjs"
)
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 25299
NEXT = PORT + 1
FAIL_FAST_CEILING = 15  # seconds; a guarded launch must die well before this

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def port_listening(port: int) -> bool:
    """Single connect probe: True iff something accepts on 127.0.0.1:port."""
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main() -> int:
    # Occupy PORT with a dummy listener (bind = readiness, no sleep).
    dummy = socket.socket()
    dummy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dummy.bind(("127.0.0.1", PORT))
    dummy.listen(1)

    proc = subprocess.Popen(
        [BIN, "web", "--no-open", "--port", str(PORT), "--no-port-walk"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _, stderr = proc.communicate(timeout=FAIL_FAST_CEILING)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        check("guarded launch exits promptly", False,
              f"still alive after {FAIL_FAST_CEILING}s (guard regressed?)")
        return 1
    finally:
        dummy.close()

    err = stderr.decode("utf-8", "replace")
    check("guarded launch exits non-zero against occupied port",
          proc.returncode != 0, f"exit={proc.returncode}")
    check("refusal message on stderr",
          "refusing to bind" in err,
          err.strip().splitlines()[-1] if err.strip() else "empty stderr")
    check(f"no port-walk to :{NEXT}", not port_listening(NEXT))

    print("ALL CHECKS PASSED" if not failures else "GUARD BROKEN")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
