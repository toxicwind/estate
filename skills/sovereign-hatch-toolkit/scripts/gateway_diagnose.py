#!/usr/bin/env python3
"""No-credentials gateway transport diagnostic.

Probes how far the path to the Hatch gateway goes WITHOUT any auth token:
TCP -> egress-proxy CONNECT -> TLS (issuer) -> WebSocket upgrade.

Expected healthy result: the upgrade is rejected (401/403/...) because no
token is presented. That proves the MITM proxy path is intact and the gate
is auth -- NOT transport. Never prints or uses credentials.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hatch_core.gateway_rpc import diagnose_transport, load_config, redact_url, build_url


def main() -> int:
    cfg = load_config()
    vm_id = cfg.get("default_vm_id", "")
    print("gateway :", redact_url(build_url(cfg, vm_id)))
    print("proxy   :", (os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
                         or "(none - direct)"))
    report = diagnose_transport(cfg["gateway_url"], vm_id)
    print()
    print(f"{'stage':<18}{'ok':<6}detail")
    print("-" * 70)
    for name, ok, detail in report["stages"]:
        print(f"{name:<18}{str(ok):<6}{detail}")
    print()
    print("note: run with HATCH_AUTH_TOKEN set to attempt a real handshake")
    print("      (token never printed; credential handling is Chris-only).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
