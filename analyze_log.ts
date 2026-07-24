import * as dfd from "danfojs-node";
import * as fs from "fs";

// Read the log file
const logContent = fs.readFileSync("sovereign/2026-07-22T00:07:28-06:00.log", "utf-8");
const lines = logContent.split("\n").filter(l => l.trim().length > 0);

console.log(`Total lines: ${lines.length}`);

// Parse log lines
interface LogEntry {
  timestamp: string;
  level: string;
  module: string;
  message: string;
}

const entries: LogEntry[] = [];
const regex = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}:\d{2})\s+(INFO|WARN|ERROR|DEBUG|TRACE)\s+\[([^\]]+)\]\s+(.+)$/;

for (const line of lines) {
  const match = line.match(regex);
  if (match) {
    entries.push({
      timestamp: match[1],
      level: match[2],
      module: match[3],
      message: match[4],
    });
  }
}

console.log(`Parsed entries: ${entries.length}`);

// Create DataFrame
const df = new dfd.DataFrame(entries);

console.log("\n--- Log Level Distribution ---");
const levelCounts = df["level"].valueCounts();
console.log(levelCounts);

console.log("\n--- Top Modules ---");
const moduleCounts = df["module"].valueCounts();
console.log(moduleCounts.head(20));

console.log("\n--- Error/Warning entries ---");
const errors = df.query({ column: "level", is: "in", to: ["ERROR", "WARN"] });
console.log(errors.head(20).toString());

// Save to CSV for further analysis
df.toCSV("log_analysis.csv");
console.log("\nSaved to log_analysis.csv");
