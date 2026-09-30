#!/usr/bin/env bun
// fleet-mirror-flush — complete yote-journaled fleet messages. (Bun port of
// flush.sh; same semantics, same log lines.)
//
// Sweeps /home/toxic/hatch/fleet-outbox/pending/*.json — the write-ahead
// journal that fleet-post (hatch cell) writes concurrently with its delivery
// race. For each record:
//   - if its uuid is already present in the fleet channel -> delete the
//     record (already delivered; this also repairs a journalDelete that raced
//     a late-arriving journal write).
//   - else if the same (sender, message body) is already present in the
//     channel (posted via `squawk send`, which historically carried no uuid)
//     -> delete the record (already delivered; no double-post).
//   - else -> post the message by direct file write into the channel dir
//     (same frontmatter format as fleet-post path B, same uuid) and delete
//     the record.
//
// Why the content check exists: fleet-post's path A (`squawk send`) embedded
// the uuid NOWHERE — only path B's frontmatter carried it. A uuid-only
// already-delivered check therefore missed every path-A delivery and
// double-posted (observed 2026-09-30: 7 duplicates in one sweep). The
// (sender, body) check over files with mtime near the journal's own mtime
// closes that gap. (fleet-post now also stamps its uuid into path-A files,
// so the uuid check catches those too — belt and suspenders.)
// Both checks are idempotent: a crash between post and delete is repaired on
// the next run.
//
// SCOPE: this sweeps ONLY the yote mirror. The cell spool
// (~/workspace/fleet-outbox on the hatch cell — the bridge-DOWN last resort)
// is swept by the Hatch platform cron "fleet-outbox-flush". The two stores
// are disjoint by construction (a message is journaled to exactly one,
// depending on whether the journal write landed), so there is no double-fire.

import { readdirSync, readFileSync, writeFileSync, unlinkSync, statSync, mkdirSync, openSync, readSync, closeSync } from "node:fs";
import { join, basename } from "node:path";

const PENDING = process.env.PENDING ?? "/home/toxic/hatch/fleet-outbox/pending";
const LOG = process.env.LOG ?? "/home/toxic/hatch/fleet-outbox/flush.log";
const LOCK = process.env.LOCK ?? "/home/toxic/hatch/fleet-outbox/flush.lock";
const SQUAWK_ROOT = process.env.SQUAWK_ROOT ?? "/home/toxic/.fleet-bus/squawk-root";

const UUID_RE = /^[a-f0-9-]{8,40}$/;
const FNAME_RE = /^[a-f0-9-]{8,40}\.json$/;
const CHANNEL_RE = /^[a-z0-9_-]{1,40}$/;

function log(msg: string): void {
  const line = `${new Date().toISOString().replace(/\.\d+Z$/, "Z")} ${msg}\n`;
  writeFileSync(LOG, line, { flag: "a" });
}

// --- lock: atomic create-or-skip with PID staleness takeover ---
// (flock releases on process death; a bare existence check would wedge on
// crash, so a stale-PID lock is taken over.)
function takeLock(): boolean {
  try {
    const fd = openSync(LOCK, "wx", 0o644);
    writeFileSync(fd, String(process.pid));
    closeSync(fd);
    return true;
  } catch {
    try {
      const pid = parseInt(readFileSync(LOCK, "utf8").trim(), 10);
      if (!Number.isFinite(pid)) return false;
      try { process.kill(pid, 0); return false; } // holder alive -> skip
      catch { /* holder dead -> take over */ }
      writeFileSync(LOCK, String(process.pid));
      return true;
    } catch { return false; }
  }
}

function splitFrontmatter(text: string): { from: string; body: string } | null {
  const lines = text.split("\n");
  if (lines.length === 0 || lines[0].trim() !== "---") return null;
  const end = lines.indexOf("---", 1);
  if (end < 0) return null;
  let from = "";
  for (const ln of lines.slice(1, end)) {
    if (ln.startsWith("from:")) { from = ln.slice(5).trim(); break; }
  }
  return { from, body: lines.slice(end + 1).join("\n") };
}

function deliveredAlready(chanDir: string, uuid: string, sender: string, message: string, recMtimeMs: number): boolean {
  let names: string[];
  try { names = readdirSync(chanDir); } catch { return false; }
  const mdNames = names.filter(n => n.endsWith(".md"));
  const uuidNeedle = `uuid: ${uuid}`;
  const wantBody = message.trim();

  // Pass 1: uuid over the whole channel (cheap 2KB head reads). Catches
  // path-B posts, this flusher's own earlier completions, and path-A posts
  // whose files fleet-post stamped with the uuid.
  for (const name of mdNames) {
    const p = join(chanDir, name);
    let fd: number | null = null;
    try {
      fd = openSync(p, "r");
      const buf = Buffer.alloc(2048);
      const n = readSync(fd, buf, 0, 2048, 0);
      if (buf.subarray(0, n).toString("binary").includes(uuidNeedle)) return true;
    } catch { /* unreadable -> skip */ } finally { if (fd !== null) { try { closeSync(fd); } catch {} } }
  }

  // Pass 2: (sender, body) over files written near the journal record.
  // Catches path-A (`squawk send`) posts, which carry no uuid.
  for (const name of mdNames) {
    const p = join(chanDir, name);
    try {
      const st = statSync(p);
      if (Math.abs(st.mtimeMs - recMtimeMs) > 900_000) continue;
      if (st.size > 65536) continue;
      const raw = readFileSync(p);
      let text: string;
      try { text = raw.toString("utf8"); } catch { continue; }
      const split = splitFrontmatter(text);
      if (!split) continue;
      if (split.from === sender && split.body.trim() === wantBody) return true;
    } catch { /* skip */ }
  }
  return false;
}

function main(): void {
  let pendingNames: string[];
  try { pendingNames = readdirSync(PENDING); } catch { return; } // no dir -> nothing
  if (!takeLock()) return; // another run holds the lock; skip quietly
  const records = pendingNames.filter(n => n.endsWith(".json")).sort();
  if (records.length === 0) return;

  let nAlready = 0, nCompleted = 0, nBad = 0;
  for (const fname of records) {
    const recPath = join(PENDING, fname);
    const bad = (kind: string) => { nBad++; log(`bad record BAD ${kind}: ${recPath}`); };
    if (!FNAME_RE.test(fname)) { bad("filename"); continue; }
    const uuid = fname.slice(0, -5);

    let r: any;
    try { r = JSON.parse(readFileSync(recPath, "utf8")); }
    catch { bad("json"); continue; }
    const sender = String(r?.sender ?? "").trim() || "agent (ember's pack)";
    const channel = String(r?.channel ?? "").trim() || "fleet";
    const message = String(r?.message ?? "");
    const ts = String(r?.ts ?? "").trim();
    if (String(r?.uuid ?? "") !== uuid || !message || !CHANNEL_RE.test(channel)) { bad("content"); continue; }

    const chanDir = join(SQUAWK_ROOT, channel);
    try { mkdirSync(chanDir, { recursive: true }); } catch {}
    let recMtimeMs: number;
    try { recMtimeMs = statSync(recPath).mtimeMs; } catch { recMtimeMs = Date.now(); }

    // Already delivered? (repairs journalDelete/delete races + crash windows;
    // also catches path-A posts via the (sender, body) check.)
    try {
      if (deliveredAlready(chanDir, uuid, sender, message, recMtimeMs)) {
        unlinkSync(recPath);
        nAlready++;
        continue;
      }
    } catch { /* fall through to post attempt */ }

    // Post it: same frontmatter shape as fleet-post path B, same uuid.
    const slug = sender.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "agent";
    const nowMs = Date.now();
    const outName = `${nowMs}-${slug}-${uuid}.md`;
    const front = `---\nseq: ts-${nowMs}\nfrom: ${sender}\nto: all\nchannel: ${channel}\nts: ${ts}\nstatus: discussion\nuuid: ${uuid}\ntitle: msg\n---\n${message}\n`;
    const outPath = join(chanDir, outName);
    try {
      writeFileSync(outPath, front);
      if (statSync(outPath).size > 0) {
        unlinkSync(recPath);
        nCompleted++;
        log(`completed COMPLETED ${outName} uuid=${uuid}`);
      } else {
        bad("write-failed");
      }
    } catch {
      bad("write-failed");
    }
  }

  if (nCompleted > 0 || nBad > 0 || nAlready > 0) {
    log(`sweep done: completed=${nCompleted} already_delivered=${nAlready} bad=${nBad}`);
  }
}

main();
