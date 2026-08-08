// Audit script: find all Rust/Go/Bun/Node projects in sovereign ecosystem
// Run: bun run audit/scripts/audit_languages.ts

import { glob } from "glob";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

interface ProjectInfo {
  path: string;
  language: "rust" | "go" | "bun" | "node" | "python" | "mixed";
  hasCargoToml: boolean;
  hasGoMod: boolean;
  hasPackageJson: boolean;
  hasBunLock: boolean;
  hasMiseToml: boolean;
  deps: string[];
}

const SEARCH_DIRS = [
  "/home/toxic/projects",
  "/home/toxic/sovereign",
];

async function scanProject(dir: string): Promise<ProjectInfo | null> {
  const files = await glob("*", { cwd: dir, nodir: true });
  const hasCargoToml = files.includes("Cargo.toml");
  const hasGoMod = files.includes("go.mod");
  const hasPackageJson = files.includes("package.json");
  const hasBunLock = files.includes("bun.lock") || files.includes("bun.lockb");
  const hasMiseToml = files.includes("mise.toml") || files.includes(".mise.toml");

  if (!hasCargoToml && !hasGoMod && !hasPackageJson) return null;

  let language: ProjectInfo["language"] = "mixed";
  if (hasCargoToml) language = "rust";
  else if (hasGoMod) language = "go";
  else if (hasBunLock) language = "bun";
  else if (hasPackageJson) language = "node";

  return {
    path: dir,
    language,
    hasCargoToml,
    hasGoMod,
    hasPackageJson,
    hasBunLock,
    hasMiseToml,
    deps: [],
  };
}

async function main() {
  const results: ProjectInfo[] = [];

  for (const searchDir of SEARCH_DIRS) {
    const entries = await glob("*", { cwd: searchDir, nodir: false });
    for (const entry of entries) {
      const fullPath = resolve(searchDir, entry);
      try {
        const info = await scanProject(fullPath);
        if (info) results.push(info);
      } catch {}
    }
  }

  const rust = results.filter((r) => r.language === "rust");
  const go = results.filter((r) => r.language === "go");
  const bun = results.filter((r) => r.language === "bun");
  const node = results.filter((r) => r.language === "node");

  console.log("=== LANGUAGE AUDIT ===\n");
  console.log(`Rust projects (${rust.length}):`);
  rust.forEach((r) => console.log(`  - ${r.path}`));
  console.log(`\nGo projects (${go.length}):`);
  go.forEach((r) => console.log(`  - ${r.path}`));
  console.log(`\nBun projects (${bun.length}):`);
  bun.forEach((r) => console.log(`  - ${r.path}`));
  console.log(`\nNode projects (${node.length}):`);
  node.forEach((r) => console.log(`  - ${r.path}`));

  // Output JSON
  const output = { total: results.length, rust, go, bun, node };
  await Bun.write("/home/toxic/sovereign/audit/language_audit.json", JSON.stringify(output, null, 2));
}

main();
