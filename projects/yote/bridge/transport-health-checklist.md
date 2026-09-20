# Transport-health checklist — gating the WS-push upgrade

**Rule:** WS push from `ws_daemon.py`'s existing single persistent connection
ships ONLY after WS health is re-proven on the live bridge. No new daemon,
ever, in this lane. Until then, observability is capped polling tail
(`bin/poll_log.py`).

## 1. Architecture surface (what the push upgrade would attach to)

### Cell side — `bin/ws_daemon.py` (~/workspace/skills/awrawr-mcp/bin/)
READ-ONLY reference. Do NOT modify; document only.

- **One persistent connection:** `Bridge` class holds a single
  `wss://github-mcp-host.tailc9ac71.ts.net/exec-ws` connection
  (reader/writer pair, guarded by one `asyncio.Lock`). There is no
  per-command connection: commands multiplex by `id` in `Bridge.pending`
  (id → asyncio.Queue).
- **Local protocol:** Unix socket `~/.cache/awrawr-ws-bridge.sock`,
  newline-delimited JSON. Client sends
  `{"cmd","workdir","argv"?, "timeout"?}`; daemon streams back
  `{"type":"chunk","stream":"stdout"|"stderr","data"}`,
  `{"type":"done","code","truncated"}`,
  `{"type":"error","message"}`.
- **Health machinery:** `pinger()` sends a WS ping every `PING_INTERVAL=25`s;
  `_reader_loop()` answers server pings; `maintain()` reconnects with
  backoff 1→30 s and re-fetches the auth surrogate on every (re)connect.
  Daemon log: `~/.cache/awrawr-ws-bridge.log`.
- **Fallback contract:** if the daemon socket is absent or reports
  `{"type":"error","message":"bridge not connected"}`, `exec.py` falls back
  to the legacy HTTPS MCP streamable-HTTP path (cached session id,
  fully buffered). Push must degrade the same way: log-stream
  subscriptions fall back to capped polling.

### awrawr-pc side — server `~/awrawr_ws_exec.py`
- Managed by pitchfork as `sovereign/awrawr-ws-exec`; funnel route
  `/exec-ws → 127.0.0.1:8379/exec-ws`. stdlib-only asyncio WS server.
  The push upgrade would need a server-side log-stream subscription frame
  (new frame type on the SAME connection) — that work is out of scope for
  this item; this checklist only gates it.

## 2. How to measure (exact commands)

All from the cell. Force transport per probe with `AWRAWR_TRANSPORT`.

**a) Daemon presence (precondition for any WS measurement):**
```bash
ls -l ~/.cache/awrawr-ws-bridge.sock        # socket exists
tail -5 ~/.cache/awrawr-ws-bridge.log        # recent "bridge connected"
```

**b) Head-to-head race (coarse):**
```bash
python3 ~/workspace/skills/awrawr-mcp/bin/race.py
```
3 iterations × (ws, https) over tiny / early-output / throughput /
realistic; reports median wall + median TTFB.

**c) Warm-probe timing series (the acceptance gate):**
```bash
for t in ws https; do
  for i in $(seq 1 20); do
    AWRAWR_TRANSPORT=$t python3 ~/workspace/skills/awrawr-mcp/bin/exec.py \
      --json --timeout 15 --argv true \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["duration_ms"])'
  done > /tmp/probe-$t.txt
done
python3 - <<'EOF'
import statistics
for t in ("ws","https"):
    xs=[float(l) for l in open(f"/tmp/probe-{t}.txt")]
    xs.sort()
    p50=statistics.median(xs)
    p95=xs[int(0.95*len(xs))-1]
    stalls=[x for x in xs if x>5000]
    print(f"{t}: n={len(xs)} p50={p50:.0f}ms p95={p95:.0f}ms "
          f"max={xs[-1]:.0f}ms stalls>5s={len(stalls)}")
EOF
```

**d) Stall watch (daemon log correlation):** any probe > 5 s counts as a
stall. After the series, confirm the daemon log shows no
"bridge disconnected, reconnecting" during the run — a reconnect mid-series
invalidates the sample.

## 3. Acceptance thresholds — "WS health re-proven"

ALL must hold, measured on the live bridge with the commands in §2:

1. Daemon socket present; log shows `bridge connected` with no reconnect
   in the last 10 minutes.
2. 20 consecutive warm WS probes (`--argv true`, timeout 15):
   - **p50 < 500 ms**
   - **p95 < 2 000 ms**
   - **zero stalls > 5 s** (a stall = one probe exceeding 5 s)
3. `race.py`: WS median wall ≤ HTTPS median wall on `tiny` and
   `realistic` (WS must not lose to the fallback it replaces).
4. Re-run the 20-probe series a second time 10 minutes later and confirm
   thresholds still hold (rules out a lucky window).

If ANY threshold fails: stay on capped polling, re-measure in 24 h, log the
numbers. Do not ship push on a degraded WS lane.

## 4. Push-upgrade attachment sketch (for the later item, not this one)

- Reuse the same `Bridge.pending` multiplex: add a server-side frame
  `{"type":"subscribe_log","job_id":...}` on `~/awrawr_ws_exec.py`;
  daemon forwards `{"type":"log_chunk","job_id",...}` frames.
- Local protocol gains `{"subscribe_log": "<worker-id>"}` on the Unix
  socket; the subscriber streams chunks until `{"type":"done"}`.
- Rate protection moves server-side (per-job byte budget), but the
  client-side caps in `poll_log.py` REMAIN as the fallback path — push
  degrades to capped polling whenever the daemon reports not-connected.
