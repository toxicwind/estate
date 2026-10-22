# kite-cli cell-repair deadlock — fixed? no; root cause proven (2026-10-22)

## Goal attempted
Use kite-cli obtuse/experimental paths to fix the cell-side sshd/kite-connector
(muse-1) so the tunnel end-to-end works.

## Obtuse approaches raced (all via /tmp/cdp_getcookie.mjs + kite-cli raw)
- CDP hijack :9223 -> Network.getAllCookies on the browser-keeper Chrome.
  MECHANISM WORKS, but the live Chrome holds only Google accounts domains, NO muse.ai.
- kite-cli cell {list,read,stat,raw,fs.*} -> all `401 api/session (cookies expired? re-export)`.
- kite-cli raw vm.health / subagents.status / config.get / feed.status -> SAME 401 (gateway enforces
  auth for every method, incl health).
- kite-cli auth export -> needs `agent-browser` (not installed) + a muse.ai login in Chrome.
- ~/.config/kite-cli/cookies.txt = stale Facebook `datr`/`ps_n` session, not Muse.
- secretsmith + cookie-vault: no kite/muse entry found.

## Root cause (a deadlock by construction)
kite-cli's cell-fix channel requires a valid **muse.ai session cookie on THIS host**.
That cookie exists only in the CELL's own logged-in browser (or an exported one we've
never had). We cannot reach the cell's ssh/Muse side (it rejects us) -> we cannot obtain
the cookie that would let kite-cli drive the cell to fix sshd -> which is the only thing
that would let us reach it. Circular.

## Unlock actions (non-hacky, forward-only)
1. Shortest: on SOME host with a working muse.ai login (e.g. the cell, before ssh dies,
   or the user's desktop Chrome), `kite-cli auth export` -> write ~/.config/kite-cli/cookies.txt.
   Then kite-cli raw vm.health + cell write can drive the cell-side sshd restart.
2. Estate-side already done: keepalive-tailscale.ts (stops relay-flap cause) + audit docs.
3. Underlying hard fact: cell sshd (:22) is simply not running; tailscale RSTs every dial.
   That is a cell-admin action (systemctl start sshd + kite connector) OR a valid kite
   session to drive it remotely.
