# KITE bridge losing connection — root cause (tailscaled + packet evidence)

## Symptom
"Bridge is down again — yote unreachable on all lanes, Remote end closed connection
without response." ~12.5h uptime between outages (now more frequent, single-digit min).

## Evidence (tailscaled journal + ss, 2026-10-22 14:3x)
- Our outbound tailnet dials to the cell's sshd RST:
  `flow TCP (100.72.199.93:40638 => 100.94.78.109:22) got RST by peer`
  → the CELL's sshd (`:22`) is NOT listening; it rejects us.
- Our KITE CONNECTOR `:18301` is NOT listening either (cell-originated inbound has no target).
- Cell WireGuard re-handshake cadence ~8-38min:
  `wg: Received handshake initiation` @ 12:52,13:26,14:04,14:12,14:30,14:37 → link flaps.
- Peer wire state: muse-1 `Active:false Direct:null Relay:nyc LastHandshake:zero bytes 0/0`.
- Path = relay-only through derp-1 (nyc, 51ms) though nearest DERP is Denver (11ms);
  no direct P2P. UDP:true IPv6:yes local, so direct is possible but not established.

## Root cause (two-sided)
1. CELL-side: sshd + kite listener on muse-1 are down → every tunnel attempt RST /
   closes-without-response. THE blocker.
2. ESTATE-side hardening opportunity: route cell via far nyc relay, no direct path;
   fast re-handshakes make the single relay hop the fragile join.

## Fixes
- Cell side (owner: cell admin; we cannot reach via refused ssh): start sshd `:22` +
  kite connector on muse-1. No agent-side workaround can complete the tunnel while
  the cell listener is down.
- Estate side (doable now): prefer closer DERP (Denver) / enable direct for muse-1;
  optionally a custom DERP map to avoid nyc. Confirm direct by watching
  `tailscale status` for `Direct:` non-null after cell sshd returns.
