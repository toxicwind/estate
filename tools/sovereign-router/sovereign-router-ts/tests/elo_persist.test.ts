// Elo durability (2026-09-21): provider Elo is written through to the
// HealthDB on every update, restored on restart, falls back to
// bench-priors.json when no stored row exists, and is never clobbered by
// priors on hot-reload.
//
//  1. Kill-restart round trip: live-learned Elo survives close + reopen.
//  2. No stored row -> bench prior (from the committed bench-priors.json).
//  3. Hot-reload (applyBenchPriors) never re-seeds restored/learned Elo.
//  4. Untouched providers still re-seed on priors refresh (benchlink
//     behavior preserved).
//  5. Failure decrements persist too.
import { describe, test, expect } from "bun:test";
import { Database } from "bun:sqlite";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

// Must be set before the router modules are imported (DB_PATH is read once).
// The module-level `state` singleton uses this; the tests below construct
// their own Matrix instances on per-test temp DBs.
process.env.SOVEREIGN_DB = "/tmp/sovereign_router_elo_persist_module.db";

const { Matrix } = await import("../router_matrix");
const { PROVIDERS } = await import("../router_config");

function tmpDb(): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "elo-persist-"));
  return path.join(dir, "router.db");
}

function readPriors(): Record<string, number> {
  const doc = JSON.parse(
    fs.readFileSync(new URL("../bench-priors.json", import.meta.url), "utf8"),
  );
  const out: Record<string, number> = {};
  for (const [p, pr] of Object.entries(doc.priors || {})) {
    const elo = (pr as { elo?: number }).elo;
    if (typeof elo === "number" && Number.isFinite(elo)) out[p] = elo;
  }
  return out;
}

const PROVS = Object.keys(PROVIDERS);

describe("Elo persistence", () => {
  test("kill-restart round trip restores live-learned Elo, not priors", () => {
    const db = tmpDb();
    const m1 = new Matrix(db);
    const p = "groq";
    const prior = m1.elo.get(p);
    expect(typeof prior).toBe("number");
    for (let i = 0; i < 5; i++) m1.record("elo-test-model", p, 200, 0.5);
    const learned = m1.elo.get(p)!;
    expect(learned).toBe(prior! + 5 * 16);
    // Write-through: the row is already in the DB before any restart.
    const ro = new Database(db, { readonly: true });
    const row = ro
      .query(`SELECT elo FROM elo_state WHERE provider=?`)
      .get(p) as { elo: number } | null;
    ro.close();
    expect(row?.elo).toBe(learned);
    // Simulate death: close every handle, then reopen.
    m1.health.conn.close();
    const m2 = new Matrix(db);
    expect(m2.elo.get(p)).toBe(learned);
    m2.health.conn.close();
  });

  test("no stored row falls back to bench priors", () => {
    const db = tmpDb();
    const m = new Matrix(db);
    const priors = readPriors();
    for (const p of PROVS) {
      expect(m.elo.get(p)).toBe(priors[p] ?? 1000);
    }
    m.health.conn.close();
  });

  test("hot-reload never clobbers restored Elo with priors", () => {
    const db = tmpDb();
    const m1 = new Matrix(db);
    const p = "cerebras";
    const prior = m1.elo.get(p)!;
    for (let i = 0; i < 3; i++) m1.record("elo-test-model", p, 429, 0.5);
    const learned = m1.elo.get(p)!;
    expect(learned).toBe(prior - 3 * 8); // moved via live traffic
    m1.health.conn.close();
    const m2 = new Matrix(db);
    expect(m2.elo.get(p)).toBe(learned); // restored, not the prior
    // Pretend bench-priors.json changed: force re-evaluation.
    m2.priorsMtime = 0;
    const r = m2.applyBenchPriors();
    expect(r.reloaded).toBe(true);
    expect(r.reseeded).not.toContain(p);
    expect(m2.elo.get(p)).toBe(learned);
    m2.health.conn.close();
  });

  test("untouched providers still re-seed when priors refresh", () => {
    const db = tmpDb();
    const m = new Matrix(db);
    const priors = readPriors();
    const p = "mistral";
    expect(m.elo.get(p)).toBe(priors[p] ?? 1000); // untouched by traffic
    m.priorsMtime = 0; // pretend the priors file changed
    const r = m.applyBenchPriors();
    expect(r.reseeded).toContain(p);
    expect(m.elo.get(p)).toBe(priors[p] ?? 1000);
    m.health.conn.close();
  });

  test("failure decrements persist too", () => {
    const db = tmpDb();
    const m1 = new Matrix(db);
    const p = "nvidia";
    const prior = m1.elo.get(p)!;
    m1.record("elo-test-model", p, 500, 1.0);
    const after = m1.elo.get(p)!;
    expect(after).toBe(Math.max(100, prior - 32));
    m1.health.conn.close();
    const m2 = new Matrix(db);
    expect(m2.elo.get(p)).toBe(after);
    m2.health.conn.close();
  });
});
