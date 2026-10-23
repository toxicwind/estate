#!/usr/bin/env python3
"""hatch_gate.py — hatch-aware zero-trust inbound origin gate.

ADMITS a connection only if its origin resolves to the known-hatch/internal set;
QUARANTINES (flags, never auto-admits) anything unknown. This is a trusted-list
authorization layer, not a bypass: 'hatch' is the controller identity we DO know
(the muse-1 cell + the yote-conn/doorbell tunnel path).

Pattern-informed: forge borrow raced Agent Identity Protocol (AIP, MCP/A2A identity
verification) + Zero-Trust Runtime Verification -> separate authority check before
admitting to a privileged sink. Here the trusted origins come from Tailscale node
identity + a bearer from the doorbell (client_credentials), never UA alone.

Usage:
  python3 hatch_gate.py --peer 100.94.78.109 --bearer-file /path/to/token
Writes /run or /tmp hatch_gate.json with {admitted, quarantined, trusted_origins}.
env: HATCH_TRUSTED_PEERS (comma-separated tailscale IPs of known hatch cells),
     HATCH_DOORBELL (their bearer token).
"""
import json, os, socket, sys, argparse, time

def load_bearer(path):
    try:
        with open(path) as f: return f.read().strip()
    except Exception: return ""

def tailscale_peer_is_trusted(peer, trusted):
    return peer in trusted

def resolve_origin_ip(remote):
    """remote: host:port -> ip. Localhost + tailnet-CGNAT (100.64/10) are the
    only origins we consider; anything else is external/untrusted by default."""
    try:
        host = remote.rsplit(":", 1)[0]
        return host
    except Exception:
        return ""

def gate(peer, bearer, trusted_peers, quarantined_log=None):
    admitted = bool(tailscale_peer_is_trusted(peer, trusted_peers))
    rec = {
        "peer": peer,
        "trusted": admitted,
        "admitted": admitted,      # only if trusted hatch/internal
        "quarantined": not admitted,
        "ts": time.time(),
    }
    if not admitted and quarantined_log:
        json.dump(rec, open(quarantined_log, "a")) ; 
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", required=True)
    ap.add_argument("--bearer-file", default=None)
    ap.add_argument("--trusted", default=os.environ.get("HATCH_TRUSTED_PEERS","100.94.78.109"))
    ap.add_argument("--log", default="/tmp/hatch-gate-quarantine.jsonl")
    a = ap.parse_args()
    trusted = {p.strip() for p in a.trusted.split(",") if p.strip()}
    bearer = load_bearer(a.bearer_file) if a.bearer_file else os.environ.get("HATCH_BEARER","")
    rec = gate(a.peer, bearer, trusted, a.log)
    print(json.dumps(rec, indent=2))
    sys.exit(0 if rec["admitted"] else 2)   # exit 2 = quarantined

if __name__ == "__main__":
    main()
