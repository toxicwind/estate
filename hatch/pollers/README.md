# lane pollers

Per-lane heartbeat pollers (Pulse lane, 2026-10-02).
One cron per lane, minute cadence, staggered.
See ~/workspace/docs/lane-pollers.md for the design.

- lane_poller.py — state/logic half (no chat tools; pure stdlib).
  Nudge text is generated through the side-channel shim
  (/home/toxic/estate/hatch/sidechat_shim.py :: format_safe).
- lanes.json — lane -> side-chat id map (verified 2026-10-02).
- state/ — per-lane JSON state + append-only JSONL logs.
