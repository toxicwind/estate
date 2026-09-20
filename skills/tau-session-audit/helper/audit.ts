#!/usr/bin/env bun
// tau-session-audit — maximal integrated: audit + ML + intent + completion + plan
// Usage: bun run helper/audit.ts [--check all|intent|completed|plan|anomalies|unknown-types|near-empty|compaction|credential-pin|ttsr-injection|branch-summary|session-init|mode-change|service-tier-change|empty|cluster|anomaly|model|cwd|completion-rate] [--verbose]

import { readdirSync, readFileSync, existsSync } from "fs";
import { join, basename, dirname } from "path";

const SESSIONS_DIR = join(process.env.HOME || "/home/toxic", ".tau", "agent", "sessions");

interface Session {
  file: string;
  events: number;
  types: Map<string, number>;
  title: string;
  model: string;
  cwd: string;
  intent: string;
  completed: boolean;
  anomalyScore: number;
}

function extractTitle(events: any[]): string {
  for (const e of events) {
    if (e.type === "session" && e.title) return e.title;
  }
  return "";
}

function extractModel(events: any[]): string {
  for (const e of events) {
    if (e.type === "model_change" && e.model) return e.model;
  }
  return "";
}

function extractCwd(events: any[]): string {
  for (const e of events) {
    if (e.type === "session" && e.cwd) return e.cwd;
  }
  return "";
}

function inferIntent(title: string, model: string, cwd: string): string {
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

function inferCompleted(types: Map<string, number>, events: number): boolean {
  if ((types.get("session_init") || 0) > 0 && events > 20) return true;
  if ((types.get("compaction") || 0) > 0) return true;
  if ((types.get("title_change") || 0) > 0) return true;
  if ((types.get("mode_change") || 0) > 0 && events > 10) return true;
  if ((types.get("service_tier_change") || 0) > 0 && events > 20) return true;
  if (events < 5) return false;
  if (events > 200) return true;
  return false;
}

function computeAnomalyScore(s: Session): number {
  let score = 0;
  score += (s.types.get("?") || 0) * 10;
  if (s.events < 5) score += 5;
  score += (s.types.get("credential_pin") || 0) * 3;
  score += (s.types.get("ttsr_injection") || 0) * 3;
  score += (s.types.get("branch_summary") || 0) * 2;
  if (s.events > 500 && (s.types.get("mode_change") || 0) > 50) score += 5;
  return score;
}

function loadSessions(): Session[] {
  const sessions: Session[] = [];
  function walk(dir: string) {
    if (!existsSync(dir)) return;
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) { walk(full); continue; }
      if (!entry.name.endsWith(".jsonl")) continue;
      const content = readFileSync(full, "utf-8");
      const lines = content.split("\n").filter((l: string) => l.trim());
      const events: any[] = [];
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
      const completed = inferCompleted(types, events);
      const anomalyScore = computeAnomalyScore({ events, types, file: full, intent, completed, model, cwd, title, sessionId: "" });
      sessions.push({ file: full.replace(SESSIONS_DIR, "").replace(/^\//, ""), events: events.length, types, title, model, cwd, intent, completed, anomalyScore });
    }
  }
  walk(SESSIONS_DIR);
  return sessions.sort((a, b) => b.events - a.events);
}

function fmt(n: number): string { return n.toLocaleString(); }

// K-means clustering
function clusterSessions(sessions: Session[], k: number = 3): Map<number, Session[]> {
  const features = sessions.map((s) => s.events);
  const min = Math.min(...features);
  const range = Math.max(...features) - min || 1;
  const centroids: number[] = [];
  for (let i = 0; i < k; i++) centroids.push(min + (range * i) / (k - 1));
  let clusters: Map<number, Session[]> = new Map();
  for (let iter = 0; iter < 20; iter++) {
    clusters = new Map();
    for (let i = 0; i < k; i++) clusters.set(i, []);
    for (const s of sessions) {
      let nearest = 0, minDist = Math.abs(s.events - centroids[0]);
      for (let c = 1; c < k; c++) { const d = Math.abs(s.events - centroids[c]); if (d < minDist) { minDist = d; nearest = c; } }
      clusters.get(nearest)!.push(s);
    }
    for (let c = 0; c < k; c++) { const cl = clusters.get(c)!; if (cl.length > 0) centroids[c] = cl.reduce((sum: number, s: Session) => sum + s.events, 0) / cl.length; }
  }
  return clusters;
}

function main() {
  const args = process.argv.slice(2);
  const checks = new Set<string>();
  let verbose = false;
  for (const arg of args) {
    if (arg === "--verbose" || arg === "-v") verbose = true;
    else if (arg.startsWith("--check=")) checks.add(arg.slice(8));
    else if (arg === "--check" || arg === "-c") { const idx = args.indexOf(arg); if (idx + 1 < args.length) checks.add(args[idx + 1]); }
    else if (arg === "--all" || arg === "-a") checks.add("all");
  }
  if (checks.size === 0) checks.add("all");
  const runAll = checks.has("all");
  const run = (name: string) => runAll || checks.has(name);

  const sessions = loadSessions();

  // Global type distribution
  const allTypes = new Map<string, number>();
  for (const s of sessions) for (const [t, c] of s.types) allTypes.set(t, (allTypes.get(t) || 0) + c);

  // Anomaly counts
  const anomalyCounts = new Map<string, number>();
  for (const s of sessions) for (const a of s.anomalies || []) anomalyCounts.set(a, (anomalyCounts.get(a) || 0) + 1);

  // Intent counts
  const intentCounts = new Map<string, number>();
  for (const s of sessions) intentCounts.set(s.intent, (intentCounts.get(s.intent) || 0) + 1);

  const completedCount = sessions.filter((s) => s.completed).length;
  const incompleteCount = sessions.filter((s) => !s.completed).length;
  let hasCritical = false;

  console.log("=".repeat(80));
  console.log("TAU SESSION AUDIT — MAXIMAL INTEGRATED");
  console.log("=".repeat(80));
  console.log();
  // DATAFRAME OUTPUT — TSV for LLM consumption
  console.log("file\tevents\ttitle\tmodel\tcwd\tintent\tcompleted\tanomalyScore\tsession_init\tmode_change\tservice_tier_change\tcompaction\tcredential_pin\tttsr_injection\tbranch_summary\tmessage\tcustom\tcustom_message\tthinking_level_change\ttitle_change\tunknown_types");
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
      s.types.get("session_init") || 0,
      s.types.get("mode_change") || 0,
      s.types.get("service_tier_change") || 0,
      s.types.get("compaction") || 0,
      s.types.get("credential_pin") || 0,
      s.types.get("ttsr_injection") || 0,
      s.types.get("branch_summary") || 0,
      s.types.get("message") || 0,
      s.types.get("custom") || 0,
      s.types.get("custom_message") || 0,
      s.types.get("thinking_level_change") || 0,
      s.types.get("title_change") || 0,
      s.types.get("?") || 0,
    ].join("\t");
    console.log(line);
  }
  console.log();

  // SUMMARY STATS
  console.log("SUMMARY:");
  console.log(`total_files: ${fmt(sessions.length)}`);
  console.log(`total_events: ${fmt(sessions.reduce((sum: number, s: Session) => sum + s.events, 0))}`);
  console.log(`completed: ${completedCount}`);
  console.log(`incomplete: ${incompleteCount}`);
  console.log(`avg_events: ${(sessions.reduce((sum: number, s: Session) => sum + s.events, 0) / sessions.length).toFixed(1)}`);
  console.log(`max_events: ${sessions[0].events}`);
  console.log(`min_events: ${sessions[sessions.length - 1].events}`);
  console.log();

  // INTENT BREAKDOWN
  if (run("intent") || run("all")) {
    console.log("INTENT BREAKDOWN:");
    for (const [intent, count] of [...intentCounts.entries()].sort((a, b) => b[1] - a[1])) {
      console.log(`  ${intent}: ${fmt(count)}`);
    }
    console.log();
  }

  // COMPLETION RATE
  if (run("completion-rate") || run("all")) {
    console.log("COMPLETION RATE BY INTENT:");
    const stats = new Map<string, { total: number; completed: number }>();
    for (const s of sessions) {
      const st = stats.get(s.intent) || { total: 0, completed: 0 };
      st.total++; if (s.completed) st.completed++;
      stats.set(s.intent, st);
    }
    for (const [intent, st] of [...stats.entries()].sort((a, b) => {
      const rA = a[1].completed / a[1].total; const rB = b[1].completed / b[1].total; return rB - rA;
    })) {
      console.log(`  ${intent}: ${st.completed}/${st.total} (${((st.completed / st.total) * 100).toFixed(1)}%)`);
    }
    console.log();
  }

  // CLUSTERING
  if (run("cluster") || run("all")) {
    console.log("K-MEANS CLUSTERING (k=3):");
    const clusters = clusterSessions(sessions, 3);
    for (const [cid, cluster] of clusters) {
      const avg = cluster.reduce((sum: number, s: Session) => sum + s.events, 0) / cluster.length;
      console.log(`  Cluster ${cid}: ${cluster.length} sessions, avg ${fmt(Math.round(avg))} events`);
      const intents = new Map<string, number>();
      for (const s of cluster) intents.set(s.intent, (intents.get(s.intent) || 0) + 1);
      for (const [intent, count] of [...intents.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3)) {
        console.log(`    - ${intent}: ${count}`);
      }
    }
    console.log();
  }

  // MODEL DISTRIBUTION
  if (run("model") || run("all")) {
    console.log("MODEL DISTRIBUTION:");
    const models = new Map<string, number>();
    for (const s of sessions) { if (s.model) models.set(s.model, (models.get(s.model) || 0) + 1); }
    for (const [model, count] of [...models.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)) {
      console.log(`  ${model}: ${count}`);
    }
    console.log();
  }

  // CWD ANALYSIS
  if (run("cwd") || run("all")) {
    console.log("WORKING DIRECTORY ANALYSIS:");
    const cwds = new Map<string, number>();
    for (const s of sessions) { if (s.cwd) cwds.set(s.cwd, (cwds.get(s.cwd) || 0) + 1); }
    for (const [cwd, count] of [...cwds.entries()].sort((a, b) => b[1] - a[1])) {
      console.log(`  ${cwd}: ${count} sessions`);
    }
    console.log();
  }

  // ANOMALY DETECTION
  if (run("anomaly") || run("all")) {
    console.log("ANOMALY DETECTION (top 10):");
    for (const s of [...sessions].sort((a, b) => b.anomalyScore - a.anomalyScore).slice(0, 10)) {
      console.log(`  score=${s.anomalyScore.toFixed(1)}  ${s.file} — ${s.intent}`);
    }
    console.log();
  }

  // PLAN GENERATION
  if (run("plan") || run("all")) {
    console.log("PLAN — NEXT STEPS:");
    const incomplete = sessions.filter((s) => !s.completed);
    if (incomplete.length > 0) {
      console.log(`  1. Review ${incomplete.length} incomplete session(s):`);
      for (const s of incomplete.slice(0, 5)) console.log(`     - ${s.file} (${s.intent})`);
    }
    const unknownTypeSessions = sessions.filter((s) => (s.types.get("?") || 0) > 0);
    if (unknownTypeSessions.length > 0) {
      console.log(`  2. Fix ${unknownTypeSessions.length} session(s) with unknown event types:`);
      for (const s of unknownTypeSessions) console.log(`     - ${s.file}`);
      hasCritical = true;
    }
    const largeIncomplete = incomplete.filter((s) => s.events > 100);
    if (largeIncomplete.length > 0) {
      console.log(`  3. Investigate ${largeIncomplete.length} large incomplete session(s):`);
      for (const s of largeIncomplete) console.log(`     - ${s.file} (${fmt(s.events)} events, ${s.intent})`);
    }
    const credSessions = sessions.filter((s) => (s.types.get("credential_pin") || 0) > 0);
    if (credSessions.length > 0) {
      console.log(`  4. Verify ${credSessions.length} session(s) with credential_pin events:`);
      for (const s of credSessions.slice(0, 3)) console.log(`     - ${s.file}`);
    }
    console.log();
  }

  // ANOMALY SUMMARY
  if (run("anomalies") || run("all")) {
    console.log("ANOMALY SUMMARY:");
    for (const [a, c] of [...anomalyCounts.entries()].sort((a, b) => b[1] - a[1])) console.log(`  ${a}: ${fmt(c)} sessions`);
    console.log();
  }

  // SESSIONS WITH ANOMALIES
  if (run("anomalies") || run("all")) {
    console.log("SESSIONS WITH ANOMALIES:");
    for (const s of sessions) {
      if (s.anomalies && s.anomalies.length > 0) console.log(`  ${s.file}: [${s.anomalies.join(", ")}] (${fmt(s.events)} events)`);
    }
    console.log();
  }

  // UNKNOWN TYPES
  if (run("unknown-types") || runAll) {
    console.log("UNKNOWN EVENT TYPES (CRITICAL):");
    for (const s of sessions) {
      if ((s.types.get("?") || 0) > 0) { console.log(`  ${s.file}: ${s.types.get("?")} unknown event(s)`); hasCritical = true; }
    }
    console.log();
  }

  // NEAR-EMPTY
  if (run("near-empty") || runCheck("empty") || runAll) {
    console.log("NEAR-EMPTY SESSIONS (≤4 events):");
    for (const s of sessions) { if (s.events <= 4) console.log(`  ${s.file}: ${fmt(s.events)} events`); }
    console.log();
  }

  // TOP 10 LARGEST
  if (run("anomalies") || run("all")) {
    console.log("TOP 10 LARGEST SESSIONS:");
    for (const s of sessions.slice(0, 10)) console.log(`  ${fmt(s.events).padStart(6)} events  ${s.file} — ${s.intent}`);
    console.log();
  }

  console.log("=".repeat(80));
  console.log(`Audit complete: ${fmt(sessions.length)} files, ${fmt(sessions.reduce((sum: number, s: Session) => sum + s.events, 0))} events`);
  if (hasCritical) console.log("⚠ CRITICAL: Unknown event types found");
  process.exit(hasCritical ? 1 : 0);
}

main();
