# kite "HEALTHY" vs actually-broken — relay-up, tunnel-down (proven 2026-10-22 14:39)

## The false-healthy mechanism (tailscaled log)
kite reported "HEALTHY again at 14:36." The wire truth:
```
14:36:54  derp-1 connected            <- tailscale relay link up (kite sees this = "HEALTHY")
14:37:04  wg handshake init
14:37:39  flow => 100.94.78.109:22 got RST by peer   <- sshd STILL down
14:39:10  magicsock: CLOSING derp-1 (idle), age 2m15s  <- THE reset trigger
14:39:13  derp-1 connected (again)
14:39:13  flow => 100.94.78.109:22 got RST by peer      <- tunnel still refused
```
kite's health probe sees the RELAY link (recovers in ~5min), not the END-TO-END ssh
tunnel. So "healthy" while cell sshd/kite connector is actually down = relay-only liveness.

## Two-layer root cause + fixes
Layer A (recurring flap, estate-side, FIXABLE NOW): Tailscale closes the idle derp-1
(nyc) relay after ~2m15s (`magicsock: closing connection ... age 2m15s`). Periodic
keepalive on the cell path prevents the idle-close -> no more ~5min down/up flapping.

Layer B (end-to-end dead, CELL-SIDE, BLOCKER): muse-1 sshd (`:22`) + kite connector are
not listening. Every dial RSTs (`got RST by peer`), tailscale ping times out, cells
Active:false Direct:null bytes 0/0. Keepalive cannot fix this; the cell listener must be
up for the tunnel to actually carry traffic. kite's "HEALTHY" is meaningless until the
cell's sshd answers.

## Action
1. Add a keepalive so tailscaled doesn't idle-close derp-1 (removes the ~5min flap).
2. Bring up sshd + kite connector on muse-1 (the real tunnel). Then verify
   `tailscale status` shows Direct/healthy + cell :22 OPEN (not RST).
3. Consider forcing Denver DERP (11ms) over nyc (51ms) once direct path is clear.
