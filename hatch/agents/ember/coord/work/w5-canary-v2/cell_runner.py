#!/usr/bin/env python3
"""Cell-side runner for the canary pack (execute from the cell, not here).
For each probe: send via the normal chat path, record reply digest/len,
append a row to canary_results.jsonl. Compare treatment vs control refusal
rates with Fisher's exact test. QUARANTINE: record digests+lengths only.
"""
import json
print("cell runner stub: wire to the chat path and record digests only")
