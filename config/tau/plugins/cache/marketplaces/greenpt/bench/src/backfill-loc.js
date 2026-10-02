#!/usr/bin/env node
"use strict";
// Backfill the `loc` field into a committed stamp's results.json by re-extracting
// code from the saved replies in raw/. Offline, no API spend — the replies are
// already on disk, only the metric is new.
//
//   node src/backfill-loc.js <stamp> [--dry]
//
// Records that already carry `loc` are left alone, so this is idempotent.

const fs = require("fs");
const path = require("path");
const { extractInfo, loc } = require("./extract");

const [stamp, ...rest] = process.argv.slice(2);
if (!stamp) {
  console.error("usage: node src/backfill-loc.js <stamp> [--dry]");
  process.exit(2);
}
const DRY = rest.includes("--dry");

const ROOT = path.join(__dirname, "..");
const file = path.join(ROOT, "results", stamp, "results.json");
const rawDir = path.join(ROOT, "results", stamp, "raw");
const data = JSON.parse(fs.readFileSync(file, "utf8"));

// lang per task, from the task definition — extraction needs it to pick the right fences
const langs = {};
for (const id of fs.readdirSync(path.join(ROOT, "tasks"))) {
  const metaPath = path.join(ROOT, "tasks", id, "meta.json");
  if (!fs.existsSync(metaPath)) continue;
  const meta = JSON.parse(fs.readFileSync(metaPath, "utf8"));
  langs[id] = meta.lang === "python" ? "python" : meta.type === "web" ? "html" : "javascript";
}

let done = 0, skipped = 0, missing = 0;
for (const r of data.records) {
  if (r.loc != null) { skipped++; continue; }
  if (r.type === "relay") { skipped++; continue; } // no code to count
  const reply = path.join(rawDir, `${r.variant}__${r.task}__r${r.run}.md`);
  if (!fs.existsSync(reply)) { missing++; continue; }

  const text = fs.readFileSync(reply, "utf8");
  const ex = extractInfo(text, langs[r.task] || "javascript");
  let code = ex.code;
  // same fallback as run.js: raw unfenced HTML still counts
  if (r.type === "web" && !/<(html|body|main|section|div)\b/i.test(code)) code = text;
  r.loc = loc(code);
  done++;
}

console.log(`${stamp}: ${done} backfilled, ${skipped} skipped, ${missing} missing raw reply`);
if (DRY) { console.log("(dry run — nothing written)"); process.exit(0); }
if (done) fs.writeFileSync(file, JSON.stringify(data, null, 2));
