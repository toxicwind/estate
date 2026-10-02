"""Pilot: run the first K tasks of the batch through the real market."""
import sys

import auctioneer_driver as ad
import bidder_launcher as bl
import tasks as t

K = int(sys.argv[1]) if len(sys.argv) > 1 else 2
RUN_DIR = sys.argv[2] if len(sys.argv) > 2 else "/tmp/e2e-pilot2"
BATCH = sys.argv[3] if len(sys.argv) > 3 else "pilot2"

t.TASKS = t.TASKS[:K]
procs = bl.launch(RUN_DIR)
print("bidders up", flush=True)
try:
    ledger = ad.run_market(RUN_DIR, BATCH)
    print("PILOT DONE", flush=True)
finally:
    bl.stop(procs)
    print("stopped", flush=True)
