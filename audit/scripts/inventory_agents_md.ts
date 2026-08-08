// Audit script: inventory all AGENTS.md files with hashes and metadata
// Run: bun run audit/scripts/inventory_agents_md.ts

import { glob } from "glob";
import { createHash } from "node:crypto";
import { stat } from "node:fs/promises";
import { resolve } from "node:path";

const IGNORE_PATTERNS = [
  "**/node_modules/**",
  "**/.cargo/**",
  "**/.npm/**",
  "**/go/pkg/**",
  "**/.cache/**",
  "**/vendor/**",
  "**/.librefang/**",
  "**/.openfang/**",
  "**/archive/**",
];

interface AgentFileEntry {
  path: string;
  size: number;
  mtime: number;
  md5: string;
  isSymlink: boolean;
  isThirdParty: boolean;
}

function computeMd5(content: Buffer): string {
  return createHash("md5").update(content).digest("hex");
}

function isThirdParty(path: string): boolean {
  const thirdPartyMarkers = [
    "node_modules",
    ".cargo",
    ".npm",
    "go/pkg",
    "vendor",
    ".cache",
  ];
  return thirdPartyMarkers.some((m) => path.includes(m));
}

async function main() {
  const files = await glob("**/AGENTS.md", {
    cwd: "/home/toxic",
    ignore: IGNORE_PATTERNS,
    nodir: true,
  });

  const entries: AgentFileEntry[] = [];

  for (const file of files) {
    const fullPath = resolve("/home/toxic", file);
    try {
      const stats = await stat(fullPath);
      const content = await Bun.file(fullPath).bytes();
      entries.push({
        path: fullPath,
        size: stats.size,
        mtime: Math.floor(stats.mtimeMs / 1000),
        md5: computeMd5(Buffer.from(content)),
        isSymlink: stats.isSymbolicLink(),
        isThirdParty: isThirdParty(fullPath),
      });
    } catch (e) {
      console.error(`Error reading ${fullPath}:`, e);
    }
  }

  // Group by hash to find duplicates
  const byHash = new Map<string, AgentFileEntry[]>();
  for (const entry of entries) {
    const existing = byHash.get(entry.md5) || [];
    existing.push(entry);
    byHash.set(entry.md5, existing);
  }

  // Output
  const output = {
    totalFiles: entries.length,
    uniqueHashes: byHash.size,
    thirdPartyFiles: entries.filter((e) => e.isThirdParty).length,
    userFiles: entries.filter((e) => !e.isThirdParty).length,
    duplicates: [...byHash.entries()]
      .filter(([_, v]) => v.length > 1)
      .map(([hash, files]) => ({ hash, count: files.length, paths: files.map((f) => f.path) })),
    entries: entries.sort((a, b) => a.path.localeCompare(b.path)),
  };

  const outPath = "/home/toxic/sovereign/audit/agents_md_inventory.json";
  await Bun.write(outPath, JSON.stringify(output, null, 2));
  console.log(`Wrote ${entries.length} entries to ${outPath}`);
  console.log(`Unique hashes: ${byHash.size}`);
  console.log(`Duplicates: ${output.duplicates.length}`);
}

main();
