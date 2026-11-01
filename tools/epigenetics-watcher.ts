#!/usr/bin/env bun
/**
 * epigenetics-watcher.ts — Sub-Agent 6: negative-space detector.
 *
 * Periodically queries expected_signals for staleness (abscission),
 * writes structured records, and posts anomalies to squawk fleet.
 *
 * Usage:
 *   bun epigenetics-watcher.ts --db <estate.db> --squawk-token <token>
 */

import { existsSync, appendFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";

type Args = { dbPath: string; squawkToken: string; interval: number };

function parseArgs(): Args {
  const a = process.argv.slice(2);
  let dbPath = "", squawkToken = "", interval = 60;
  for (let i = 0; i < a.length; i++) {
    if (a[i] === "--db" || a[i] === "-d") dbPath = a[++i];
    else if (a[i] === "--squawk-token") squawkToken = a[++i];
    else if (a[i] === "--interval" || a[i] === "-i") interval = parseInt(a[++i], 10);
  }
  if (!dbPath) {
    console.error("usage: epigenetics-watcher.ts --db <estate.db> [--squawk-token <token>] [--interval <seconds>]");
    process.exit(2);
  }
  return { dbPath, squawkToken, interval };
}

/** Post an anomaly as a squawk todo item (non-blocking). */
async function postAnomaly(token: string, signalId: string, reason: string, lastSeen: number): Promise<void> {
  if (!token) return;
  const title = `abscission: ${signalId}`;
  const body = `Signal ${signalId} has not been seen since epoch ${lastSeen}. Reason: ${reason}.`;
  try {
    // Post to squawk fleet todo
    await fetch("http://127.0.0.1:25120/v1/rooms/fleet/messages", {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ title, body, priority: "high" }),
    }).catch(() => {});
    // Also write to local squawk todo
    const slug = signalId.replace(/[:/]/g, "-");
    const now = new Date().toISOString().replace(/[:.]/g, "");
    const todoFile = `/home/toxic/pens/ranch/products/squawk/todo/${now}-epigenetics-abscission-${slug}.md`;
    appendFileSync(todoFile, `# ${title}\n\n${body}\n\n> Detected by epigenetics-watcher.ts\n`, "utf8");
    console.log(`[epigenetics] posted abscission: ${signalId} (${reason})`);
  } catch (e) {
    console.error(`[epigenetics] squawk post failed: ${(e as Error).message}`);
  }
}

function main() {
  const { dbPath, squawkToken, interval } = parseArgs();

  if (!existsSync(dbPath)) {
    console.error(`ledger db not found: ${dbPath}`);
    process.exit(1);
  }

  const db = new DatabaseSync(dbPath);

  // Ensure tables exist
  db.exec(`
    CREATE TABLE IF NOT EXISTS expected_signals (
      signal_id TEXT PRIMARY KEY,
      source_node TEXT,
      expected_interval_seconds INTEGER,
      last_seen_timestamp INTEGER
    );
  `);
  db.exec(`
    CREATE TABLE IF NOT EXISTS abscission_events (
      event_id TEXT PRIMARY KEY,
      signal_id TEXT,
      timestamp INTEGER,
      reason TEXT
    );
  `);

  const now = Math.floor(Date.now() / 1000);
  let totalAbscissions = 0;

  const insertStmt = db.prepare(
    "INSERT OR REPLACE INTO abscission_events (event_id, signal_id, timestamp, reason) VALUES (?, ?, ?, ?)"
  );

  const results = db.prepare(
    "SELECT signal_id, source_node, expected_interval_seconds, last_seen_timestamp " +
    "FROM expected_signals " +
    "WHERE (? - last_seen_timestamp) > expected_interval_seconds"
  );

  function runCheck() {
    const rows = results.all(now);
    if (rows.length === 0) return;

    for (const row of rows) {
      const rowTyped = row as { signal_id: string; source_node: string; expected_interval_seconds: number; last_seen_timestamp: number };
      const reason = "timeout";
      const eventId = `abscission-${rowTyped.signal_id.replace(/:/g, "-")}-${now}`;
      insertStmt.run(eventId, rowTyped.signal_id, now, reason);

      postAnomaly(squawkToken, rowTyped.signal_id, reason, rowTyped.last_seen_timestamp);
      totalAbscissions++;
    }
  }

  // Run once immediately, then on interval
  runCheck();
  console.log(`[epigenetics-watcher] started (db=${dbPath}, interval=${interval}s, squawk=${!!squawkToken})`);

  setInterval(() => {
    try { runCheck(); }
    catch (e) {
      console.error(`[epigenetics-watcher] check failed: ${(e as Error).message}`);
    }
  }, interval * 1000);

  // Graceful shutdown
  process.on("SIGTERM", () => {
    db.close();
    console.log(`[epigenetics-watcher] shutdown (total abscissions: ${totalAbscissions})`);
    process.exit(0);
  });
}

main();
