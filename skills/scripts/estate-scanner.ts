#!/usr/bin/env bun
/**
 * estate-scanner.ts — High-throughput sovereign estate path & binary audit engine.
 *
 * Fast filesystem traversal, broken symlink detection, bizarre path / git-mode
 * corruption audit, and bin directory sanity check across the sovereign estate.
 */

import { readdirSync, statSync, lstatSync, readlinkSync, existsSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";

export interface FileRecord {
  dir: string;
  name: string;
  fullPath: string;
  isLink: boolean;
  isBrokenLink: boolean;
  linkTarget: string;
  isFile: boolean;
  isDir: boolean;
  isExec: boolean;
  isBizarre: boolean;
  bizarreReasons: string[];
  sizeBytes: number;
}

const home = homedir();
const sovereignRoot = join(home, "sovereign");

const scanRoots = [
  join(home, ".local/bin"),
  join(home, "bin"),
  join(sovereignRoot, "bin"),
  join(sovereignRoot, "helpers"),
  join(home, ".cargo/bin"),
  join(home, ".bun/bin"),
  join(sovereignRoot, "projects/tau/launcher"),
  join(sovereignRoot, "projects/range/bin"),
  sovereignRoot,
  home,
];

export function scanEstate(): { records: FileRecord[]; durationMs: number } {
  const records: FileRecord[] = [];
  const start = performance.now();

  function walk(dir: string, maxDepth: number, currentDepth = 0) {
    if (currentDepth > maxDepth || !existsSync(dir)) return;

    try {
      const entries = readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const name = entry.name;
        const fullPath = join(dir, name);

        // Skip massive un-auditable scratch trees
        if (
          name === ".git" ||
          name === "node_modules" ||
          name === "target" ||
          name === "dotfiles_pull" ||
          name === ".cache" ||
          name === "cache" ||
          name === "gist-archive"
        ) {
          continue;
        }

        let isLink = false;
        let isBrokenLink = false;
        let linkTarget = "";
        let isFile = false;
        let isDir = false;
        let isExec = false;
        let sizeBytes = 0;

        try {
          const lstat = lstatSync(fullPath);
          isLink = lstat.isSymbolicLink();
          if (isLink) {
            try {
              linkTarget = readlinkSync(fullPath);
              isBrokenLink = !existsSync(fullPath);
            } catch {
              isBrokenLink = true;
            }
          }

          isDir = entry.isDirectory() && !isLink;
          isFile = entry.isFile() || (isLink && !isDir);
          if (!isDir && existsSync(fullPath)) {
            const stat = statSync(fullPath);
            sizeBytes = stat.size;
            isExec = (stat.mode & 0o111) !== 0;
          }
        } catch {
          isBrokenLink = true;
        }

        const bizarreReasons: string[] = [];
        if (name.includes(":")) bizarreReasons.push("colon_in_name");
        if (name.startsWith("100644") || name.startsWith("100755")) bizarreReasons.push("git_mode_in_name");
        if (name.startsWith(" ") || name.endsWith(" ")) bizarreReasons.push("whitespace_padding");
        if (name.includes("\\")) bizarreReasons.push("backslash_in_name");
        if (isBrokenLink && (dir.includes("bin") || dir === home)) bizarreReasons.push("broken_symlink_in_bin_or_home");
        if ((name.endsWith(".bak") || name.includes(".bak-")) && dir.includes("bin")) bizarreReasons.push("backup_pile_in_bin");

        records.push({
          dir,
          name,
          fullPath,
          isLink,
          isBrokenLink,
          linkTarget,
          isFile,
          isDir,
          isExec,
          isBizarre: bizarreReasons.length > 0,
          bizarreReasons,
          sizeBytes,
        });

        if (isDir) {
          walk(fullPath, maxDepth, currentDepth + 1);
        }
      }
    } catch {
      // Ignore unreadable dirs
    }
  }

  for (const root of scanRoots) {
    const maxDepth = root === home ? 1 : 3;
    walk(root, maxDepth, 0);
  }

  const durationMs = performance.now() - start;
  return { records, durationMs };
}

if (import.meta.main) {
  console.log("== Sovereign Estate Path & Binary Audit ==");
  const { records, durationMs } = scanEstate();
  console.log(`Scanned ${records.length} paths in ${durationMs.toFixed(2)}ms`);

  const bizarre = records.filter((r) => r.isBizarre);
  console.log(`Anomalies detected: ${bizarre.length}`);

  const groups = new Map<string, FileRecord[]>();
  for (const r of bizarre) {
    const key = r.bizarreReasons.sort().join("+");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(r);
  }

  for (const [reason, items] of groups.entries()) {
    console.log(`\n=== [Anomaly: ${reason}] (Count: ${items.length}) ===`);
    for (const item of items) {
      const targetInfo = item.linkTarget ? ` -> ${item.linkTarget}` : "";
      console.log(`  - ${item.name} (${item.fullPath})${targetInfo}`);
    }
  }

  const broken = records.filter((r) => r.isBrokenLink && r.dir.includes("bin"));
  if (broken.length === 0) {
    console.log("\nPASS: All PATH bin symlinks are valid and healthy.");
  } else {
    console.log(`\nFAIL: ${broken.length} broken symlinks in PATH.`);
    process.exit(1);
  }
}
