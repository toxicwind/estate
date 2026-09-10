// Engine Audit Skill — sovereign/skills/engine-audit.ts
// Audits the tau engine fork vs upstream oh-my-pi, produces structured diff dataframes.
// Usage: bun run /home/toxic/sovereign/skills/engine-audit.ts

import { writeFileSync, mkdirSync } from "node:fs";
import { execSync } from "node:child_process";
import { join } from "node:path";

const TAU_DIR = "/home/toxic/projects/sovereign-projects/tau";
const ENGINE_DIR = join(TAU_DIR, "engine");
const VENDOR_OH_MY_PI = join(ENGINE_DIR, "vendor/oh-my-pi/packages");
const ENGINE_PACKAGES = join(ENGINE_DIR, "packages");
const SKILLS_DIR = "/home/toxic/sovereign/skills";

interface DiffRow {
  type: "only_in_engine" | "only_in_vendor" | "modified";
  location: string;
  file: string;
  vendor_path?: string;
  engine_path?: string;
}

function runDiff(): string {
  const cmd = `diff -rq "${VENDOR_OH_MY_PI}" "${ENGINE_PACKAGES}" 2>&1 || true`;
  return execSync(cmd, { encoding: "utf-8", maxBuffer: 10 * 1024 * 1024 });
}

function parseDiff(output: string): DiffRow[] {
  const lines = output.trim().split("\n");
  const records: DiffRow[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("Only in ")) {
      const colonIdx = trimmed.indexOf(": ");
      if (colonIdx > 0) {
        const loc = trimmed.slice(8, colonIdx);
        const file = trimmed.slice(colonIdx + 2);
        records.push({
          type: loc.includes("engine/packages") ? "only_in_engine" : "only_in_vendor",
          location: loc.replace(`${ENGINE_DIR}/`, ""),
          file,
        });
      }
    } else if (trimmed.startsWith("Files ") && trimmed.includes(" differ")) {
      const match = trimmed.match(/^Files (.+) and (.+) differ$/);
      if (match) {
        records.push({
          type: "modified",
          vendor_path: match[1].replace(`${ENGINE_DIR}/`, ""),
          engine_path: match[2].replace(`${ENGINE_DIR}/`, ""),
        });
      }
    }
  }
  return records;
}

function generateMarkdown(df: DiffRow[]): string {
  const engineOnly = df.filter((r) => r.type === "only_in_engine");
  const vendorOnly = df.filter((r) => r.type === "only_in_vendor");
  const modified = df.filter((r) => r.type === "modified");

  const lines: string[] = [];
  lines.push("# Engine Audit — Sovereign Fork vs Upstream");
  lines.push("");
  lines.push(`Generated: ${new Date().toISOString()}`);
  lines.push(`Total differences: ${df.length}`);
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  lines.push("| Type | Count |");
  lines.push("|------|-------|");
  lines.push(`| Only in engine (sovereign) | ${engineOnly.length} |`);
  lines.push(`| Only in vendor (upstream) | ${vendorOnly.length} |`);
  lines.push(`| Modified | ${modified.length} |`);
  lines.push("");

  lines.push("## Sovereign Additions (only in engine)");
  lines.push("");
  for (const r of engineOnly) {
    lines.push(`- \`${r.location}/${r.file}\``);
  }
  lines.push("");

  lines.push("## Upstream Only (not in engine)");
  lines.push("");
  for (const r of vendorOnly) {
    lines.push(`- \`${r.location}/${r.file}\``);
  }
  lines.push("");

  lines.push("## Modified Files");
  lines.push("");
  for (const r of modified) {
    lines.push(`- vendor: \`${r.vendor_path}\` → engine: \`${r.engine_path}\``);
  }
  lines.push("");

  return lines.join("\n");
}

function saveCSV(df: DiffRow[], path: string) {
  const header = "type,location,file,vendor_path,engine_path\n";
  const rows = df
    .map((r) => {
      if (r.type === "modified") {
        return `${r.type},"","","${r.vendor_path || ""}","${r.engine_path || ""}"`;
      }
      return `${r.type},"${r.location}","${r.file}","",""`;
    })
    .join("\n");
  writeFileSync(path, header + rows);
}

function main() {
  console.log("Running engine audit...");
  const diffOutput = runDiff();
  const df = parseDiff(diffOutput);

  mkdirSync(SKILLS_DIR, { recursive: true });

  const csvPath = join(SKILLS_DIR, "engine-vendor-diff.csv");
  const mdPath = join(SKILLS_DIR, "engine-audit.md");

  saveCSV(df, csvPath);
  const md = generateMarkdown(df);
  writeFileSync(mdPath, md);

  console.log(`Saved ${df.length} rows to ${csvPath}`);
  console.log(`Saved audit to ${mdPath}`);
  console.log("");
  console.log("=== Summary ===");
  console.log(`Total: ${df.length}`);
  console.log(`Only in engine: ${df.filter((r) => r.type === "only_in_engine").length}`);
  console.log(`Only in vendor: ${df.filter((r) => r.type === "only_in_vendor").length}`);
  console.log(`Modified: ${df.filter((r) => r.type === "modified").length}`);
}

main();
