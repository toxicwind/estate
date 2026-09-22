#!/usr/bin/env bun
/**
 * telemetric-oracle.ts — Non-Invasive Database & Telemetry Grounding Supervisor for Super Ralph
 *
 * Architecture Invariants:
 * 1. Zero Keystroke Injection: Never inject C-c or terminal text into running panes.
 * 2. Respect Sovereign Router (:25104): Preserves 114-model ranking pool without socket overriding.
 * 3. Database Grounding: Queries .super-ralph/workflow.db for real transaction state, ticket progress, and quiescence.
 * 4. Non-Invasive Observation: Ingests telemetry purely for rate tracking, memory profiling, and observability.
 */

import { existsSync } from "node:fs";
import { Database } from "bun:sqlite";

export interface TelemetryVector {
  timestamp: string;
  elapsedSeconds: number;
  tokensIn: number;      // Ingestion mass
  tokensOut: number;     // Generative yield
  tokensContext: number; // Active context horizon
  durationSeconds: number;
  velocityTokPerSec: number;
}

export interface WorkflowDbState {
  dbExists: boolean;
  totalTickets: number;
  completedTickets: number;
  inProgressTickets: number;
  activeConcurrency: number;
  currentIteration: number;
  maxIterations: number;
  isQuiescent: boolean;
  lastStateChange: string | null;
}

export interface NonInvasiveVerdict {
  timestamp: string;
  contextSaturationPct: number;
  generativeEfficiency: number;
  entropyIndex: number;
  velocityTokPerSec: number;
  workflowState: WorkflowDbState | null;
  observabilitySummary: string;
}

export class NonInvasiveTelemetricOracle {
  private contextCeiling: number;
  private history: TelemetryVector[] = [];

  constructor(contextCeiling = 300_000) {
    this.contextCeiling = contextCeiling;
  }

  /**
   * Parse a raw terminal HUD telemetry line.
   */
  parseHudLine(line: string): TelemetryVector | null {
    const raw = line.trim();
    if (!raw) return null;

    const tsMatch = raw.match(/\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]/);
    const deltaMatch = raw.match(/Δ\s*(\d+m)?(\d+s)?/);
    const inMatch = raw.match(/In:\s*([\d.]+)(K|M)?/i);
    const outMatch = raw.match(/Out:\s*([\d.]+)(K|M)?/i);
    const totalMatch = raw.match(/Total:\s*([\d.]+)(K|M)?/i);
    const durationMatch = raw.match(/([\d.]+)s\s*\(/);
    const rateMatch = raw.match(/\(([\d.]+)\/s\)/);

    if (!tsMatch) return null;

    const parseNum = (val: string | undefined, mult: string | undefined): number => {
      if (!val) return 0;
      const num = parseFloat(val);
      if (mult?.toUpperCase() === "K") return num * 1000;
      if (mult?.toUpperCase() === "M") return num * 1000000;
      return num;
    };

    let elapsed = 0;
    if (deltaMatch) {
      const m = deltaMatch[1] ? parseInt(deltaMatch[1]) : 0;
      const s = deltaMatch[2] ? parseInt(deltaMatch[2]) : 0;
      elapsed = m * 60 + s;
    }

    const vector: TelemetryVector = {
      timestamp: tsMatch[1],
      elapsedSeconds: elapsed,
      tokensIn: parseNum(inMatch?.[1], inMatch?.[2]),
      tokensOut: parseNum(outMatch?.[1], outMatch?.[2]),
      tokensContext: parseNum(totalMatch?.[1], totalMatch?.[2]),
      durationSeconds: durationMatch ? parseFloat(durationMatch[1]) : 0,
      velocityTokPerSec: rateMatch ? parseFloat(rateMatch[1]) : 0,
    };

    this.history.push(vector);
    if (this.history.length > 50) this.history.shift();
    return vector;
  }

  /**
   * Non-invasively inspects .super-ralph/workflow.db SQLite state.
   */
  inspectWorkflowDb(dbPath: string): WorkflowDbState {
    if (!existsSync(dbPath)) {
      return {
        dbExists: false,
        totalTickets: 0,
        completedTickets: 0,
        inProgressTickets: 0,
        activeConcurrency: 0,
        currentIteration: 0,
        maxIterations: 25,
        isQuiescent: false,
        lastStateChange: null,
      };
    }

    try {
      const db = new Database(dbPath, { readonly: true });
      
      // Query runs table / node outputs if present in Smithers schema
      const tables = db.query("SELECT name FROM sqlite_master WHERE type='table'").all() as Array<{ name: string }>;
      const tableNames = new Set(tables.map(t => t.name));

      let total = 0;
      let completed = 0;
      let inProgress = 0;
      let iteration = 0;
      let quiescent = false;

      if (tableNames.has("nodes")) {
        const nodeStats = db.query("SELECT status, count(*) as count FROM nodes GROUP BY status").all() as Array<{ status: string; count: number }>;
        for (const row of nodeStats) {
          if (row.status === "completed") completed += row.count;
          if (row.status === "running" || row.status === "in_progress") inProgress += row.count;
          total += row.count;
        }
      }

      if (tableNames.has("runs")) {
        const runRow = db.query("SELECT status, iteration FROM runs ORDER BY created_at DESC LIMIT 1").get() as { status?: string; iteration?: number } | null;
        if (runRow) {
          iteration = runRow.iteration ?? 0;
          quiescent = runRow.status === "completed";
        }
      }

      db.close();

      return {
        dbExists: true,
        totalTickets: total,
        completedTickets: completed,
        inProgressTickets: inProgress,
        activeConcurrency: inProgress,
        currentIteration: iteration,
        maxIterations: 25,
        isQuiescent: quiescent,
        lastStateChange: new Date().toISOString(),
      };
    } catch {
      return {
        dbExists: true,
        totalTickets: 0,
        completedTickets: 0,
        inProgressTickets: 0,
        activeConcurrency: 0,
        currentIteration: 0,
        maxIterations: 25,
        isQuiescent: false,
        lastStateChange: null,
      };
    }
  }

  /**
   * Produces a non-invasive diagnostic grounding verdict.
   */
  evaluate(vector: TelemetryVector, dbPath?: string): NonInvasiveVerdict {
    const etaGen = vector.tokensIn > 0 ? vector.tokensOut / vector.tokensIn : 1.0;
    const saturation = (vector.tokensContext / this.contextCeiling) * 100;
    const dbState = dbPath ? this.inspectWorkflowDb(dbPath) : null;

    const summary = [
      `[Telemetry EKG] Context Saturation: ${saturation.toFixed(1)}% (${(vector.tokensContext / 1000).toFixed(0)}K / ${(this.contextCeiling / 1000).toFixed(0)}K)`,
      `Yield Ratio: ${(etaGen * 100).toFixed(1)}% | Velocity: ${vector.velocityTokPerSec.toFixed(1)} tok/s`,
      dbState?.dbExists
        ? `Database Grounding: ${dbState.completedTickets}/${dbState.totalTickets} nodes settled | Concurrency: ${dbState.activeConcurrency} in-flight | Iteration: ${dbState.currentIteration}/${dbState.maxIterations}`
        : "Database Grounding: workflow.db awaiting initial transaction",
    ].join(" · ");

    return {
      timestamp: vector.timestamp,
      contextSaturationPct: Number(saturation.toFixed(2)),
      generativeEfficiency: Number(etaGen.toFixed(4)),
      entropyIndex: Number((saturation * (1 - etaGen)).toFixed(2)),
      velocityTokPerSec: vector.velocityTokPerSec,
      workflowState: dbState,
      observabilitySummary: summary,
    };
  }
}

// CLI test harness
if (import.meta.main) {
  const oracle = new NonInvasiveTelemetricOracle(300_000);
  const sampleHud = "[2026-09-22 07:43:59] Δ 1m33s | In: 2.9K | Out: 1.1K | Total: 268K | 5.9s (115.0/s)";
  console.log("== Non-Invasive Database & Telemetry Grounding Test ==");
  const parsed = oracle.parseHudLine(sampleHud);
  if (parsed) {
    const verdict = oracle.evaluate(parsed, "/home/toxic/sovereign/projects/range/ranch/corral/.super-ralph/workflow.db");
    console.log(verdict.observabilitySummary);
    console.log("Full Grounding Verdict:", JSON.stringify(verdict, null, 2));
  }
}
