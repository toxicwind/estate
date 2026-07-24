#!/usr/bin/env bun
/**
 * Deep Semantic Log Analysis - Using verified danfojs API
 */

import * as dfd from "danfojs-node";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const LOG_PATH = "/home/toxic/sovereign/2026-07-22T00:07:28-06:00.log";
const OUT_DIR = "/home/toxic/sovereign/audit-output/deep";

interface LogEntry {
  timestamp: string;
  level: string;
  module: string;
  message: string;
  raw: string;
  repo?: string;
  path?: string;
  errorType?: string;
  severity?: number;
  component?: string;
}

function parseLogLine(line: string): LogEntry | null {
  const match = line.match(
    /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}:\d{2})\s+(INFO|ERROR|WARN)\s+\[([^\]]+)\]\s+(.+)$/,
  );
  if (!match) return null;
  return {
    timestamp: match[1],
    level: match[2],
    module: match[3],
    message: match[4],
    raw: line,
  };
}

function enrichEntry(entry: LogEntry): LogEntry {
  const repoMatch = entry.message.match(/\/repos\/([^/]+)\//);
  if (repoMatch) entry.repo = repoMatch[1];

  const pathMatch = entry.message.match(/"([^"]+)"/);
  if (pathMatch) entry.path = pathMatch[1];

  if (entry.level === "ERROR" || entry.level === "WARN") {
    if (
      entry.message.includes("symlink") ||
      entry.message.includes("canonicalizing")
    ) {
      entry.errorType = "filesystem_symlink";
      entry.severity = 3;
    } else if (entry.message.includes("git")) {
      entry.errorType = "git_repository";
      entry.severity = 2;
    } else if (
      entry.message.includes("Missing") ||
      entry.message.includes("type field")
    ) {
      entry.errorType = "task_format";
      entry.severity = 2;
    } else if (entry.message.includes("memory")) {
      entry.errorType = "memory_pressure";
      entry.severity = 4;
    } else {
      entry.errorType = "other";
      entry.severity = 1;
    }
  }

  const moduleParts = entry.module.split("::");
  entry.component = moduleParts[0];
  return entry;
}

function main() {
  console.log("Deep Semantic Log Analysis");
  console.log("=".repeat(50));

  const logContent = readFileSync(LOG_PATH, "utf-8");
  const lines = logContent.trim().split("\n");
  console.log(`Loaded ${lines.length} lines`);

  const entries: LogEntry[] = [];
  for (const line of lines) {
    const parsed = parseLogLine(line);
    if (parsed) entries.push(enrichEntry(parsed));
  }
  console.log(`Parsed ${entries.length} entries`);

  const df = new dfd.DataFrame(entries);
  console.log(`DataFrame shape: [${df.shape[0]}, ${df.shape[1]}]`);

  mkdirSync(OUT_DIR, { recursive: true });

  // 1. TEMPORAL ANALYSIS
  console.log("\n--- Temporal Analysis ---");
  const timestamps = df["timestamp"].apply((x: string) =>
    new Date(x).getTime(),
  );
  df["timestamp_parsed"] = timestamps;

  const timeRange = {
    start: timestamps.min(),
    end: timestamps.max(),
    durationMs: timestamps.max() - timestamps.min(),
  };
  console.log(
    `  Time range: ${new Date(timeRange.start).toISOString()} to ${new Date(timeRange.end).toISOString()}`,
  );
  console.log(`  Duration: ${(timeRange.durationMs / 1000).toFixed(1)}s`);

  const eps = df.shape[0] / (timeRange.durationMs / 1000);
  console.log(`  Event rate: ${eps.toFixed(1)} events/sec`);

  // Time buckets (1 second)
  const timeBuckets = timestamps.apply(
    (x: number) => Math.floor(x / 1000) * 1000,
  );
  df["time_bucket"] = timeBuckets;
  const bucketCounts = df.groupby(["time_bucket"]).size();
  const peakSecond = bucketCounts
    .sortValues("count", { ascending: false })
    .head(1);
  console.log(`  Peak second: ${peakSecond.values[0][1]} events`);

  // 2. MODULE/COMPONENT
  console.log("\n--- Module/Component Analysis ---");
  const modStats = df.groupby(["module"]).agg({ level: "count" });
  console.log(modStats.toString());

  const compStats = df.groupby(["component"]).agg({ level: "count" });
  console.log("\nBy Component:");
  console.log(compStats.toString());

  // 3. REPOSITORY HEATMAP
  console.log("\n--- Repository Error Heatmap ---");
  const errors = df.query("level == 'ERROR' or level == 'WARN'");
  if (errors.shape[0] > 0) {
    const repoErrors = errors.groupby(["repo", "errorType"]).size();
    const sortedRepoErrors = repoErrors.sortValues("count", {
      ascending: false,
    });
    console.log(sortedRepoErrors.head(20).toString());

    // Multi-error-type repos
    const repoErrorTypes = errors
      .groupby(["repo"])
      .nunique({ columns: ["errorType"] });
    const multiTypeRepos = repoErrorTypes.query("errorType > 1");
    if (multiTypeRepos.shape[0] > 0) {
      console.log("\nRepos with multiple error types:");
      console.log(multiTypeRepos.toString());
    }
  }

  // 4. ERROR CASCADING
  console.log("\n--- Error Cascading Patterns ---");
  errors["time_bucket_5s"] = errors["timestamp_parsed"].apply(
    (x: number) => Math.floor(x / 5000) * 5000,
  );
  const cascades = errors
    .groupby(["repo", "time_bucket_5s", "errorType"])
    .size();
  const burstPatterns = cascades
    .query("count > 10")
    .sortValues("count", { ascending: false });
  if (burstPatterns.shape[0] > 0) {
    console.log("Burst patterns (>10 errors/5sec):");
    console.log(burstPatterns.head(10).toString());
  }

  // 5. MEMORY PRESSURE
  console.log("\n--- Memory Pressure Correlation ---");
  const memEvents = df.query("module == 'zed::reliability'");
  if (memEvents.shape[0] > 0) {
    console.log(memEvents[["timestamp", "message"]].toString());
    const memTimes = memEvents["timestamp_parsed"].values as number[];
    for (const mt of memTimes) {
      const nearby = errors.query(
        `timestamp_parsed > ${mt - 5000} and timestamp_parsed < ${mt + 5000}`,
      );
      if (nearby.shape[0] > 0) {
        console.log(
          `  Memory event at ${new Date(mt).toISOString()} -> ${nearby.shape[0]} errors in +/-5s`,
        );
        const byType = nearby
          .groupby(["errorType"])
          .size()
          .sortValues("count", { ascending: false });
        console.log(byType.toString());
      }
    }
  }

  // 6. GIT REPOSITORY SCAN
  console.log("\n--- Git Repository Scan Analysis ---");
  const gitEvents = df.query("module == 'git::repository'");
  console.log(`  Total repos scanned: ${gitEvents.shape[0]}`);
  const gitErrors = df.query(
    "module == 'git::repository' and (level == 'ERROR' or level == 'WARN')",
  );
  console.log(`  Git errors: ${gitErrors.shape[0]}`);

  const repoNames = gitEvents["message"].apply((msg: string) => {
    const m = msg.match(/\/repos\/([^/]+)\//);
    return m ? m[1] : "unknown";
  });
  const uniqueRepos = [...new Set(repoNames.values)];
  console.log(`  Unique repos: ${uniqueRepos.length}`);

  const categories: Record<string, number> = {
    dotfiles: 0,
    zed: 0,
    ide: 0,
    other: 0,
  };
  for (const r of uniqueRepos) {
    if (
      r.includes("dotfile") ||
      r.includes("dotfiles") ||
      r.includes("hyde") ||
      r.includes("hypr") ||
      r.includes("cachy") ||
      r.includes("omarchy")
    )
      categories.dotfiles++;
    else if (r.includes("zed") || r.includes("Zed")) categories.zed++;
    else if (
      r.includes("ide") ||
      r.includes("fang") ||
      r.includes("lapce") ||
      r.includes("void")
    )
      categories.ide++;
    else categories.other++;
  }
  console.log("  Categories:", categories);

  // 7. ANOMALY DETECTION
  console.log("\n--- Anomaly Detection ---");
  const moduleCounts = df["module"].valueCounts();
  const rareModules = moduleCounts.query("count < 5");
  console.log(`  Rare modules (<5 occurrences): ${rareModules.shape[0]}`);
  console.log(rareModules.toString());

  const errorTimeSeries = errors
    .groupby(["time_bucket"])
    .size()
    .sortValues("count", { ascending: false });
  const meanErrors = errorTimeSeries["count"].mean();
  const stdErrors = errorTimeSeries["count"].std();
  const spikes = errorTimeSeries.query(`count > ${meanErrors + 3 * stdErrors}`);
  if (spikes.shape[0] > 0) {
    console.log("  Statistical spikes (3 sigma):");
    console.log(spikes.toString());
  }

  // 8. PREDICTIVE INSIGHTS
  console.log("\n--- Predictive Insights ---");
  const repoErrorCounts = errors
    .groupby(["repo"])
    .size()
    .sortValues("count", { ascending: false });
  console.log("  Top at-risk repos:");
  console.log(repoErrorCounts.head(10).toString());

  const errorTypeTime = errors
    .groupby(["time_bucket", "errorType"])
    .size()
    .unstack({ fillValue: 0 });
  if (errorTypeTime.shape[1] > 1) {
    console.log("  Error type trends (last 5 buckets):");
    console.log(errorTypeTime.tail(5).toString());
  }

  // SAVE
  console.log("\n--- Saving ---");
  writeFileSync(
    join(OUT_DIR, "enriched_entries.json"),
    JSON.stringify(entries, null, 2),
  );

  const report = `# Deep Semantic Log Analysis Report

**Log:** \`2026-07-22T00:07:28-06:00.log\` (1000 lines)
**Analysis Time:** ${new Date().toISOString()}

---

## Temporal Profile
- **Duration:** ${(timeRange.durationMs / 1000).toFixed(1)}s
- **Event Rate:** ${eps.toFixed(1)} events/sec
- **Peak Second:** ${peakSecond.values[0][1]} events

---

## Component Activity
${compStats.toString()}

---

## Repository Error Heatmap
${errors.shape[0] > 0 ? sortedRepoErrors.head(20).toString() : "No errors"}

---

## Multi-Error-Type Repos
${multiTypeRepos && multiTypeRepos.shape[0] > 0 ? multiTypeRepos.toString() : "None detected"}

---

## Memory Pressure Correlation
${memEvents.shape[0] > 0 ? `Memory events: ${memEvents.shape[0]}\n${memEvents[["timestamp", "message"]].toString()}` : "None"}

---

## Git Scan Profile
- **Total repos:** ${gitEvents.shape[0]}
- **Unique repos:** ${uniqueRepos.length}
- **Categories:** ${JSON.stringify(categories)}

---

## Anomalies
- **Rare modules:** ${rareModules.shape[0]}
- **Statistical spikes:** ${spikes.shape[0]}

---

## Risk Forecast
**Top 10 at-risk repos:**
${repoErrorCounts.head(10).toString()}
`;

  writeFileSync(join(OUT_DIR, "deep-analysis-report.md"), report);
  console.log(`Report: ${OUT_DIR}/deep-analysis-report.md`);
  console.log(`Data: ${OUT_DIR}/enriched_entries.json`);

  console.log("\nDeep analysis complete!");
}

main().catch(console.error);
