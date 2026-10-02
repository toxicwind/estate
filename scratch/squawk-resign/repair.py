#!/usr/bin/env python3
"""Re-sign squawk channel messages with canonical squawk-root keys.

Usage: python3 squawk_resign2.py <channel> <file1> [<file2> ...]
Files are re-signed IN ORDER with the sender's own canonical key;
each non-first file's parents are re-linked to the previous file's
post-rewrite msg id. Author/content/timestamps preserved.
Derived <channel>/log.jsonl records are refreshed (msg_hmac + parents).
Run on awrawr-pc.
"""
import sys
import json

sys.path.insert(0, "/home/toxic/squawk")
from pathlib import Path

import fleet_identity
from fleet_dag import msg_id

ROOT = Path("/home/toxic/.shingle/squawk-root")
KD = ROOT / "keys"


def render(meta_order, meta, body):
    lines = ["---"]
    for k in meta_order:
        lines.append(k + ": " + meta[k])
    lines += ["---", ""]
    return "\n".join(lines) + body.rstrip() + "\n"


def resign(chan, fname, parents):
    path = chan / fname
    meta, body = fleet_identity._parse_file(Path(path))
    sender = meta["from"]
    order = list(meta.keys())
    canon = fleet_identity.canonical_message(
        seq=int(meta["seq"]),
        sender=sender,
        to=meta["to"],
        reply_to=(meta.get("reply_to") or None),
        channel=meta["channel"],
        ts=meta["ts"],
        status=meta["status"],
        title=meta["title"],
        body=body,
        lamport=int(meta["lamport"]),
        parents=parents,
    )
    sig = fleet_identity.sign(sender, canon, KD)
    meta["parents"] = "[" + ", ".join(parents) + "]"
    meta["hmac"] = sig
    Path(path).write_text(render(order, meta, body), encoding="utf-8")
    assert fleet_identity.verify(sender, canon, sig, KD), "self-verify failed"
    return sig


def main():
    chan_name, files = sys.argv[1], sys.argv[2:]
    chan = ROOT / chan_name
    prev_id = None
    sig_by_seq = {}
    for i, fname in enumerate(files):
        if i == 0:
            meta, _ = fleet_identity._parse_file(chan / fname)
            cur = meta.get("parents", "").strip()
            if cur not in ("[]", ""):
                parents = [p.strip() for p in cur.strip("[]").split(",") if p.strip()]
            else:
                parents = []
        else:
            parents = [prev_id]
        sig = resign(chan, fname, parents)
        seq = int(fname.split("-")[0])
        sig_by_seq[seq] = sig
        prev_id = msg_id(chan / fname)
        print("resigned %s hmac=%s id=%s" % (fname, sig[:16], prev_id[:16]))
    # refresh derived log.jsonl
    logp = chan / "log.jsonl"
    id_by_seq = {int(f.split("-")[0]): msg_id(chan / f) for f in files}
    first_seq = int(files[0].split("-")[0])
    recs = []
    for line in logp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        s = r.get("seq")
        if s in sig_by_seq:
            r["msg_hmac"] = sig_by_seq[s]
            if s != first_seq and (s - 1) in id_by_seq:
                r["parents"] = [id_by_seq[s - 1]]
        recs.append(r)
    logp.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in recs) + "\n",
        encoding="utf-8",
    )
    print(chan_name + "/log.jsonl updated")
    print("OK")


main()
