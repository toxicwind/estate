/**
 * delivery-ledger.ts — SQLite delivery ledger for the yote Telegram gateway.
 *
 * At-least-once delivery with idempotent processing. The store interface shape
 * (commitInbound / markProcessed-terminal / loadOffset / saveOffset /
 * listUnprocessed) is borrowed from thesongzhu/Friday's TelegramInboxStore
 * (MIT) — adapted to bun:sqlite and to this gateway's real structure
 * (src/yote.ts + src/lib/*, single-bot scope).
 *
 * Two watermarks, kept deliberately separate:
 *   1. poll cursor (telegram_poll_cursor): advanced at inbox-commit time,
 *      BEFORE processing ("commit-before-process"). This is the offset handed
 *      to Telegram getUpdates, so committed updates are never re-fetched.
 *   2. processed watermark: MAX(update_id) with a terminal status
 *      (processed | dead_lettered). Advances ONLY at terminal state.
 *      A crash mid-processing leaves the row pending/processing -> the
 *      re-drive sweep (and boot reconciliation) replays it, while the
 *      send-dedupe table guarantees the reply is never sent twice.
 *
 * The DB lives OUTSIDE the repo (~/.yote/delivery-ledger.db): it is runtime
 * state, never declared config, so the GitOps reconciler must not touch it.
 */

import { Database } from "bun:sqlite";
import { createHash } from "node:crypto";
import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { mkdirSync } from "node:fs";

export const BOT_CHANNEL = "bot";
/** Same logical reply may not be re-sent within this window. */
export const DEDUPE_WINDOW_MS = 24 * 3600 * 1000;
/** Dedupe rows older than this are pruned (must exceed the window). */
export const DEDUPE_PRUNE_MS = 48 * 3600 * 1000;

export type InboxStatus =
  | "pending"
  | "processing"
  | "processed"
  | "delivery_unknown"
  | "dead_lettered";
export type TerminalStatus = "processed" | "dead_lettered";

const SCHEMA = `
CREATE TABLE IF NOT EXISTS telegram_inbox (
  channel_id      TEXT NOT NULL,
  update_id       INTEGER NOT NULL,
  update_json     TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','processing','processed','delivery_unknown','dead_lettered')),
  attempts        INTEGER NOT NULL DEFAULT 0,
  attempted_at_ms INTEGER,
  last_error      TEXT,
  received_at_ms  INTEGER NOT NULL,
  processed_at_ms INTEGER,
  PRIMARY KEY (channel_id, update_id)
);
CREATE TABLE IF NOT EXISTS telegram_poll_cursor (
  channel_id    TEXT PRIMARY KEY,
  offset        INTEGER NOT NULL,
  updated_at_ms INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS send_dedupe (
  dedupe_key    TEXT PRIMARY KEY,
  chat_id       INTEGER NOT NULL,
  update_id     INTEGER NOT NULL,
  created_at_ms INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger_kv (
  key           TEXT PRIMARY KEY,
  value         TEXT NOT NULL,
  updated_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inbox_status ON telegram_inbox(channel_id, status);
CREATE INDEX IF NOT EXISTS idx_dedupe_created ON send_dedupe(created_at_ms);
`;

export function defaultLedgerPath(): string {
  const home = process.env.HOME || homedir() || "/home/toxic";
  return process.env.YOTE_LEDGER_DB || join(home, ".yote", "delivery-ledger.db");
}

export function sha256Hex(s: string): string {
  return createHash("sha256").update(s, "utf8").digest("hex");
}

export interface CommitResult {
  inserted: boolean;
  status: InboxStatus;
}

export interface InboxRow {
  update_id: number;
  update_json: string;
  attempts: number;
  status: InboxStatus;
}

export class DeliveryLedger {
  private db: Database;
  readonly path: string;

  constructor(dbPath: string = defaultLedgerPath()) {
    this.path = dbPath;
    mkdirSync(dirname(dbPath), { recursive: true });
    this.db = new Database(dbPath, { create: true });
    // WAL: a SIGKILL mid-write cannot corrupt the ledger; readers never block.
    this.db.exec("PRAGMA journal_mode=WAL;");
    this.db.exec("PRAGMA busy_timeout=5000;");
    this.db.exec(SCHEMA);
  }

  close(): void {
    this.db.close();
  }

  /**
   * Idempotent inbox commit. INSERT OR IGNORE on (channel_id, update_id):
   * a redelivered update_id yields exactly one row. Returns whether the row
   * is new and its current status so the caller can skip terminal rows.
   */
  commitInbound(channelId: string, update: unknown): CommitResult {
    const updateId = (update as any)?.update_id;
    if (typeof updateId !== "number" || !Number.isFinite(updateId)) {
      throw new Error("commitInbound: update without numeric update_id");
    }
    const ins = this.db
      .prepare(
        `INSERT OR IGNORE INTO telegram_inbox
         (channel_id, update_id, update_json, status, attempts, received_at_ms)
         VALUES (?, ?, ?, 'pending', 0, ?)`,
      )
      .run(channelId, updateId, JSON.stringify(update), Date.now());
    if (Number(ins.changes) > 0) return { inserted: true, status: "pending" };
    const row = this.db
      .prepare(
        `SELECT status FROM telegram_inbox WHERE channel_id = ? AND update_id = ?`,
      )
      .get(channelId, updateId) as { status: InboxStatus };
    return { inserted: false, status: row.status };
  }

  /** Count one processing attempt; returns the new attempt count. */
  markAttempt(channelId: string, updateId: number): number {
    const now = Date.now();
    this.db
      .prepare(
        `UPDATE telegram_inbox
         SET attempts = attempts + 1, attempted_at_ms = ?, status = 'processing'
         WHERE channel_id = ? AND update_id = ?
           AND status IN ('pending','delivery_unknown','processing')`,
      )
      .run(now, channelId, updateId);
    const row = this.db
      .prepare(
        `SELECT attempts FROM telegram_inbox WHERE channel_id = ? AND update_id = ?`,
      )
      .get(channelId, updateId) as { attempts: number };
    return row.attempts;
  }

  /** Terminal transition: replied, deduped-skip, or dead-lettered. */
  markTerminal(
    channelId: string,
    updateId: number,
    status: TerminalStatus,
    error?: string,
  ): void {
    this.db
      .prepare(
        `UPDATE telegram_inbox
         SET status = ?, processed_at_ms = ?, last_error = COALESCE(?, last_error)
         WHERE channel_id = ? AND update_id = ?`,
      )
      .run(status, Date.now(), error ?? null, channelId, updateId);
  }

  /**
   * Boot reconciliation: rows left pending/processing by a crash become
   * delivery_unknown and are returned for re-driving through the same
   * dedupe-guarded path. Pending rows are NEVER pruned.
   */
  reconcileBoot(channelId: string): InboxRow[] {
    this.db
      .prepare(
        `UPDATE telegram_inbox SET status = 'delivery_unknown'
         WHERE channel_id = ? AND status IN ('pending','processing')`,
      )
      .run(channelId);
    return this.listRedrivable(channelId, Number.MAX_SAFE_INTEGER, Date.now(), 0);
  }

  /**
   * Rows safe to re-drive: non-terminal, under the attempt cap, and past the
   * cooldown SINCE THEIR LAST ATTEMPT (a poison update backs off instead of
   * spinning). 'processing' rows seen here are necessarily stale — the poll
   * loop is single-threaded, so no live proc owns them.
   */
  listRedrivable(
    channelId: string,
    maxAttempts: number,
    nowMs: number,
    cooldownMs = 30_000,
  ): InboxRow[] {
    return this.db
      .prepare(
        `SELECT update_id, update_json, attempts, status FROM telegram_inbox
         WHERE channel_id = ? AND status IN ('pending','processing','delivery_unknown')
           AND attempts < ? AND COALESCE(attempted_at_ms, received_at_ms) <= ?
         ORDER BY update_id ASC`,
      )
      .all(channelId, maxAttempts, nowMs - cooldownMs) as InboxRow[];
  }

  /** Poll cursor for getUpdates. 0 when never committed. */
  loadOffset(channelId: string): number {
    const row = this.db
      .prepare(`SELECT offset FROM telegram_poll_cursor WHERE channel_id = ?`)
      .get(channelId) as { offset: number } | null;
    return row ? row.offset : 0;
  }

  /** Monotonic commit-before-process: the cursor never regresses. */
  saveOffset(channelId: string, offset: number): void {
    this.db
      .prepare(
        `INSERT INTO telegram_poll_cursor (channel_id, offset, updated_at_ms)
         VALUES (?, ?, ?)
         ON CONFLICT(channel_id) DO UPDATE
         SET offset = excluded.offset, updated_at_ms = excluded.updated_at_ms
         WHERE excluded.offset > telegram_poll_cursor.offset`,
      )
      .run(channelId, offset, Date.now());
  }

  /**
   * Terminal-state watermark: MAX(update_id) with status processed|dead_lettered.
   * Advances ONLY when an update reaches a terminal state — never on "consumed".
   */
  processedWatermark(channelId: string): number {
    const row = this.db
      .prepare(
        `SELECT MAX(update_id) AS m FROM telegram_inbox
         WHERE channel_id = ? AND status IN ('processed','dead_lettered')`,
      )
      .get(channelId) as { m: number | null };
    return row.m ?? 0;
  }

  static sendDedupeKey(
    scope: string,
    chatId: number,
    updateId: number,
    textHash: string,
  ): string {
    return `${scope}:${chatId}:${updateId}:${textHash}`;
  }

  /**
   * Claim a send. true = first claim, proceed. false = the same logical
   * message was already claimed: skip it — no duplicate sends, ever.
   * The claim is taken BEFORE the send attempt on purpose: if the process
   * dies after Telegram accepted the message but before we saw the response,
   * the replay must NOT re-send. A failed send goes to the DLQ (operator-
   * visible); the DLQ replay uses its own key scope so it can still deliver.
   * Claims older than the dedupe window may be reclaimed (genuine repeats
   * after 24h are allowed).
   */
  claimSend(
    chatId: number,
    updateId: number,
    textHash: string,
    nowMs = Date.now(),
    windowMs = DEDUPE_WINDOW_MS,
    scope = "send",
  ): boolean {
    const key = DeliveryLedger.sendDedupeKey(scope, chatId, updateId, textHash);
    const ins = this.db
      .prepare(
        `INSERT OR IGNORE INTO send_dedupe (dedupe_key, chat_id, update_id, created_at_ms)
         VALUES (?, ?, ?, ?)`,
      )
      .run(key, chatId, updateId, nowMs);
    if (Number(ins.changes) > 0) return true;
    const row = this.db
      .prepare(`SELECT created_at_ms FROM send_dedupe WHERE dedupe_key = ?`)
      .get(key) as { created_at_ms: number };
    if (nowMs - row.created_at_ms > windowMs) {
      this.db.prepare(`DELETE FROM send_dedupe WHERE dedupe_key = ?`).run(key);
      this.db
        .prepare(
          `INSERT INTO send_dedupe (dedupe_key, chat_id, update_id, created_at_ms)
           VALUES (?, ?, ?, ?)`,
        )
        .run(key, chatId, updateId, nowMs);
      return true;
    }
    return false;
  }

  pruneSendDedupe(nowMs = Date.now(), olderThanMs = DEDUPE_PRUNE_MS): number {
    const r = this.db
      .prepare(`DELETE FROM send_dedupe WHERE created_at_ms < ?`)
      .run(nowMs - olderThanMs);
    return Number(r.changes);
  }

  recordSuccessfulSend(nowMs = Date.now()): void {
    this.setKv("last_successful_send_ms", String(nowMs), nowMs);
  }

  recordOpenFangLatency(ms: number, nowMs = Date.now()): void {
    this.setKv("last_openfang_ms", String(nowMs), nowMs);
    this.setKv("last_openfang_latency_ms", String(Math.round(ms)), nowMs);
  }

  private setKv(key: string, value: string, nowMs: number): void {
    this.db
      .prepare(
        `INSERT INTO ledger_kv (key, value, updated_at_ms) VALUES (?, ?, ?)
         ON CONFLICT(key) DO UPDATE
         SET value = excluded.value, updated_at_ms = excluded.updated_at_ms`,
      )
      .run(key, value, nowMs);
  }

  private getKv(key: string): string | null {
    const row = this.db
      .prepare(`SELECT value FROM ledger_kv WHERE key = ?`)
      .get(key) as { value: string } | null;
    return row ? row.value : null;
  }

  inboxDepth(channelId: string): { pending: number; deliveryUnknown: number } {
    const p = this.db
      .prepare(
        `SELECT COUNT(*) AS c FROM telegram_inbox WHERE channel_id = ? AND status = 'pending'`,
      )
      .get(channelId) as { c: number };
    const d = this.db
      .prepare(
        `SELECT COUNT(*) AS c FROM telegram_inbox WHERE channel_id = ? AND status IN ('processing','delivery_unknown')`,
      )
      .get(channelId) as { c: number };
    return { pending: p.c, deliveryUnknown: d.c };
  }

  dlqDepth(channelId: string): number {
    const row = this.db
      .prepare(
        `SELECT COUNT(*) AS c FROM telegram_inbox WHERE channel_id = ? AND status = 'dead_lettered'`,
      )
      .get(channelId) as { c: number };
    return row.c;
  }

  listDeadLettered(channelId: string): InboxRow[] {
    return this.db
      .prepare(
        `SELECT update_id, update_json, attempts, status FROM telegram_inbox
         WHERE channel_id = ? AND status = 'dead_lettered' ORDER BY update_id ASC`,
      )
      .all(channelId) as InboxRow[];
  }

  healthStats(channelId: string = BOT_CHANNEL): {
    pollOffset: number;
    processedWatermark: number;
    inboxPending: number;
    inboxDeliveryUnknown: number;
    dlqDepth: number;
    lastSuccessfulSendMs: number | null;
    lastOpenFangMs: number | null;
    lastOpenFangLatencyMs: number | null;
  } {
    const depth = this.inboxDepth(channelId);
    const num = (k: string): number | null => {
      const v = this.getKv(k);
      return v === null ? null : Number(v);
    };
    return {
      pollOffset: this.loadOffset(channelId),
      processedWatermark: this.processedWatermark(channelId),
      inboxPending: depth.pending,
      inboxDeliveryUnknown: depth.deliveryUnknown,
      dlqDepth: this.dlqDepth(channelId),
      lastSuccessfulSendMs: num("last_successful_send_ms"),
      lastOpenFangMs: num("last_openfang_ms"),
      lastOpenFangLatencyMs: num("last_openfang_latency_ms"),
    };
  }
}
