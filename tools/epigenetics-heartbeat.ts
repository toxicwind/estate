#!/usr/bin/env bun
/**
 * epigenetics-heartbeat.ts — Sub-Agent 6: heartbeat register.
 *
 * Scans the dedupe ledger (async-sampler output) to discover every
 * source_node:event_key bucket that has emitted data, then seeds or
 * refreshes the expected_signals row:
 *   - expected_interval = average time between consecutive emits
 *   - last_seen         = most recent emit timestamp
 *
 * Writes directly into the sqlite ledger database created by the sampler.
 *
 * Usage:
 *   bun epigenetics-heartbeat.ts <ledger.jsonl> --db <estate.db> [--force]
 */

import { readFileSync, writeFileSync, existsSync, appendFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";

type Args = { ledgerPath: string; dbPath: string; force: boolean };

function parseArgs(): Args {
  const a = process.argv.slice(2);
  let ledgerPath = "", dbPath = "", force = false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] === "--db" || a[i] === "-d") dbPath = a[++i];
    else if (a[i] === "--force" || a[i] === "-f") force = true;
    else if (!a[i].startsWith("-")) ledgerPath = a[i];
  }
  if (!ledgerPath || !dbPath) {
    console.error("usage: epigenetics-heartbeat.ts <ledger.jsonl> --db <db.sqlite> [--force]");
    process.exit(2);
  }
  return { ledgerPath, dbPath, force };
}

function dedupeIntervals(events: number[]): number[] {
  // sorted time differences
  const sorted = events.slice().sort((a, b) => a - b);
  const diffs: number[] = [];
  for (let i = 1; i < sorted.length; i++) diffs.push(sorted[i] - sorted[i - 1]);
  return diffs;
}

function main() {
  const { ledgerPath, dbPath, force } = parseArgs();

  if (!existsSync(ledgerPath)) {
    console.error(`ledger not found: ${ledgerPath}`);
    process.exit(1);
  }

  const db = new DatabaseSync(dbPath);
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

  // Scan ledger for shed records to discover buckets
  type BucketInfo = { source_node: string; bucket: string; events: number[]; total_count: number };
  const buckets = new Map<string, BucketInfo>();

  for (const line of readFileSync(ledgerPath, "utf8").trim().split("\n")) {
    if (!line) continue;
    const rec = JSON.parse(line) as { source_node?: string; bucket?: string; ts?: number; at?: number; event_key?: string; rule?: string; count?: number };
    if (rec.rule === "dedupe" && rec.source_node && rec.bucket && rec.at) {
      const key = rec.bucket;
      const info = buckets.get(key) || { source_node: rec.source_node, bucket: key, events: [], total_count: 0 };
      info.events.push(rec.at);
      info.total_count += rec.count || 1;
      buckets.set(key, info);
    }
  }

  // Scan ledger for raw records to discover event_key timestamps
  for (const line of readFileSync(ledgerPath, "utf8").trim().split("\n")) {
    if (!line) continue;
    const rec = JSON.parse(line) as { source_node?: string; event_key?: string; ts?: number };
    if (rec.source_node && rec.event_key && rec.ts) {
      const key = `${rec.source_node}:${rec.event_key}`;
      const info = buckets.get(key) || { source_node: rec.source_node, bucket: key, events: [], total_count: 0 };
      info.events.push(rec.ts);
      buckets.set(key, info);
    }
  }

  let registered = 0, refreshed = 0;
  const stmt = db.prepare(
    "INSERT OR REPLACE INTO expected_signals (signal_id, source_node, expected_interval_seconds, last_seen_timestamp) VALUES (?, ?, ?, ?)"
  );

  for (const [sigId, info] of buckets) {
    const intervals = dedupeIntervals(info.events);
    const avgMs = intervals.length > 0
      ? Math.round(intervals.reduce((a, b) => a + b, 0) / intervals.length)
      : 60; // default 60s if single event
    const lastSeen = info.events.length > 0 ? Math.max(...info.events) : 0;

    stmt.run(sigId, info.source_node, avgMs, lastSeen);

    if (info.events.length === 1 && lastSeen > 0) {
      registered++;
    } else if (info.events.length > 1) {
      refreshed++;
    }
  }

  // If force: also register all shed-record-only buckets with high threshold
  if (force) {
    for (const line of readFileSync(ledgerPath, "utf8").trim().split("\n")) {
      if (!line) continue;
      const rec = JSON.parse(line) as { event_id?: string; bucket?: string; at?: number; rule?: string };
      if (rec.rule === "shed" && rec.bucket && rec.at) {
        const sigId = rec.event_id!;
        const exists = db.prepare("SELECT 1 FROM expected_signals WHERE signal_id = ?")
          .get(sigId);
        if (!exists) {
          stmt.run(sigId, "unknown", 300, rec.at);
          registered++;
        }
      }
    }
  }

  const total = buckets.size;
  db.close();
  console.log(`heartbeat registered: ${registered} new, ${refreshed} refreshed, ${total - registered - refreshed} unchanged of ${total}`);
}

main();
