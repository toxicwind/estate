#!/usr/bin/env node
import { runTokenWalk, quantifyEntropySiphon, annealSchedule } from "./lib/walk.mjs";
import { VOCAB, PSEUDO_TOKEN, DIM, EMBEDDINGS } from "./lib/embeddings.mjs";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const STEPS = 12, T_START = 0.2, T_END = 1.6;
const OUT = process.env.WALK_OUT || "./walk_data.json";

function main() {
  const { results, stats, Ts } = runTokenWalk();
  const quantified = quantifyEntropySiphon(results);
  console.log(`=== Token Walk (deterministic) === DIM=${DIM} STEPS=${STEPS} T ${T_START}->${T_END} vocab=${VOCAB.length}+pseudo`);
  console.log("Annealing :", Ts.map(t => t.toFixed(3)).join(" -> "));
  console.log("Siphon    :", JSON.stringify(quantified));
  console.log("Sample    :");
  console.table(results.filter(r => r.path === "linear").slice(0, 3).map(r => ({ step: r.step, T: r.T, token: r.token, P: r.P, err: r.dPdDelta, jump: r.jump ? `${r.jump.from}->${r.jump.to}` : "" })));
  console.log(`Global maxP=${stats.maxP.toFixed(2)} loadBearing=${stats.loadBearingCount} points=${results.length}`);
  try {
    mkdirSync(dirname(OUT), { recursive: true });
    writeFileSync(OUT, JSON.stringify({ results, quantified, Ts, vocab: VOCAB, pseudo: PSEUDO_TOKEN, formula: "P=25+T*18+dist*0.85+jitter" }, null, 2));
    console.log(`wrote ${OUT}`);
  } catch (e) { console.error("write failed:", e.message); process.exitCode = 2; }
  return { results, quantified };
}
main();
