#!/usr/bin/env python3
"""Ember: fix _pump_backlog self-post filter (2026-09-21).

The loop's ingest() ignores its own posts (SELF_FROMS), so a pump-posted
intake_request with frm=FROM is never ingested and no auction opens.
Fix: post the intake_request as frm="backlog-pump" (a non-self identity),
so the normal ingest path triages it and the resulting task_post (also
from backlog-pump) clears the self-post filter, opening the auction.
Trust is unchanged: task_post is still control-HMAC-signed by the oracle.
"""
import sys
from pathlib import Path

LOOP = Path("/home/toxic/sovereign/agents/oracle-market/bin/oracle_loop.py")

OLD = '''        try:
            name = self.market.post(
                "intake_request",
                "intake-%s" % self._safe_frm(title),
                {"text": text},
                note=("oracle-market: autonomous backlog pump -- no swarm "
                      "proposal arrived; launching next queued task."),
                frm=FROM)'''
NEW = '''        # NOTE: frm="backlog-pump", NOT FROM. ingest() ignores the
        # oracle's own posts (SELF_FROMS); a self-from intake_request would
        # never be triaged and no auction would open. backlog-pump is a
        # non-self requester identity, so the normal intake -> task_post
        # -> auction path runs. The task_post stays control-HMAC-signed.
        try:
            name = self.market.post(
                "intake_request",
                "intake-%s" % self._safe_frm(title),
                {"text": text},
                note=("oracle-market: autonomous backlog pump -- no swarm "
                      "proposal arrived; launching next queued task."),
                frm="backlog-pump")'''


def main():
    text = LOOP.read_text(encoding="utf-8")
    if 'frm="backlog-pump"' in text:
        print("fix already applied")
        return 0
    assert OLD in text, "anchor not found"
    text = text.replace(OLD, NEW, 1)
    LOOP.write_text(text, encoding="utf-8")
    print("fixed: pump now posts as backlog-pump")
    return 0


if __name__ == "__main__":
    sys.exit(main())
