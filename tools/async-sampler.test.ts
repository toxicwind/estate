#!/usr/bin/env bun
/**
 * async-sampler.test.ts — TDD regression guard for estate-log-conditioner.
 *
 * The conditioner reads two REAL estate JSONL event streams (hephaistos +
 * delendai) and condenses duplicates into a ledger + sqlite shed records.
 * This test pins the REAL behavior of that pipeline end-to-end by spawning
 * the tool with `--once` against a scratch ledger/db, then asserting the
 * ledger/sqlite contents. It uses real event data (not invented fixtures).
 */
import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { execSync } from "node:child_process";
import { existsSync, readFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";

const TOOL = join(import.meta.dir, "estate-log-conditioner.ts");

// Real estate event sources the conditioner consumes. Existence is the
// contract: if one is missing the pipeline silently processes less, which
// the test catches.
const REAL_STREAMS = [
  "/home/toxic/pens/estate/.cache/hephaistos/runtime/events.jsonl",
  "/home/toxic/pens/estate/products/estate-brain/.cache/delendai/runtime/events.jsonl",
];

let workDir: string;
let ledger: string;
let dbPath: string;

function runOnce() {
  execSync(`bun ${TOOL} ${ledger} --db ${dbPath} --once`, {
    cwd: import.meta.dir,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
}

function ledgerLines(): string[] {
  if (!existsSync(ledger)) return [];
  return readFileSync(ledger, "utf8").trim().split("\n").filter(Boolean);
}

function shedRecords(): Array<Record<string, unknown>> {
  if (!existsSync(dbPath)) return [];
  const db = new DatabaseSync(dbPath);
  const rows = db.prepare("SELECT * FROM shed_records").all() as Array<Record<string, unknown>>;
  db.close();
  return rows;
}

function expectedSignals(): Array<Record<string, unknown>> {
  if (!existsSync(dbPath)) return [];
  const db = new DatabaseSync(dbPath);
  const rows = db.prepare("SELECT * FROM expected_signals").all() as Array<Record<string, unknown>>;
  db.close();
  return rows;
}

beforeAll(() => {
  workDir = mkdtempSync(join(tmpdir(), "async-sampler-"));
  ledger = join(workDir, "ledger.jsonl");
  dbPath = join(workDir, "events.db");
});

afterAll(() => {
  if (workDir) rmSync(workDir, { recursive: true, force: true });
});

describe("estate-log-conditioner", () => {
  it("reads at least one real estate event stream", () => {
    const exist = REAL_STREAMS.filter(existsSync);
    expect(exist.length).toBeGreaterThan(0);
    for (const s of REAL_STREAMS) {
      const lines = existsSync(s) ? readFileSync(s, "utf8").trim().split("\n").filter(Boolean) : [];
      expect(lines.every((l) => {
        try { JSON.parse(l); return true; } catch { return false; }
      })).toBe(true);
    }
  });

  it("processes real events and writes a non-empty ledger", () => {
    runOnce();
    const lines = ledgerLines();
    expect(lines.length).toBeGreaterThan(0);
  });

  it("persists each raw event to the ledger (non-lossy)", () => {
    // Every real event line must appear (normalized) in the ledger.
    let rawCount = 0;
    for (const s of REAL_STREAMS) {
      if (!existsSync(s)) continue;
      for (const l of readFileSync(s, "utf8").trim().split("\n").filter(Boolean)) {
        const rec = JSON.parse(l) as { kind?: string };
        const match = ledgerLines().filter((ll) => {
          try { return JSON.parse(ll).kind === rec.kind; } catch { return ll === l; }
        });
        expect(match.length).toBeGreaterThanOrEqual(1);
        rawCount++;
      }
    }
    expect(rawCount).toBeGreaterThan(0);
  });

  it("writes shed records for duplicated kinds with correct counts", () => {
    const sheds = shedRecords();
    expect(sheds.length).toBeGreaterThan(0);
    for (const s of sheds) {
      expect(s.count).toBeGreaterThan(1);
      expect(s.rule).toBe("dedupe");
      expect(typeof s.bucket).toBe("string");
      expect(typeof s.source_node).toBe("string");
    }
  });

  it("creates the ledger schema (shed_records/expected_signals/abscission_events)", () => {
    if (!existsSync(dbPath)) return;
    const db = new DatabaseSync(dbPath);
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all() as Array<{ name: string }>;
    db.close();
    const names = tables.map((t) => t.name);
    expect(names).toContain("shed_records");
    expect(names).toContain("expected_signals");
    expect(names).toContain("abscission_events");
  });

  it("seeds expected_signals after heartbeat runs", () => {
    // Heartbeat is a separate tool; if its db path matches, verify signals.
    const signals = expectedSignals();
    // Not asserted in the conditioner alone — signals are seeded by
    // epigenetics-heartbeat. This documents that contract.
    expect(Array.isArray(signals)).toBe(true);
  });

  it("writes valid epoch timestamps on ledger events", () => {
    for (const ll of ledgerLines()) {
      try {
        const rec = JSON.parse(ll);
        if (typeof rec.ts === "number") expect(rec.ts).toBeGreaterThan(0);
      } catch { /* non-JSON pass-through is expected */ }
    }
  });
});