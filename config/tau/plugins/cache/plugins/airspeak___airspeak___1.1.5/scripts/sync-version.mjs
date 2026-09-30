#!/usr/bin/env node
// Propagate plugin/package.json version to SKILL.md (both copies) and
// marketplace.json. `--check` verifies only; otherwise syncs.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const check = process.argv.includes("--check");
const { version } = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));

const targets = [
  ...["../skills/airspeak/SKILL.md", "skills/airspeak/SKILL.md"].map((rel) => ({
    label: `${rel} metadata.version`,
    file: join(root, rel),
    read: (t) => t.match(/^(  version: ")([^"]*)(")$/m)?.[2],
    write: (t) => t.replace(/^(  version: ")[^"]*(")$/m, `$1${version}$2`),
  })),
  {
    label: ".omp-plugin/marketplace.json (metadata + plugins[0])",
    file: join(root, "../.omp-plugin/marketplace.json"),
    read: (t) => {
      const m = JSON.parse(t);
      return m.metadata.version === m.plugins[0].version ? m.metadata.version : null;
    },
    write: (t) => {
      const m = JSON.parse(t);
      m.metadata.version = version;
      m.plugins[0].version = version;
      return JSON.stringify(m, null, 2) + "\n";
    },
  },
];

const stale = [];
for (const t of targets) {
  const text = readFileSync(t.file, "utf8");
  const current = t.read(text);
  if (current === version) continue;
  if (check) {
    stale.push(`${t.label}: ${current ?? "unparseable"} != ${version}`);
  } else {
    writeFileSync(t.file, t.write(text));
    stale.push(t.label);
  }
}

if (check && stale.length) {
  console.error(`version check failed (expected ${version}):\n  ${stale.join("\n  ")}`);
  process.exit(1);
}
console.log(check ? `all version fields in sync at ${version}` : stale.length ? `updated to ${version}: ${stale.join(", ")}` : `already in sync at ${version}`);
