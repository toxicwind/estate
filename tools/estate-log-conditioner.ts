#!/usr/bin/env bun
/**
 * estate-log-conditioner.ts — Sub-Agent 6: integrates async-sampler into the estate log lifecycle.
 *
 * Tails all known estate JSONL event streams, feeds lines through the
 * dedupe ledger, and appends to the ledger file. The epigenetics-watcher
 * then runs on the ledger on its own interval.
 *
 * Estate event format (from delendai/hephaistos):
 *   { version: 1, ts: "2026-10-31T04:48:47.093Z", kind: "session.started", meta: {...} }
 *
 * Usage:
 *   bun estate-log-conditioner.ts <ledger.jsonl>
 *     [--db <estate.db>] --squawk-token <token> [--watch|--once]
 */

import { existsSync, readFileSync, writeFileSync, appendFileSync } from "node:fs";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";

type Args = {
  ledgerPath: string;
  dbPath: string;
  squawkToken: string;
  watch: boolean;
  runOnce: boolean;
};

function parseArgs(): Args {
  const a = process.argv.slice(2);
  let ledgerPath = "", dbPath = "", squawkToken = "", watch = false, runOnce = false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] === "--db" || a[i] === "-d") dbPath = a[++i];
    else if (a[i] === "--squawk-token") squawkToken = a[++i];
    else if (a[i] === "--watch") watch = true;
    else if (a[i] === "--once" || a[i] === "-1") runOnce = true;
    else if (!a[i].startsWith("-")) ledgerPath = a[i];
  }
  if (!ledgerPath) {
    console.error("usage: estate-log-conditioner.ts <ledger.jsonl> [--db <db>] [--squawk-token <token>] [--watch|--once]");
    process.exit(2);
  }
  return { ledgerPath, dbPath: dbPath || join("/home/toxic/pens/estate/db", "estate-events.db"), squawkToken, watch, runOnce };
}

const ESTATE_EVENT_PATHS = [
  "/home/toxic/pens/estate/.cache/hephaistos/runtime/events.jsonl",
  "/home/toxic/pens/estate/products/estate-brain/.cache/delendai/runtime/events.jsonl",
];

/**
 * Estate event record (from delendai/hephaistos runtime).
 * Format: { version, ts: ISO-string, kind, meta, sessionId }
 */
type EventRecord = {
  version?: number;
  kind?: string;
  ts?: string | number;
  meta?: Record<string, unknown>;
  sessionId?: string;
  [k: string]: unknown;
};

/** Dedupe key: source_node + kind (estate events use kind, not event_key). */
function dedupeKey(rec: EventRecord): string {
  const src = rec.source_node || "anon";
  const key = rec.kind || "unknown";
  return `${src}:${key}`;
}

/** Parse ISO ts string to epoch seconds, or return current time. */
function parseTs(rec: EventRecord): number {
  if (typeof rec.ts === "number") return rec.ts;
  if (typeof rec.ts === "string") {
    const d = new Date(rec.ts);
    if (!isNaN(d.getTime())) return Math.floor(d.getTime() / 1000);
  }
  return Math.floor(Date.now() / 1000);
}

/** Write a shed record to the ledger. */
function writeShed(ledger: string, sourceNode: string, eventKey: string, ts: number, count: number): void {
  const shed = {
    event_id: `shed-${ts}-${eventKey}`,
    source_node: sourceNode,
    at: ts,
    bucket: `${sourceNode}:${eventKey}`,
    count,
    rule: "dedupe",
  };
  appendFileSync(ledger, JSON.stringify(shed) + "\n");
}

/** Post to squawk (non-blocking). */
async function postToSquawk(token: string, signalId: string, reason: string): Promise<void> {
  if (!token) return;
  try {
    await fetch("http://127.0.0.1:25120/v1/rooms/fleet/messages", {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ title: `dedupe: ${signalId}`, body: `Condensed ${signalId}`, priority: "low" }),
    }).catch(() => {});
  } catch { /* squawk down is non-fatal */ }
}

/** Process a batch of events from a log file. */
function processLog(logPath: string, ledger: string, db: DatabaseSync | null): { events: number; shed: number } {
  if (!existsSync(logPath)) return { events: 0, shed: 0 };

  const content = readFileSync(logPath, "utf8").trim();
  if (!content) return { events: 0, shed: 0 };

  const lines = content.split("\n");
  const counts = new Map<string, number>();
  let shedTotal = 0;

  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const rec = JSON.parse(line) as EventRecord;
      const bucket = dedupeKey(rec);
      const ts = parseTs(rec);
      const src = rec.source_node || "anon";
      const key = rec.kind || "unknown";

      // Write raw event to ledger
      const rawLedgerLine = { source_node: src, event_key: key, ts, kind: rec.kind, at: ts };
      appendFileSync(ledger, JSON.stringify(rawLedgerLine) + "\n");
      counts.set(bucket, (counts.get(bucket) || 0) + 1);
    } catch {
      // Non-JSON lines pass through as-is (log doctrine: don't lose bytes)
      appendFileSync(ledger, line + "\n");
    }
  }

  // Condense and write shed records
  const insertStmt = db?.prepare(
    "INSERT OR REPLACE INTO shed_records (event_id, source_node, at, bucket, count, rule) VALUES (?,?,?,?,?,?)"
  );

  for (const [bucket, count] of counts) {
    if (count <= 1) continue;
    const [source, key] = bucket.split(":");
    const ts = Math.floor(Date.now() / 1000);

    writeShed(ledger, source, key, ts, count);
    shedTotal += count;

    if (db && insertStmt) {
      insertStmt.run(
        `shed-${ts}-${key}`, source, ts, bucket, count, "dedupe"
      );
    }
  }

  return { events: lines.length, shed: shedTotal };
}

async function main() {
  const { ledgerPath, dbPath, squawkToken, watch, runOnce } = parseArgs();

  // Ensure ledger exists
  if (!existsSync(ledgerPath)) {
    writeFileSync(ledgerPath, "");
  }

  const db = dbPath ? new DatabaseSync(dbPath) : null;
  if (db) {
    db.exec(`
      CREATE TABLE IF NOT EXISTS shed_records (
        event_id TEXT PRIMARY KEY,
        source_node TEXT,
        at INTEGER,
        bucket TEXT,
        count INTEGER,
        rule TEXT
      );
      CREATE TABLE IF NOT EXISTS expected_signals (
        signal_id TEXT PRIMARY KEY,
        source_node TEXT,
        expected_interval_seconds INTEGER,
        last_seen_timestamp INTEGER
      );
      CREATE TABLE IF NOT EXISTS abscission_events (
        event_id TEXT PRIMARY KEY,
        signal_id TEXT,
        timestamp INTEGER,
        reason TEXT
      );
    `);
  }

  let totalEvents = 0;
  let totalShed = 0;

  function processAll() {
    let events = 0, shed = 0;
    for (const path of ESTATE_EVENT_PATHS) {
      const result = processLog(path, ledgerPath, db);
      events += result.events;
      shed += result.shed;
    }
    totalEvents += events;
    totalShed += shed;
    console.log(`[conditioner] processed ${events} events, shed ${shed} into counts`);

    // Post shed summary to squawk
    if (squawkToken && totalShed > 0) {
      postToSquawk(squawkToken, "estate-conditioner", `Condensed ${totalShed} events into dedupe counts`);
    }
  }

  processAll();
  console.log(`[conditioner] started (ledger=${ledgerPath}, db=${dbPath || "none"}, watch=${watch}, squawk=${!!squawkToken})`);

  if (runOnce) {
    db?.close();
    return;
  }

  if (watch) {
    setInterval(processAll, 30_000); // 30s interval
  }

  // Graceful shutdown
  process.on("SIGTERM", () => {
    console.log(`[conditioner] shutdown (total events: ${totalEvents}, shed: ${totalShed})`);
    db?.close();
    process.exit(0);
  });
}

main();
