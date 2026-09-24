#!/usr/bin/env bun
// tau-session-audit — maximal integrated: audit + ML + patterns + report
// Usage: bun run helper/audit.ts [--report] [--check all|intent|completed|plan|patterns|todo-phantom|anomalies|unknown-types|near-empty|model|cwd] [--verbose]

import { readdirSync, readFileSync, existsSync, writeFileSync } from "fs";
import { join } from "path";
import { runAllPatterns } from "../patterns/index";
import type { PatternMatch, SessionEvent } from "../patterns/types";
import { generateMarkdownReport, type AuditedSession } from "./report";

const SESSIONS_DIR = join(process.env.HOME || "/home/toxic", ".tau", "agent", "sessions");

export interface Session extends AuditedSession {}

function extractTitle(events: SessionEvent[]): string {
  for (const e of events) {
    if (e.type === "session" && typeof e.title === "string") return e.title;
  }
  return "";
}

function extractModel(events: SessionEvent[]): string {
  for (const e of events) {
    if (e.type === "model_change" && typeof e.model === "string") return e.model;
  }
  return "";
}

function extractCwd(events: SessionEvent[]): string {
  for (const e of events) {
    if (e.type === "session" && typeof e.cwd === "string") return e.cwd;
  }
  return "";
}

export function inferIntent(title: string, model: string, cwd: string): string {
  const t = title.toLowerCase();
  const m = model.toLowerCase();
  const c = cwd.toLowerCase();
  if (t.includes("omp") && t.includes("tau")) return "OMP → Tau config migration";
  if (t.includes("groq") || m.includes("groq")) return "Groq provider integration";
  if (t.includes("nvidia") || m.includes("nvidia") || m.includes("nemotron")) return "NVIDIA config / model setup";
  if (t.includes("session") && t.includes("migrat")) return "Session migration (omp → tau)";
  if (t.includes("audit")) return "Audit / verification";
  if (t.includes("bench")) return "Benchmark";
  if (t.includes("subagent") || t.includes("scout")) return "Subagent / scout work";
  if (t.includes("hotfix")) return "Hotfix";
  if (t.includes("router")) return "Router config";
  if (t.includes("profile")) return "Profile synthesis";
  if (t.includes("tau") && (t.includes("cli") || t.includes("verif"))) return "Tau CLI verification";
  if (t.includes("maximal")) return "Maximal dynamic bench";
  if (t.includes("sovereign")) return "Sovereign project work";
  if (t.includes("deepwiki")) return "Deepwiki MCP audit";
  if (t.includes("mesh")) return "Mesh deepwiki plan";
  if (t.includes("har")) return "HAR session verification";
  if (t.includes("rsync")) return "Cache migration (rsync)";
  if (t.includes("retrieve")) return "Retrieve tools usage";
  if (t.includes("tau command")) return "Tau command fix";
  if (t.includes("zed") || t.includes("qed")) return "Zed/Qed application fix";
  if (t.includes("bun helper")) return "Bun helper setup";
  if (t.includes("catalog")) return "Sovereign mutator catalog";
  if (t.includes("matter") || t.includes("bulb")) return "Matter bulb fix";
  if (t.includes("registry") || t.includes("imports")) return "Groq registry imports";
  if (t.includes("agent config")) return "Tau agent config";
  if (t.includes("syntax") || t.includes("file errors")) return "Syntax/file error fix";
  if (t.includes("bashrc")) return "Bashrc aliases setup";
  if (t.includes("db") || t.includes("database")) return "DB setup/confirmation";
  if (t.includes("continue")) return "Continue next task";
  if (c.includes("sovereign")) return "Sovereign project work";
  if (c.includes("tau")) return "Tau project work";
  return "General agent work";
}

export function inferCompleted(types: Map<string, number>, events: number, patterns: PatternMatch[]): boolean {
  // If there are critical phantom todo completions, do not mark completed
  const hasCriticalPhantom = patterns.some((p) => p.patternId === "CONSECUTIVE_TODO_FLURRY" && p.severity === "critical");
  if (hasCriticalPhantom) return false;

  if ((types.get("session_init") || 0) > 0 && events > 20) return true;
  if ((types.get("compaction") || 0) > 0 && events > 50) return true;
  if ((types.get("title_change") || 0) > 0 && events > 30) return true;
  if ((types.get("mode_change") || 0) > 0 && events > 20) return true;
  if (events < 5) return false;
  return false;
}

export function computeAnomalyScore(eventsCount: number, types: Map<string, number>, patterns: PatternMatch[]): number {
  let score = 0;
  score += (types.get("?") || 0) * 10;
  if (eventsCount < 5) score += 5;
  score += (types.get("credential_pin") || 0) * 3;
  score += (types.get("ttsr_injection") || 0) * 3;
  score += (types.get("branch_summary") || 0) * 2;
  for (const p of patterns) {
    if (p.severity === "critical") score += 15;
    else if (p.severity === "high") score += 8;
    else if (p.severity === "medium") score += 3;
  }
  return score;
}

export function loadSessions(): Session[] {
  const sessions: Session[] = [];
  function walk(dir: string) {
    if (!existsSync(dir)) return;
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) { walk(full); continue; }
      if (!entry.name.endsWith(".jsonl")) continue;
      const content = readFileSync(full, "utf-8");
      const lines = content.split("\n").filter((l) => l.trim());
      const events: SessionEvent[] = [];
      for (const line of lines) {
        try { events.push(JSON.parse(line)); } catch { /* skip */ }
      }
      const types = new Map<string, number>();
      for (const e of events) {
        const t = e.type || "?";
        types.set(t, (types.get(t) || 0) + 1);
      }
      const title = extractTitle(events);
      const model = extractModel(events);
      const cwd = extractCwd(events);
      const intent = inferIntent(title, model, cwd);

      const patterns = runAllPatterns(events, { file: full, model, cwd, title });
      let phantomTodoCount = 0;
      for (const p of patterns) {
        if (p.patternId === "CONSECUTIVE_TODO_FLURRY" && typeof p.details.consecutiveCount === "number") {
          phantomTodoCount += p.details.consecutiveCount;
        } else if (p.patternId === "MESSAGE_NO_TOOLS_THEN_TODO_DONE") {
          phantomTodoCount += 1;
        }
      }

      const completed = inferCompleted(types, events.length, patterns);
      const anomalyScore = computeAnomalyScore(events.length, types, patterns);

      sessions.push({
        file: full.replace(SESSIONS_DIR, "").replace(/^\//, ""),
        events: events.length,
        types,
        title,
        model,
        cwd,
        intent,
        completed,
        anomalyScore,
        patterns,
        phantomTodoCount,
      });
    }
  }
  walk(SESSIONS_DIR);
  return sessions.sort((a, b) => b.events - a.events);
}

function fmt(n: number): string { return n.toLocaleString(); }

function main() {
  const args = process.argv.slice(2);
  const checks = new Set<string>();
  let verbose = false;
  let reportMode = false;
  let saveReportPath = "";

  for (const arg of args) {
    if (arg === "--verbose" || arg === "-v") verbose = true;
    else if (arg === "--report" || arg === "-r") reportMode = true;
    else if (arg.startsWith("--out=")) saveReportPath = arg.slice(6);
    else if (arg.startsWith("--check=")) checks.add(arg.slice(8));
    else if (arg === "--check" || arg === "-c") {
      const idx = args.indexOf(arg);
      if (idx + 1 < args.length) checks.add(args[idx + 1]);
    }
    else if (arg === "--all" || arg === "-a") checks.add("all");
  }

  if (checks.size === 0 && !reportMode) {
    checks.add("all");
  }
  const runAll = checks.has("all");
  const run = (name: string) => runAll || checks.has(name);

  const sessions = loadSessions();

  // If reportMode or requested, generate and print/save markdown report
  if (reportMode) {
    const reportMd = generateMarkdownReport(sessions, { verbose });
    if (saveReportPath) {
      writeFileSync(saveReportPath, reportMd, "utf-8");
      console.log(`Report written to ${saveReportPath}`);
    } else {
      console.log(reportMd);
    }
    return;
  }

  const completedCount = sessions.filter((s) => s.completed).length;
  const incompleteCount = sessions.filter((s) => !s.completed).length;
  let hasCritical = false;

  console.log("=".repeat(80));
  console.log("TAU SESSION AUDIT — REPORT FORWARD & PATTERNS INTEGRATED");
  console.log("=".repeat(80));
  console.log();

  // DATAFRAME OUTPUT — TSV
  console.log("file\tevents\ttitle\tmodel\tcwd\tintent\tcompleted\tanomalyScore\tphantom_todos\tpattern_matches\tunknown_types");
  for (const s of sessions) {
    const line = [
      s.file,
      s.events,
      `"${s.title.replace(/"/g, '""')}"`,
      s.model,
      s.cwd,
      s.intent,
      s.completed,
      s.anomalyScore.toFixed(1),
      s.phantomTodoCount,
      s.patterns.length,
      s.types.get("?") || 0,
    ].join("\t");
    console.log(line);
  }
  console.log();

  // SUMMARY STATS
  console.log("SUMMARY:");
  console.log(`total_files: ${fmt(sessions.length)}`);
  console.log(`total_events: ${fmt(sessions.reduce((sum, s) => sum + s.events, 0))}`);
  console.log(`completed: ${completedCount}`);
  console.log(`incomplete: ${incompleteCount}`);
  console.log(`sessions_with_phantom_todos: ${sessions.filter((s) => s.phantomTodoCount > 0).length}`);
  console.log(`total_pattern_detections: ${sessions.reduce((sum, s) => sum + s.patterns.length, 0)}`);
  console.log();

  // PATTERN CHECKS
  if (run("patterns") || run("todo-phantom") || runAll) {
    console.log("FIRST-CLASS PATTERN DETECTIONS:");
    const patternSummary = new Map<string, number>();
    for (const s of sessions) {
      for (const p of s.patterns) {
        patternSummary.set(p.name, (patternSummary.get(p.name) || 0) + 1);
      }
    }
    for (const [pname, count] of patternSummary.entries()) {
      console.log(`  ${pname}: ${count} incident(s)`);
    }
    console.log();

    const topPhantom = sessions.filter((s) => s.phantomTodoCount > 0).slice(0, 10);
    console.log("TOP SESSIONS WITH PHANTOM TODO COMPLETIONS:");
    for (const s of topPhantom) {
      console.log(`  ${s.file} (${s.model}): ${s.phantomTodoCount} phantom todos [Intent: ${s.intent}]`);
    }
    console.log();
  }

  // UNKNOWN TYPES
  if (run("unknown-types") || runAll) {
    console.log("UNKNOWN EVENT TYPES (CRITICAL):");
    for (const s of sessions) {
      if ((s.types.get("?") || 0) > 0) {
        console.log(`  ${s.file}: ${s.types.get("?")} unknown event(s)`);
        hasCritical = true;
      }
    }
    console.log();
  }

  console.log("=".repeat(80));
  console.log(`Audit complete: ${fmt(sessions.length)} files analyzed. Use --report for GitHub Markdown report.`);
  if (hasCritical) console.log("⚠ CRITICAL: Unknown event types found");
  process.exit(hasCritical ? 1 : 0);
}

main();
