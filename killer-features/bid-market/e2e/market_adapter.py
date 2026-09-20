"""Seam between the e2e harness and the REAL squawk bid-marketplace.

Wired to PROTOCOL.md v0 (msg_type frontmatter + JSON body, HMAC-signed
via signpost.py, channel `bid-market`). The auction mechanics live in
auctioneer_driver.py (test-harness auctioneer implementing the protocol's
bid window + deterministic tie-break); when t2-impl-auctioneer lands the
real auctioneer this module grows a --auctioneer real path.

WIRED = True: schema confirmed against the real bidder.py.
"""

import auctioneer_driver

CHANNEL = auctioneer_driver.CHANNEL
WIRED = True


def run_market(run_dir, batch_id):
    """Full market run through the real protocol. Returns the ledger."""
    return auctioneer_driver.run_market(run_dir, batch_id)
