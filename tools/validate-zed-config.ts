#!/usr/bin/env bun
// validate-zed-config.ts — runtime rejection, not prose reminder.
// Run BEFORE applying any Zed/settings.json change:
//   bun ~/sovereign/tools/validate-zed-config.ts
// Exits 1 on the first hard failure. The agent should never claim "config is correct"
// without this passing.

import { readFileSync, existsSync } from "node:fs";
import json5 from "json5";

// Zed configs are JSONC (comments + trailing commas). Parse with json5, not stdlib json.
function parseJSONC(raw: string): any {
  return json5.parse(raw);
}

const ZED = "/home/toxic/.config/zed/settings.json";
let failures = 0;
const fail = (m: string) => {
  console.error("  FAIL:", m);
  failures++;
};
const ok = (m: string) => console.log("  ok:", m);

console.log("== validate-zed-config ==");

// 1. JSON parses (catches trailing commas, comments if using json5 upstream).
if (!existsSync(ZED)) fail(`${ZED} missing`);
else {
  const raw = readFileSync(ZED, "utf8");
  try {
    parseJSONC(raw);
    ok("settings.json valid JSONC");
  } catch (e: any) {
    fail(`invalid JSONC: ${e.message}`);
  }
}

// 2. Exactly ONE context_server: mcpproxy-sovereign.
try {
  const j = parseJSONC(readFileSync(ZED, "utf8"));
  const cs = j.context_servers || {};
  const ks = Object.keys(cs);
  if (ks.length === 1 && ks[0] === "mcpproxy-sovereign")
    ok("single mcpproxy-sovereign entry");
  else
    fail(
      `expected exactly 1 context_server 'mcpproxy-sovereign', got: ${ks.join(", ")}`,
    );

  // 3. No openai_compatible model uses forbidden fields.
  const lm = j.language_models?.openai_compatible || {};
  let bad = 0;
  for (const prov of Object.keys(lm)) {
    for (const m of lm[prov].available_models || []) {
      for (const f of ["tool_parser", "hf_model", "reasoning_parser"]) {
        if (f in m) {
          fail(`provider ${prov} model ${m.name} has forbidden field ${f}`);
          bad++;
        }
      }
    }
  }
  if (!bad) ok("no openai_compatible forbidden fields");

  // 4. No custom_headers.Authorization on openai_compatible (stripped by Zed).
  for (const prov of Object.keys(lm)) {
    const ch = lm[prov].custom_headers || {};
    if ("Authorization" in ch)
      fail(
        `provider ${prov} sets custom_headers.Authorization (stripped by Zed)`,
      );
  }
  if (
    !Object.keys(lm).some(
      (p) => "Authorization" in (lm[p].custom_headers || {}),
    )
  )
    ok("no custom_headers.Authorization");
} catch {}

console.log(
  failures
    ? `\n${failures} FAILURE(S) — config rejected.`
    : "\nAll checks passed.",
);
process.exit(failures ? 1 : 0);
