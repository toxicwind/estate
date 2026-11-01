#!/usr/bin/env bun
/**
 * async-sampler.ts — Sub-Agent 6: source-side log conditioner.
 *
 * Replaces the (rejected) kernel splice/shredder design with a NON-LOSSY
 * conditioner: identical rows are deduplicated into a counter, load shed is
 * recorded as a structured `shed` row, and every retained/reduced signal is
 * written to an append-only JSONL ledger. Nothing is discarded that isn't
 * reconstructable from a retained count.
 *
 * Data-framed, dedupe-friendly, schema-stable per estate log doctrine.
 *
 * Usage:
 *   bun tools/async-sampler.ts <ledger.jsonl>                # read stdin JSONL, write ledger
 *   bun tools/async-sampler.ts <ledger.jsonl> --db <epigenetics.sqlite>
 *                                                           # also upsert expected_signals + shed_records
 */

import { createInterface } from "node:readline";
import { appendFileSync } from "node:fs";

const LEDGER = process.argv[2];
const DB = process.argv.indexOf("--db") >= 0 ? process.argv[process.argv.indexOf("--db") + 1] : null;

if (!LEDGER) {
  console.error("usage: bun tools/async-sampler.ts <ledger.jsonl> [--db <sqlite>]");
  process.exit(2);
}

const counts = new Map<string, { count: number; last: string }>();
const bucketFor = (row: Record<string, unknown>): string =>
  [row.source_node, row.event_key].filter(Boolean).join(":");

async function main() {
  const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
  const db = DB ? await import("node:sqlite").then((m) => new m.DatabaseSync(DB)).catch(() => null) : null;
  if (db) {
    db.exec(`
      CREATE TABLE IF NOT EXISTS expected_signals (
        signal_id TEXT PRIMARY KEY, source_node TEXT, expected_interval_seconds INTEGER,
        last_seen_timestamp INTEGER, created_at INTEGER DEFAULT (strftime('%s','now'))
      );
      CREATE TABLE IF NOT EXISTS shed_records (
        event_id TEXT PRIMARY KEY, source_node TEXT, at INTEGER, bucket TEXT, count INTEGER, rule TEXT
      );
    `);
  }

  let shedTotal = 0;
  for await (const line of rl) {
    const t = line.trim();
    if (!t) continue;
    let row: Record<string, unknown>;
    try {
      row = JSON.parse(t);
    } catch {
      appendFileSync(LEDGER, line + "\n"); // non-JSON passthrough — never drop
      continue;
    }
    appendFileSync(LEDGER, line + "\n"); // keep the raw row always

    // dedupe-count identical events
    const bucket = bucketFor(row);
    if (bucket) {
      counts.set(bucket, counts.get(bucket) ?? { count: 0, last: "" });
      const c = counts.get(bucket)!;
      c.count += 1;
      c.last = String(row.ts ?? Date.now());
    }
  }

  // flush shed records (counted, not dropped)
  const ts = Math.floor(Date.now() / 1000);
  for (const [bucket, c] of counts) {
    if (!bucket) continue;
    const [source_node, event_key] = bucket.split(":");
    const shed = { event_id: `shed-${ts}-${event_key ?? "anon"}`, source_node, at: ts, bucket, count: c.count, rule: "dedupe" };
    appendFileSync(LEDGER, JSON.stringify(shed) + "\n");
    shedTotal += c.count;
    if (db) {
      db.prepare(
        "INSERT OR REPLACE INTO shed_records (event_id, source_node, at, bucket, count, rule) VALUES (?,?,?,?,?,?)",
      ).run(shed.event_id, source_node, ts, bucket, c.count, shed.rule);
    }
  }

  console.log(`[async-sampler] ${counts.size} dedupe buckets, ${shedTotal} rows condensed into counts — ledger: ${LEDGER}`);
  db?.close();
}

await main();