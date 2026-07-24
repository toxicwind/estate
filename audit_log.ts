c#!/usr/bin/env bun
/**
 * Sovereign Log Audit Script
 * Uses Danfo.js to parse 1000-line Zed log and produce structured audit report.
 * Outputs: audit-output/audit-report.md, audit-data.json, audit-fixes.json
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import * as dfd from "danfojs-node";
import { join } from "node:path";

const LOG_PATH = "/home/toxic/sovereign/2026-07-22T00:07:28-06:00.log";
const OUT_DIR = "/home/toxic/sovereign/audit-output";

interface LogEntry {
  timestamp: string;
  level: string;
  module: string;
  message: string;
  raw: string;
}

interface ParsedError {
  path: string;
  errorType: string;
  repo: string;
  category: string;
  count: number;
}

function parseLogLine(line: string): LogEntry | null {
  const match = line.match(
    /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}:\d{2})\s+(INFO|ERROR|WARN)\s+\[([^\]]+)\]\s+(.+)$/
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

function extractSymlinkError(msg: string): { path: string; error: string; repo: string } | null {
  const symlinkMatch = msg.match(
    /error reading target of symlink "([^"]+)": canonicalizing "([^"]+)": ([^(]+)\(os error (\d+)\)/
  );
  if (symlinkMatch) {
    const path = symlinkMatch[1];
    const error = symlinkMatch[3].trim();
    const repoMatch = path.match(/\/repos\/([^/]+)\//);
    const repo = repoMatch ? repoMatch[1] : "unknown";
    return { path, error, repo };
  }
  const warnMatch = msg.match(
    /Failed to read symlink target metadata for path "([^"]+)": ([^(]+)\(os error (\d+)\)/
  );
  if (warnMatch) {
    const path = warnMatch[1];
    const error = warnMatch[2].trim();
    const repoMatch = path.match(/\/repos\/([^/]+)\//);
    const repo = repoMatch ? repoMatch[1] : "unknown";
    return { path, error, repo };
  }
  return null;
}

function categorizeError(error: string): string {
  if (error.includes("No such file or directory")) return "broken_symlink";
  if (error.includes("Too many levels of symbolic links")) return "symlink_loop";
  return "other";
}

function main() {
  console.log("📊 Loading log file...");
  const logContent = readFileSync(LOG_PATH, "utf-8");
  const lines = logContent.trim().split("\n");
  console.log(`   Total lines: ${lines.length}`);

  const entries: LogEntry[] = [];
  const errorMap = new Map<string, ParsedError>();

  for (const line of lines) {
    const parsed = parseLogLine(line);
    if (!parsed) continue;
    entries.push(parsed);

    if (parsed.level === "ERROR" || parsed.level === "WARN") {
      const extracted = extractSymlinkError(parsed.message);
      if (extracted) {
        const category = categorizeError(extracted.error);
        const key = `${extracted.repo}|${category}|${extracted.error}`;
        if (errorMap.has(key)) {
          errorMap.get(key)!.count++;
        } else {
          errorMap.set(key, {
            path: extracted.path,
            errorType: extracted.error,
            repo: extracted.repo,
            category,
            count: 1,
          });
        }
      }
    }
  }

  const errors = Array.from(errorMap.values());

  // Create DataFrames
  const dfEntries = new dfd.DataFrame(entries);
  const dfErrors = new dfd.DataFrame(errors);

  // --- FIXED: use dfd.toJSON with format: 'row' instead of .toJSON() ---
  const levelCountsArr = dfd.toJSON(dfEntries["level"].valueCounts(), { format: "row" });
  const moduleCountsArr = dfd.toJSON(dfEntries["module"].valueCounts(), { format: "row" });
  const repoCountsArr = dfd.toJSON(dfErrors["repo"].valueCounts(), { format: "row" });
  const categoryCountsArr = dfd.toJSON(dfErrors["category"].valueCounts(), { format: "row" });

  // Convert row arrays to objects for easy lookup
  const levelCounts = Object.fromEntries(levelCountsArr.map(([key, val]) => [key, val]));
  const moduleCounts = Object.fromEntries(moduleCountsArr.map(([key, val]) => [key, val]));
  const repoCounts = Object.fromEntries(repoCountsArr.map(([key, val]) => [key, val]));
  const categoryCounts = Object.fromEntries(categoryCountsArr.map(([key, val]) => [key, val]));

  // Top repos by error count
  const topRepos = dfErrors
    .groupby(["repo"])
    .agg({ count: "sum" })
    .sortValues("count", { ascending: false })
    .head(10);

  // Top error categories
  const topCategories = dfErrors
    .groupby(["category"])
    .agg({ count: "sum" })
    .sortValues("count", { ascending: false });

  // Generate report
  const report = `# Sovereign Log Audit Report

**Log File:** \`2026-07-22T00:07:28-06:00.log\` (1000 lines)
**Generated:** ${new Date().toISOString()}

---

## 📈 Summary Statistics

| Metric | Value |
|--------|-------|
| Total Log Lines | ${lines.length} |
| Parsed Entries | ${entries.length} |
| ERROR Level | ${levelCounts.ERROR || 0} |
| WARN Level | ${levelCounts.WARN || 0} |
| INFO Level | ${levelCounts.INFO || 0} |
| Unique Error Patterns | ${errors.length} |
| Total Error Occurrences | ${errors.reduce((a, b) => a + b.count, 0)} |

---

## 📊 By Module
${Object.entries(moduleCounts)
  .sort((a, b) => b[1] - a[1])
  .map(([mod, cnt]) => `| \`${mod}\` | ${cnt} |`)
  .join("\n")}

---

## 🔴 Top 10 Problematic Repositories
| Repository | Error Count |
|------------|-------------|
${topRepos.values.map((row: any) => `| ${row[0]} | ${row[1]} |`).join("\n")}

---

## 🏷️ Error Categories
| Category | Count |
|----------|-------|
${topCategories.values.map((row: any) => `| ${row[0]} | ${row[1]} |`).join("\n")}

---

## 📋 Detailed Error Breakdown
${errors
  .sort((a, b) => b.count - a.count)
  .map(
    (e) =>
      `### ${e.repo} (${e.category})
- **Error:** \`${e.errorType}\`
- **Occurrences:** ${e.count}
- **Example Path:** \`${e.path}\``
  )
  .join("\n\n")}

---

## 🎯 Fix Plan for Subagents

### Subagent A: Symlink Cleanup (Broken Symlinks)
**Scope:** All \`broken_symlink\` errors (${errors.filter(e => e.category === "broken_symlink").length} patterns, ${errors.filter(e => e.category === "broken_symlink").reduce((a, b) => a + b.count, 0)} occurrences)

**Repos to fix:**
${errors
  .filter(e => e.category === "broken_symlink")
  .sort((a, b) => b.count - a.count)
  .map(e => `- ${e.repo}: ${e.count} occurrences`)
  .join("\n")}

**Action:** Remove or fix dangling symlinks in \`dotfiles_pull/repos/*\` directories.

### Subagent B: Symlink Loop Resolution
**Scope:** All \`symlink_loop\` errors (${errors.filter(e => e.category === "symlink_loop").length} patterns, ${errors.filter(e => e.category === "symlink_loop").reduce((a, b) => a + b.count, 0)} occurrences)

**Repos to fix:**
${errors
  .filter(e => e.category === "symlink_loop")
  .sort((a, b) => b.count - a.count)
  .map(e => `- ${e.repo}: ${e.count} occurrences`)
  .join("\n")}

**Action:** Resolve circular symlink chains (likely HyDE assets).

---

## 💾 Machine-Readable Outputs
- \`audit-data.json\` — Full parsed data
- \`audit-fixes.json\` — Structured fix list for subagents
`;

  // Write outputs
  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(join(OUT_DIR, "audit-report.md"), report);
  writeFileSync(join(OUT_DIR, "audit-data.json"), JSON.stringify({ entries, errors }, null, 2));

  // Fix list for subagents
  const fixList = {
    subagentA: {
      name: "Symlink Cleanup - Broken Symlinks",
      category: "broken_symlink",
      totalPatterns: errors.filter(e => e.category === "broken_symlink").length,
      totalOccurrences: errors.filter(e => e.category === "broken_symlink").reduce((a, b) => a + b.count, 0),
      repos: errors
        .filter(e => e.category === "broken_symlink")
        .sort((a, b) => b.count - a.count)
        .map(e => ({ repo: e.repo, count: e.count, examplePath: e.path, error: e.errorType })),
    },
    subagentB: {
      name: "Symlink Loop Resolution",
      category: "symlink_loop",
      totalPatterns: errors.filter(e => e.category === "symlink_loop").length,
      totalOccurrences: errors.filter(e => e.category === "symlink_loop").reduce((a, b) => a + b.count, 0),
      repos: errors
        .filter(e => e.category === "symlink_loop")
        .sort((a, b) => b.count - a.count)
        .map(e => ({ repo: e.repo, count: e.count, examplePath: e.path, error: e.errorType })),
    },
  };

  writeFileSync(join(OUT_DIR, "audit-fixes.json"), JSON.stringify(fixList, null, 2));

  console.log("\n✅ Audit complete!");
  console.log(`   Report: ${OUT_DIR}/audit-report.md`);
  console.log(`   Data: ${OUT_DIR}/audit-data.json`);
  console.log(`   Fixes: ${OUT_DIR}/audit-fixes.json`);

  // Print summary to console
  console.log("\n" + "=".repeat(60));
  console.log(report.split("---")[2]?.split("\n").slice(0, 15).join("\n") || "");
  console.log("=".repeat(60));
}

main().catch(console.error);