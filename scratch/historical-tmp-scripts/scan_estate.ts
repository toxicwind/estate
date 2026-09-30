import { readdirSync, statSync, lstatSync, readlinkSync, existsSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";

interface FileRecord {
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
const scanRoots = [
  join(home, ".local/bin"),
  join(home, "bin"),
  join(home, "sovereign/bin"),
  join(home, ".cargo/bin"),
  join(home, ".bun/bin"),
  join(home, "sovereign/projects/tau/launcher"),
  join(home, "sovereign/projects/mesh/bin"),
  join(home, "sovereign"),
  home,
];

const records: FileRecord[] = [];

function walk(dir: string, maxDepth: number, currentDepth = 0) {
  if (currentDepth > maxDepth || !existsSync(dir)) return;

  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const name = entry.name;
      const fullPath = join(dir, name);

      // Skip huge / irrelevant trees
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
  } catch (err) {
    // Permission or missing dir
  }
}

console.log("Starting Bun Estate Scan...");
const start = performance.now();

for (const root of scanRoots) {
  const maxDepth = root === home ? 1 : 3;
  walk(root, maxDepth, 0);
}

const elapsed = (performance.now() - start).toFixed(2);
console.log(`Scan completed in ${elapsed}ms. Total records: ${records.length}`);

const bizarre = records.filter((r) => r.isBizarre);
console.log(`Total bizarre / anomalous entries: ${bizarre.length}\n`);

// Group by reasons
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
