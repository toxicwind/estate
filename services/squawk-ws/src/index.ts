#!/usr/bin/env bun
/**
 * squawk-ws: first-class websocket push feed for Squawk. Bun/TS port of
 * ranch/squawk-ws/squawk_ws_server.py (752 lines Python -> this file).
 *
 * Watches the live message sources and pushes new messages to subscribed
 * websocket clients in real time. Replaces all polling (vault pulls,
 * long-poll, digest crons) for the Chris-facing feed.
 *
 * Sources:
 *   - ${SQUAWK_CHAT_ROOT}/<channel>/*.md  (chat.py channel files)
 *   - zipfs-vault local zip manifest (unsealed relay envelopes)
 *
 * Protocol:
 *   - ws://host:25147/squawk-ws (behind Tailscale funnel; binds 127.0.0.1)
 *   - Auth: `Authorization: Bearer <token>` header on the Upgrade request,
 *     or `?token=<token>` query param (browsers cannot set headers on
 *     WebSocket()). Constant-time compared against SQUAWK_WS_TOKEN_FILE
 *     plus the feed token file (unified web credential). No valid
 *     credential -> 401.
 *   - After 101, client sends {"subscribe": ["fleet","leads"]} (or nothing =
 *     all channels). Optional "since": <gseq> (or {"since": {"fleet": N, ...}})
 *     replays everything newer than that cursor -- outbox first, then disk
 *     via the durable file_seq->gseq map for cursors older than outbox
 *     retention. Server replays backlog oldest-first, then streams live
 *     messages as JSON text frames:
 *       {"seq": N, "file_seq": M, "channel": "fleet", "sender": "shingle",
 *        "text": "...", "ts": "...", "sealed": false}
 *     `seq` is the server-global monotonic cursor (use for `since`).
 *     `file_seq` is the durable per-channel file sequence from seq_alloc
 *     (survives restarts, merges, and reseeds; the stable cross-writer id).
 *     Sealed messages broadcast sender + sealed:true FLAG ONLY -- never
 *     content or ciphertext.
 *   - Slow consumers: if a client's queue (256) fills, the server closes the
 *     connection with WS code 1013 (try again later) instead of silently
 *     dropping. Reconnect with "since" to resume without loss.
 *   - Plain HTTP GET /ping -> {"ok": true, ...} (health check, no auth).
 *     GET /health is an alias (pitchfork health checks).
 *
 * State: global monotonic seq + per-source cursors + file_seq->gseq map
 * persisted in SQUAWK_WS_STATE_DIR/state.json, so restarts never reset or
 * duplicate. The map is backfilled on first boot after upgrade (one-time
 * renumber of pre-map history); afterwards every file keeps a stable gseq.
 *
 * Bun notes vs the Python:
 *   - WebSocket framing/handshake is Bun-native (Bun.serve websocket);
 *     the Python did manual RFC 6455 over raw asyncio streams.
 *   - inotify-via-ctypes is replaced by node:fs watch (inotify on Linux),
 *     debounced 300ms to coalesce bursts (same as Python's rescan sleep).
 *   - Vault zip reads go through the `unzip -p` CLI (no zip dep).
 *   - Bun auto-answers WS pings; the server still sends a 30s keepalive
 *     ping to every subscriber (was a per-connection pinger task).
 *   - DELIBERATE DEVIATION: SQUAWK_WS_PORT is required (fail-fast) per the
 *     services/_template convention. The Python defaulted to 25147.
 */

import { watch } from "node:fs";
import * as fs from "node:fs";
import * as path from "node:path";
import { timingSafeEqual } from "node:crypto";

// ---------------------------------------------------------------- env

const SERVICE = "squawk-ws";

function requiredPort(): number {
  const raw = process.env.SQUAWK_WS_PORT;
  if (!raw) {
    console.error(
      `FATAL ${SERVICE}: SQUAWK_WS_PORT is not set (ports come from config/ports.env, never hardcoded)`
    );
    process.exit(1);
  }
  const port = Number(raw);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    console.error(`FATAL ${SERVICE}: SQUAWK_WS_PORT=${raw} is not a valid port`);
    process.exit(1);
  }
  return port;
}

const PORT = requiredPort();
const CHAT_ROOT = process.env.SQUAWK_CHAT_ROOT ?? "/home/toxic/.fleet-bus/squawk-root";
const CHANNELS: string[] = (process.env.SQUAWK_WS_CHANNELS ?? "fleet,leads")
  .split(",")
  .map((c) => c.trim())
  .filter(Boolean);
const VAULT_ZIP =
  process.env.SQUAWK_WS_VAULT ?? "/home/toxic/workspace/skills/zipfs-vault/store/vault.zip";
const TOKEN_FILE = process.env.SQUAWK_WS_TOKEN_FILE ?? "/home/toxic/.squawk-ws-token";
const FEED_TOKEN_FILE =
  process.env.SQUAWK_WS_FEED_TOKEN_FILE ?? "/home/toxic/.fleet-bus/squawk-relay/feed-token";
const STATE_DIR = process.env.SQUAWK_WS_STATE_DIR ?? "/home/toxic/.squawk-ws";
const STATE_FILE = path.join(STATE_DIR, "state.json");

const OUTBOX_KEEP = 200;
const REPLAY_MAX = 1000; // hard cap on a single since-replay, oldest-first
const SUB_QUEUE_MAX = 256; // slow-consumer threshold -> WS 1013 close
const SLOW_CLOSE_CODE = 1013;
const PING_EVERY_MS = 30_000;
const RESCAN_DEBOUNCE_MS = 300;
const SEND_BUFFERED_CAP = 4 * 1024 * 1024; // transport backpressure pause

const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/;
const MSG_FILE_RE = /^\d+-.*\.md$/;
const ALIAS_RE = /^(fleet|leads)\/(\d+)$/;

// directories under the chat root that are NOT message channels
const RESERVED_DIRS = new Set(["keys"]);

// ---------------------------------------------------------------- types

interface BroadcastMsg {
  seq: number;
  file_seq: number;
  channel: string;
  sender: string;
  ts: string;
  sealed: boolean;
  text?: string;
}

interface ParsedMsg {
  msg_seq: number;
  channel: string;
  sender: string;
  ts: string;
  sealed: boolean;
  text: string;
}

interface SubData {
  subscribed: boolean;
  want: Set<string>;
  queue: BroadcastMsg[];
  pumping: boolean;
  closed: boolean;
}

// ---------------------------------------------------------------- state

let gseq = 0;
let chan_last: Record<string, number> = {}; // channel -> last msg_seq seen
let vault_last = 0; // last vault alias seq seen
let gseq_map: Record<string, Record<string, number>> = {}; // channel -> {file_seq: gseq}
let outbox: Record<string, BroadcastMsg[]> = {}; // channel -> [msgs], oldest-first
const subscribers = new Set<SubData>();
const dynamicChannels = new Set<string>();
const watchedDirs = new Set<string>();
let rescanScheduled = false;

function allChannels(): string[] {
  return [...CHANNELS, ...[...dynamicChannels].sort()];
}

function mapGet(ch: string, fileSeq: number): number | undefined {
  return gseq_map[ch]?.[String(fileSeq)];
}

function mapPut(ch: string, fileSeq: number, g: number): void {
  (gseq_map[ch] ??= {})[String(fileSeq)] = g;
}

function loadState(): void {
  try {
    const s = JSON.parse(fs.readFileSync(STATE_FILE, "utf-8"));
    gseq = Number(s.gseq ?? 0) || 0;
    chan_last = { ...(s.chan ?? {}) };
    vault_last = Number(s.vault ?? 0) || 0;
    const raw = s.gseq_map ?? {};
    gseq_map = {};
    for (const [ch, m] of Object.entries(raw)) {
      if (m && typeof m === "object") {
        gseq_map[ch] = {};
        for (const [k, v] of Object.entries(m as Record<string, unknown>)) {
          gseq_map[ch][String(k)] = Number(v) || 0;
        }
      }
    }
  } catch {
    // no state yet -- start fresh
  }
}

function saveState(): void {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    const tmp = STATE_FILE + ".tmp";
    fs.writeFileSync(
      tmp,
      JSON.stringify({ gseq, chan: chan_last, vault: vault_last, gseq_map })
    );
    fs.renameSync(tmp, STATE_FILE); // atomic: readers never see a half-write
  } catch (e) {
    console.error(`state save failed: ${e}`);
  }
}

// ---------------------------------------------------------------- message parsing

function parseMsgFile(p: string): ParsedMsg | null {
  let text: string;
  try {
    text = fs.readFileSync(p, "utf-8");
  } catch {
    return null;
  }
  // tolerate lone \r
  const norm = text.replace(/\r\n/g, "\n");
  const m = FRONTMATTER_RE.exec(norm);
  if (!m) return null;
  const [, fm, body] = m;
  const meta: Record<string, string> = {};
  for (const line of fm.split("\n")) {
    const idx = line.indexOf(":");
    if (idx > 0) meta[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
  }
  let seq = 0;
  const rawSeq = meta.seq ?? "0";
  const parsed = Number.parseInt(rawSeq, 10);
  if (Number.isFinite(parsed)) seq = parsed;
  const sealed = (meta.status ?? "") === "sealed";
  return {
    msg_seq: seq,
    channel: meta.channel ?? path.basename(path.dirname(p)),
    sender: meta.from ?? "unknown",
    ts: meta.ts ?? "",
    sealed,
    text: sealed ? "" : body.trim(),
  };
}

function readTokenFile(p: string): string {
  try {
    return fs.readFileSync(p, "utf-8").trim();
  } catch {
    return "";
  }
}

/** All valid bearer tokens: the WS token file plus the feed token file. */
function loadTokens(): Set<string> {
  const toks = new Set<string>();
  for (const p of [TOKEN_FILE, FEED_TOKEN_FILE]) {
    const t = readTokenFile(p);
    if (t) toks.add(t);
  }
  return toks;
}

function tokenOk(presented: string, toks: Set<string>): boolean {
  if (!presented || toks.size === 0) return false;
  const pb = Buffer.from(presented);
  for (const t of toks) {
    const tb = Buffer.from(t);
    if (pb.length === tb.length && timingSafeEqual(pb, tb)) return true;
  }
  return false;
}

// ---------------------------------------------------------------- publish / fanout

function closeSlow(sub: SubData, peer: string): void {
  sub.closed = true;
  subscribers.delete(sub);
  try {
    (sub as unknown as { ws?: { close(code: number, reason: string): void } }).ws?.close(
      SLOW_CLOSE_CODE,
      "slow consumer"
    );
  } catch {
    // ignore
  }
  console.log(`slow consumer ${peer} closed (1013)`);
}

function pump(sub: SubData): void {
  if (sub.pumping || sub.closed) return;
  const ws = (sub as unknown as { ws: Bun.ServerWebSocket<SubData> }).ws;
  sub.pumping = true;
  try {
    while (sub.queue.length > 0) {
      if (ws.getBufferedAmount() > SEND_BUFFERED_CAP) break; // wait for drain
      const m = sub.queue[0];
      const n = ws.send(JSON.stringify(m));
      if (n <= 0) break; // closed or dropped; drain/close will settle it
      sub.queue.shift();
    }
  } finally {
    sub.pumping = false;
  }
}

function enqueue(sub: SubData, msg: BroadcastMsg, peer: string): void {
  if (sub.closed) return;
  if (sub.queue.length >= SUB_QUEUE_MAX) {
    // Slow consumer: close with 1013 so it can reconnect with `since`
    // and resume without loss.
    closeSlow(sub, peer);
    return;
  }
  sub.queue.push(msg);
  pump(sub);
}

function peerOf(sub: SubData): string {
  try {
    const ws = (sub as unknown as { ws: Bun.ServerWebSocket<SubData> }).ws;
    return ws.remoteAddress ?? "?";
  } catch {
    return "?";
  }
}

function fanout(msg: BroadcastMsg): void {
  for (const sub of [...subscribers]) {
    if (!sub.want.has(msg.channel)) continue;
    enqueue(sub, msg, peerOf(sub));
  }
}

/** Assign global seq, buffer, persist, broadcast. Returns the message. */
function publish(
  channel: string,
  sender: string,
  text: string,
  ts: string,
  sealed: boolean,
  fileSeq = 0
): BroadcastMsg {
  gseq += 1;
  if (fileSeq) mapPut(channel, fileSeq, gseq);
  const msg: BroadcastMsg = {
    seq: gseq,
    file_seq: fileSeq,
    channel,
    sender,
    ts: ts ?? "",
    sealed: Boolean(sealed),
  };
  if (!sealed) msg.text = text ?? "";
  const buf = (outbox[channel] ??= []);
  buf.push(msg);
  if (buf.length > OUTBOX_KEEP) buf.splice(0, buf.length - OUTBOX_KEEP);
  saveState();
  fanout(msg);
  console.log(
    `publish seq=${gseq} file_seq=${fileSeq} ch=${channel} from=${sender} sealed=${sealed}`
  );
  return msg;
}

// ---------------------------------------------------------------- source scanning

let scanLock = false;

function discoverChannels(): void {
  let names: string[];
  try {
    names = fs
      .readdirSync(CHAT_ROOT, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name);
  } catch {
    return;
  }
  for (const name of names) {
    if (
      name.startsWith(".") ||
      CHANNELS.includes(name) ||
      dynamicChannels.has(name) ||
      RESERVED_DIRS.has(name)
    )
      continue;
    dynamicChannels.add(name);
    const d = path.join(CHAT_ROOT, name);
    if (!watchedDirs.has(d)) {
      try {
        installWatch(d);
        watchedDirs.add(d);
        console.log(`discovered + watching channel ${d}`);
      } catch (e) {
        console.log(`watch failed for ${d}: ${e}`);
      }
    }
  }
}

function channelFiles(ch: string): string[] {
  const d = path.join(CHAT_ROOT, ch);
  let entries: string[];
  try {
    entries = fs.readdirSync(d);
  } catch {
    return [];
  }
  return entries
    .filter((n) => MSG_FILE_RE.test(n))
    .sort()
    .map((n) => path.join(d, n));
}

function scanChannels(initial = false): void {
  if (scanLock) return;
  scanLock = true;
  try {
    discoverChannels();
    for (const ch of allChannels()) {
      const last = chan_last[ch] ?? 0;
      let newest = last;
      const files = channelFiles(ch);
      if (initial) {
        // Seed outbox with REAL gseqs. Files already in the durable
        // map keep their recorded gseq (stable across restarts);
        // pre-map history gets fresh gseqs once, then persists.
        for (const p of files) {
          const parsed = parseMsgFile(p);
          if (!parsed) continue;
          const fseq = parsed.msg_seq;
          let g = mapGet(ch, fseq);
          if (g === undefined) {
            gseq += 1;
            g = gseq;
            mapPut(ch, fseq, g);
          }
          const m: BroadcastMsg = {
            seq: g,
            file_seq: fseq,
            channel: parsed.channel,
            sender: parsed.sender,
            ts: parsed.ts,
            sealed: parsed.sealed,
          };
          if (!parsed.sealed) m.text = parsed.text;
          const buf = (outbox[ch] ??= []);
          buf.push(m);
          newest = Math.max(newest, fseq);
        }
        const buf = outbox[ch];
        if (buf && buf.length > OUTBOX_KEEP) buf.splice(0, buf.length - OUTBOX_KEEP);
        if (newest !== last) chan_last[ch] = newest;
        continue;
      }
      for (const p of files) {
        const parsed = parseMsgFile(p);
        if (!parsed || parsed.msg_seq <= last) continue;
        newest = Math.max(newest, parsed.msg_seq);
        // Advance the in-memory cursor BEFORE publishing so a
        // concurrent or repeated scan of the same directory sees
        // the updated floor and skips the file. publish() persists
        // state, so chan_last is durable as soon as this line runs.
        chan_last[ch] = newest;
        publish(
          parsed.channel,
          parsed.sender,
          parsed.text,
          parsed.ts,
          parsed.sealed,
          parsed.msg_seq
        );
      }
      if (newest !== last) chan_last[ch] = newest;
    }
    if (initial) saveState();
  } finally {
    scanLock = false;
  }
}

function readZipEntry(zipPath: string, entry: string): Buffer | null {
  try {
    const proc = Bun.spawnSync(["unzip", "-p", zipPath, entry]);
    if (proc.exitCode !== 0) return null;
    return Buffer.from(proc.stdout);
  } catch {
    return null;
  }
}

function scanVault(initial = false): void {
  if (scanLock) return;
  scanLock = true;
  try {
    if (!fs.existsSync(VAULT_ZIP)) return;
    const manifestRaw = readZipEntry(VAULT_ZIP, "manifest.json");
    if (!manifestRaw) return;
    let manifest: Record<string, unknown>;
    try {
      manifest = JSON.parse(manifestRaw.toString("utf-8"));
    } catch {
      return;
    }
    const items: Array<{ num: number; ch: string; env: Record<string, unknown> }> = [];
    for (const [alias, blob] of Object.entries(manifest)) {
      const m = ALIAS_RE.exec(alias);
      if (!m) continue;
      const ch = m[1];
      const num = Number.parseInt(m[2], 10);
      if (!Number.isFinite(num) || num <= vault_last) continue;
      const blobName =
        typeof blob === "object" && blob !== null
          ? String((blob as Record<string, unknown>).blob ?? "")
          : String(blob ?? "");
      if (!blobName) continue;
      const envRaw = readZipEntry(VAULT_ZIP, "blobs/" + blobName);
      if (!envRaw) continue;
      try {
        const env = JSON.parse(envRaw.toString("utf-8")) as Record<string, unknown>;
        items.push({ num, ch, env });
      } catch {
        continue;
      }
    }
    if (initial) {
      if (items.length > 0) vault_last = Math.max(...items.map((i) => i.num));
      return;
    }
    items.sort((a, b) => a.num - b.num);
    for (const { num, ch, env } of items) {
      const sealed = Boolean(env.sealed ?? false);
      publish(
        ch,
        String(env.sender ?? "?"),
        String(env.text ?? ""),
        String(env.ts ?? ""),
        sealed
      );
      vault_last = Math.max(vault_last, num);
    }
  } finally {
    scanLock = false;
  }
}

function doRescan(): void {
  scanChannels();
  scanVault();
}

function scheduleRescan(): void {
  if (rescanScheduled) return;
  rescanScheduled = true;
  setTimeout(() => {
    try {
      doRescan();
    } finally {
      // Clear only after the scan completes, so events arriving during
      // the wait do not schedule concurrent rescans.
      rescanScheduled = false;
    }
  }, RESCAN_DEBOUNCE_MS);
}

function installWatch(dir: string): void {
  // node:fs watch uses inotify on Linux. 'rename' covers create/move-to;
  // 'change' covers close-write. Debounced rescan coalesces bursts.
  const watcher = watch(dir, (_event, _filename) => {
    scheduleRescan();
  });
  watcher.on("error", (e) => {
    console.log(`watch error for ${dir}: ${e}`);
  });
}

// ---------------------------------------------------------------- since-replay

function cursorFor(ch: string, since: unknown): number {
  if (since !== null && typeof since === "object") {
    const v = (since as Record<string, unknown>)[ch];
    const n = Number(v ?? 0);
    return Number.isFinite(n) ? Math.trunc(n) : 0;
  }
  const n = Number(since ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Messages with gseq > `since`, oldest-first, capped at REPLAY_MAX.
 * `since` may be a single gseq (applies to all channels) or a dict
 * {channel: gseq}. Outbox covers recent history; for cursors older than
 * outbox retention we fall back to a disk scan via the durable
 * file_seq->gseq map.
 */
function replaySince(want: Set<string>, since: unknown): BroadcastMsg[] {
  const out: BroadcastMsg[] = [];
  for (const ch of [...want].sort()) {
    const cur = cursorFor(ch, since);
    const buf = outbox[ch] ?? [];
    // Fast path: cursor inside outbox coverage.
    if (buf.length > 0 && cur >= (buf[0]?.seq ?? 0)) {
      out.push(...buf.filter((m) => m.seq > cur));
      continue;
    }
    // Slow path: cursor older than outbox (or outbox empty after a
    // restart) -- scan disk via the durable file_seq->gseq map.
    const seen = new Set<number>();
    let diskOk = true;
    let files: string[];
    try {
      files = channelFiles(ch);
    } catch {
      diskOk = false;
      files = [];
    }
    if (diskOk) {
      for (const p of files) {
        const parsed = parseMsgFile(p);
        if (!parsed) continue;
        const g = mapGet(ch, parsed.msg_seq);
        if (g === undefined || g <= cur) continue;
        const m: BroadcastMsg = {
          seq: g,
          file_seq: parsed.msg_seq,
          channel: parsed.channel,
          sender: parsed.sender,
          ts: parsed.ts,
          sealed: parsed.sealed,
        };
        if (!parsed.sealed) m.text = parsed.text;
        out.push(m);
        seen.add(parsed.msg_seq);
      }
    }
    // live tail not yet on disk (skip file_seqs already covered above)
    out.push(
      ...buf.filter((m) => m.seq > cur && !seen.has(m.file_seq))
    );
  }
  out.sort((a, b) => a.seq - b.seq);
  return out.slice(-REPLAY_MAX);
}

// ---------------------------------------------------------------- HTTP + WS server

function healthPayload(): Record<string, unknown> {
  return {
    ok: true,
    service: SERVICE,
    seq: gseq,
    clients: subscribers.size,
    channels: allChannels(),
    high_water: Object.fromEntries(allChannels().map((ch) => [ch, chan_last[ch] ?? 0])),
  };
}

function isPingPath(pathname: string): boolean {
  return pathname.replace(/\/+$/, "").endsWith("/ping");
}

const server = Bun.serve<SubData>({
  port: PORT,
  hostname: "127.0.0.1",
  fetch(req, server) {
    const url = new URL(req.url);
    const pathname = url.pathname;

    if (req.method === "GET" && (isPingPath(pathname) || pathname === "/health")) {
      return Response.json(healthPayload());
    }

    const upgrade = req.headers.get("upgrade")?.toLowerCase() ?? "";
    const wsKey = req.headers.get("sec-websocket-key");
    if (upgrade !== "websocket" || !wsKey) {
      return new Response("not found", { status: 404 });
    }

    // auth: Authorization: Bearer <t> header, or ?token=<t> query
    // (browsers cannot set headers on WebSocket()).
    const toks = loadTokens();
    const auth = req.headers.get("authorization") ?? "";
    const qtoken = url.searchParams.get("token") ?? "";
    let ok = false;
    if (toks.size > 0) {
      if (auth.startsWith("Bearer ")) {
        ok = tokenOk(auth.slice(7).trim(), toks);
      }
      if (!ok && qtoken) ok = tokenOk(qtoken, toks);
    }
    if (!ok) {
      console.log("auth rejected");
      return new Response("unauthorized", { status: 401 });
    }

    const sub: SubData = {
      subscribed: false,
      want: new Set(),
      queue: [],
      pumping: false,
      closed: false,
    };
    // stash the ws handle on the data object for pump()/closeSlow()
    const upgraded = server.upgrade(req, { data: sub });
    if (!upgraded) return new Response("upgrade failed", { status: 500 });
    return undefined as unknown as Response;
  },
  websocket: {
    open(ws) {
      const sub = ws.data as SubData;
      (sub as unknown as { ws: Bun.ServerWebSocket<SubData> }).ws = ws;
      // wait for the first text frame = subscribe message
    },
    message(ws, message) {
      const sub = ws.data as SubData;
      if (sub.closed || sub.subscribed) return; // ignore post-subscribe frames
      let parsed: Record<string, unknown> = {};
      try {
        const text = typeof message === "string" ? message : message.toString("utf-8");
        const v: unknown = JSON.parse(text);
        if (v && typeof v === "object") parsed = v as Record<string, unknown>;
      } catch {
        // malformed subscribe -> fall through with defaults
      }
      const chans = parsed.subscribe ?? "all";
      let want: Set<string>;
      if (chans === "all") {
        want = new Set(allChannels());
      } else if (Array.isArray(chans)) {
        const known = new Set(allChannels());
        want = new Set(chans.filter((c): c is string => typeof c === "string" && known.has(c)));
      } else {
        want = new Set(allChannels());
      }
      sub.want = want;
      sub.subscribed = true;
      subscribers.add(sub);
      const since = parsed.since ?? 0;
      console.log(
        `subscriber channels=${[...want].sort().join(",")} since=${JSON.stringify(since)}`
      );
      // backfill: replay everything after `since`, oldest first
      for (const m of replaySince(want, since)) {
        enqueue(sub, m, ws.remoteAddress ?? "?");
        if (sub.closed) break;
      }
    },
    drain(ws) {
      const sub = ws.data as SubData;
      pump(sub);
    },
    close(ws) {
      const sub = ws.data as SubData;
      sub.closed = true;
      if (subscribers.delete(sub)) {
        console.log("subscriber gone");
      }
    },
  },
});

// keepalive: Bun auto-answers pings; we still send a 30s server ping
// (was a per-connection pinger task in the Python).
const pingTimer = setInterval(() => {
  for (const sub of [...subscribers]) {
    if (sub.closed) continue;
    try {
      (sub as unknown as { ws: Bun.ServerWebSocket<SubData> }).ws.ping();
    } catch {
      // close handler will clean up
    }
  }
}, PING_EVERY_MS);

// ---------------------------------------------------------------- main

loadState();
scanChannels(true); // initial: seed outbox + cursors, no broadcast
scanVault(true); // initial: advance vault cursor, no broadcast
console.log(`${SERVICE}: initial scan done, gseq=${gseq}`);

for (const ch of allChannels()) {
  const d = path.join(CHAT_ROOT, ch);
  try {
    if (fs.statSync(d).isDirectory()) {
      installWatch(d);
      watchedDirs.add(d);
      console.log(`watching ${d}`);
    }
  } catch (e) {
    console.log(`watch failed for ${d}: ${e}`);
  }
}
const vaultParent = path.dirname(VAULT_ZIP);
try {
  if (fs.statSync(vaultParent).isDirectory()) {
    installWatch(vaultParent);
    console.log(`watching ${vaultParent}`);
  }
} catch (e) {
  console.log(`watch failed for ${vaultParent}: ${e}`);
}

console.log(`${SERVICE} listening on 127.0.0.1:${PORT} (pid ${process.pid})`);

function shutdown(signal: string): void {
  console.log(`${SERVICE}: ${signal}, draining`);
  clearInterval(pingTimer);
  for (const sub of [...subscribers]) {
    try {
      (sub as unknown as { ws: Bun.ServerWebSocket<SubData> }).ws.close(1001, "shutdown");
    } catch {
      // ignore
    }
  }
  server.stop(true);
  process.exit(0);
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
