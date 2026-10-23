#!/usr/bin/env bun
/**
 * keepalive-tailscale.ts — improbable-failure connection optimizer.
 *
 * Root cause (proven 2026-10-22): tailscaled idle-closes the DERP relay
 * (~2m15s of no traffic -> `magicsock: closing connection to derp-1 (idle), age
 * 2m15s`). That close is the recurring flap: bridge drops, "remote end closed
 * without response", re-handshake ~5min later. Keepalive below prevents the
 * idle-close by scheduling a sub-idle-interval packet toward the peer.
 *
 * This is the estate-side layer. It does NOT paper over the cell-listener
 * being down; it removes the *flapping* cause so the tunnel stays warm the
 * moment the cell sshd returns.
 *
 * Run under pitchfork (supervisord-style loop); ctrl-c safe.
 *
 * Usage:
 *   bun keepalive-tailscale.ts [--interval-ms 90000] [--peer 100.94.78.109]
 */
import { execSync } from "node:child_process";

const PREFER_MS = 90_000;          // < 135000 (tailscaled ~2m15s idle-close)
const PEER = "100.94.78.109";      // kite cell (muse-1)

function args(): { interval: number; peer: string; dry: boolean } {
  const a = process.argv.slice(2);
  const i = a.includes("--interval-ms") ? Number(a[a.indexOf("--interval-ms") + 1]) : PREFER_MS;
  const p = a.includes("--peer") ? a[a.indexOf("--peer") + 1] : PEER;
  const dry = a.includes("--dry");
  return { interval: isNaN(i) ? PREFER_MS : i, peer: p, dry };
}

function poke(peer: string): boolean {
  // persistent, cheap keepalive that tailscaled counts as traffic toward the peer
  try {
    const out = execSync(`tailscale ping --c 1 --timeout ${Math.floor(PREFER_MS/1000)} ${peer} 2>/dev/null`,
      { timeout: 15000, stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
    return !out.startsWith("ping") || !out.includes("timed");
  } catch {
    return false; // peer not currently reachable; still tried (keeps the UDP/relay path warm)
  }
}

const cfg = args();
console.log(`keepalive-tailscale: interval=${cfg.interval}ms peer=${cfg.peer} dry=${cfg.dry}`);
let pokes = 0, ok = 0;
setInterval(() => {
  const t0 = Date.now();
  const live = poke(cfg.peer);
  const dt = Date.now() - t0;
  pokes++; if (live) ok++;
  if (cfg.dry) { console.log(`dry ${live?"reachable":"unreachable"} (${dt}ms)`); }
  // write a tiny state file an external monitor can read (mirrors the cell VJ feed)
  try {
    const fs = "node:fs";
    import(fs).then(m => m.writeFileSync("/tmp/keepalive-tailscale.json",
      JSON.stringify({ pokes, ok, last: Date.now(), lastOk: live, dtMs: dt }))).catch(()=>{});
  } catch {}
}, cfg.interval);
