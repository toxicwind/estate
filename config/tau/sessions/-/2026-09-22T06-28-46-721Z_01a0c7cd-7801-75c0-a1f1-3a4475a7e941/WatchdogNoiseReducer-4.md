{
  "dedup_mechanism": "ConditionRegistry uses a seen-set (dictionary) keyed by condition identifier. Each entry stores a signature (sig), first timestamp, last timestamp, and count (n). The note() method returns 'fire' for new conditions or signature changes (state CHANGED), 'suppress' for identical signatures. The sweep() method clears conditions not observed in the current run. There are NO hardcoded thresholds in the dedup logic itself.",
  "hardcoded_thresholds": {
    "STUCK_UNSEEN_S": 180,
    "STUCK_WEDGED_S": 1800,
    "TRIAGE_WINDOW_S": 900
  },
  "recommendations": [
    "Increase dedup window: add a configurable DEDUP_WINDOW_S (default 600s) to allow conditions to stabilize before escalating",
    "Reduce alert thresholds: lower STUCK_UNSEEN_S to 60s and STUCK_WEDGED_S to 300s for faster stall detection",
    "Add rate limiting: introduce MAX_ALERTS_PER_HOUR limit per condition type to prevent alert storms",
    "Add cooldown period: after an alert fires, suppress related alerts for a short cooldown (e.g., 30s)",
    "Add a dedup window: compare timestamps to only escalate if the signature changed more than DEDUP_WINDOW_S ago"
  ]
}