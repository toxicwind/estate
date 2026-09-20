
## 2026-09-14 18:35 MDT — persistence-audit worker (HFT-latency program, depth-2)
Latency findings from the squawk-ws / pitchfork / funnel audit on awrawr-pc:
- pitchfork kill -9 -> healthy listener: **1.26s** (canary, :25998; old PID 2716197 -> new 2726649). Supervisor retry=true is fast; the dominant cost is process spawn, not detection.
- Manual (non-pitchfork) squawk-ws -> pitchfork-owned: `pitchfork start` took ~5s wall (ready_cmd poll). Supervision gap (manual process outside pitchfork) was the root cause of intermittent 502s on /squawk-ws — Funnel had a route but no listener.
- `pitchfork start` IPC timeout: 63s (CLI 2.25.0 vs supervisor 2.16.0 version skew). Daemon actually started; CLI timed out waiting. Version skew is a real operational latency/correctness hazard.
- Funnel routes (/mcp, /exec-ws, /squawk-ws) verified present 18:33 MDT. tailscaled restart test: BLOCKED — `systemctl restart tailscaled` needs interactive auth (user toxic lacks sudo for it); `sudo -n` hung. tailscaled uptime 2w3d (since 2026-08-28) — restart path untested.
