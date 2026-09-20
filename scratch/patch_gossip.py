#!/usr/bin/env python3
"""Coordinator patch 12: scan_only() in fleet_gossip.py + gossip command."""
from pathlib import Path

BASE = Path("/home/toxic/.shingle/chat")

# --- 1. scan_only in fleet_gossip.py ---
p = BASE / "fleet_gossip.py"
src = p.read_text(encoding="utf-8")

anchor = "# --- self-test ---"
assert src.count(anchor) == 1
scan_only = '''def scan_only(root: _RootType, agent: str) -> dict:
    """Scan-only variant of anti_entropy(): gap scan + fresh digest +
    divergence comparison, but NO backfill. For `gossip --no-repair`.

    Same report shape as anti_entropy(); "backfilled" is always empty.
    """
    _check_safe_name(agent, "agent")
    report = {
        "agent": agent,
        "channels": [],
        "digest": "",
        "gaps_found": {},
        "backfilled": {},
        "unrecoverable": {},
        "divergent": {},
        "errors": {},
    }
    chans = _channels(root)
    report["channels"] = chans
    for ch in chans:
        try:
            gaps = scan_gaps(root, ch)
            if gaps["missing"]:
                report["gaps_found"][ch] = [m["seq"] for m in gaps["missing"]]
                report["unrecoverable"][ch] = gaps["missing"]
        except (GossipError, OSError, fleet_log.FleetLogError) as exc:
            report["errors"][ch] = f"{type(exc).__name__}: {exc}"
    report["digest"] = str(write_digest(root, agent))
    ddir = Path(root) / DIGESTS_DIR
    try:
        others = sorted(
            p.stem for p in ddir.glob("*.json") if p.stem != agent
        )
    except OSError:
        others = []
    for other in others:
        try:
            div = compare_digests(root, agent, other)
        except GossipError as exc:
            report["errors"][f"digest:{other}"] = str(exc)
            continue
        for ch in div:
            report["divergent"].setdefault(ch, []).append(other)
    return report


'''
src = src.replace(anchor, scan_only + anchor, 1)
p.write_text(src, encoding="utf-8")
print("fleet_gossip.py: scan_only added")

# --- 2. gossip command in chat.py ---
p = BASE / "chat.py"
src = p.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

rep(
    "import fleet_ephemeral\nimport fleet_identity\n",
    "import fleet_ephemeral\nimport fleet_gossip\nimport fleet_identity\n",
)

rep(
    "def cmd_suggest_role(root: Path, a):\n",
    '''def cmd_gossip(root: Path, a):
    """Anti-entropy pass (Demers et al. 1987): scan for seq gaps, backfill
    recoverable ones from log.jsonl, publish a divergence digest.

    Backfilled files are byte-faithful reconstructions (original frontmatter
    + original hmac, plus a non-HMAC-covered recovered_from marker), so they
    pass verification on the read path. Gossip never allocates seqs.
    """
    if a.channel:
        gaps = fleet_gossip.scan_gaps(root, a.channel)
        bf = fleet_gossip.backfill(root, a.channel) if a.repair else None
        if a.json:
            print(json.dumps({"gaps": gaps, "backfill": bf}, indent=2))
        else:
            missing = [m["seq"] for m in gaps["missing"]]
            print(f"channel '{a.channel}': max_seq={gaps['max_seq']}, "
                  f"missing={missing or 'none'}")
            if bf:
                print(f"  backfilled={bf['recovered'] or 'none'}, "
                      f"unrecoverable={[m['seq'] for m in bf['unrecoverable']] or 'none'}")
                if bf["log_error"]:
                    print(f"  log_error={bf['log_error']}")
        return
    report = (fleet_gossip.anti_entropy(root, a.agent) if a.repair
              else fleet_gossip.scan_only(root, a.agent))
    if a.json:
        print(json.dumps(report, indent=2))
        return
    print(f"gossip pass for '{a.agent}': {len(report['channels'])} channel(s)")
    for ch, seqs in sorted(report["gaps_found"].items()):
        print(f"  {ch}: gaps at seq {seqs}")
    for ch, seqs in sorted(report["backfilled"].items()):
        print(f"  {ch}: backfilled seq {seqs}")
    for ch, items in sorted(report["unrecoverable"].items()):
        seqs = [m["seq"] if isinstance(m, dict) else m for m in items]
        print(f"  {ch}: UNRECOVERABLE seq {seqs}")
    for ch, others in sorted(report["divergent"].items()):
        print(f"  {ch}: divergent vs {others}")
    for k, e in sorted(report["errors"].items()):
        print(f"  error [{k}]: {e}")
    if report["unrecoverable"] or report["errors"]:
        raise SystemExit(3)


def cmd_suggest_role(root: Path, a):
''',
)

rep(
    '''    s = sub.add_parser(
        "suggest-role",
        help="ADVISORY ONLY: suggest a specialization from local claim traces (never enforced)",
    )
    s.add_argument("channel", help="channel to read traces from")
    s.add_argument("--as", dest="agent", required=True, help="agent asking for a suggestion")
    s.set_defaults(func=cmd_suggest_role)
''',
    '''    s = sub.add_parser(
        "suggest-role",
        help="ADVISORY ONLY: suggest a specialization from local claim traces (never enforced)",
    )
    s.add_argument("channel", help="channel to read traces from")
    s.add_argument("--as", dest="agent", required=True, help="agent asking for a suggestion")
    s.set_defaults(func=cmd_suggest_role)

    s = sub.add_parser(
        "gossip",
        help="anti-entropy pass: scan seq gaps, backfill from log, compare digests",
    )
    s.add_argument("--as", dest="agent", required=True, help="agent running the pass")
    s.add_argument("--channel", default=None, help="scope to one channel (default: all)")
    s.add_argument("--repair", dest="repair", action="store_true", default=True,
                   help="backfill recoverable gaps (default)")
    s.add_argument("--no-repair", dest="repair", action="store_false",
                   help="scan + digests only, no backfill")
    s.add_argument("--json", action="store_true", help="print the raw report as JSON")
    s.set_defaults(func=cmd_gossip)
''',
)

p.write_text(src, encoding="utf-8")
print("patch applied:", p)
