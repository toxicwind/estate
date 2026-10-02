// PX benchmark: text tokens vs image tokens for the honey-px read path.
//
// Renders repo corpora of varying token density with pxpipe's public renderer
// (renderTextToImages, reflow:true — the same path `pxpipe export` and the
// honey-px skill use) and compares:
//
//   text tokens   @anthropic-ai/tokenizer + gpt-tokenizer o200k (same pair as
//                 bench/eso/formats.mjs and bench/headroom/run.mjs)
//   image tokens  Anthropic's pixel formula, ceil(w*h/750) per page — an
//                 ESTIMATE of billed vision tokens, not measured usage
//
// Comprehension is NOT measured here (needs a live model panel; see
// RESULTS.md for the in-session Fable 5 read-back check). Token deltas are a
// different axis from the lossless ESON/TOON deltas: PX is LOSSY on exact
// strings — misreads are silent. The honey-px skill carries the guards.

import fs from "node:fs";
import path from "node:path";
import { countTokens as claudeTokens } from "@anthropic-ai/tokenizer";
import { countTokens as o200kTokens } from "gpt-tokenizer/encoding/o200k_base";
import { renderTextToImages } from "pxpipe-proxy";

const ROOT = path.resolve(new URL(".", import.meta.url).pathname, "../..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

// Density spread: dense JS, dense JSON, markdown prose, and a multi-page slab.
const CORPORA = [
  { label: "dense JS (bin/eso.js)", text: read("bin/eso.js") },
  { label: "dense JS (eso/index.js)", text: read("eso/index.js") },
  {
    label: "dense JSON (dict_array_100)",
    text: read("bench/headroom/fixtures/dict_array_100_sequential_b91d1fff5ba3.json"),
  },
  {
    label: "dense JSON (time_series_50)",
    text: read("bench/headroom/fixtures/time_series_50_25cd28df5a50.json"),
  },
  { label: "md prose (skills/honey/SKILL.md)", text: read("skills/honey/SKILL.md") },
  { label: "md prose (README.md)", text: read("README.md") },
  {
    label: "repo slab (eso/*.js joined)",
    text: fs
      .readdirSync(path.join(ROOT, "eso"))
      .filter((f) => f.endsWith(".js"))
      .map((f) => `\n===== eso/${f} =====\n` + read(path.join("eso", f)))
      .join(""),
  },
];

const visionTokens = (pages) =>
  pages.reduce((s, p) => s + Math.ceil((p.width * p.height) / 750), 0);

const rows = [];
let sumC = 0, sumImg = 0;
for (const { label, text } of CORPORA) {
  const { pages, droppedChars } = await renderTextToImages(text, { reflow: true });
  const img = visionTokens(pages);
  const c = claudeTokens(text);
  rows.push({
    corpus: label,
    chars: text.length,
    "chars/tok": +(text.length / c).toFixed(2),
    "text tok (claude)": c,
    "text tok (o200k)": o200kTokens(text),
    pages: pages.length,
    "img tok (est)": img,
    saved: `${Math.round((1 - img / c) * 100)}%`,
    dropped: droppedChars,
  });
  sumC += c;
  sumImg += img;
}

console.log("PX: text vs image tokens (image = ceil(w*h/750) estimate, reflow render)\n");
console.table(rows);
console.log(
  `TOTAL  ${sumC} text tokens (claude) -> ${sumImg} image tokens  ` +
    `(${Math.round((1 - sumImg / sumC) * 100)}% saved)`
);
console.log(
  "\nBreak-even: image cost is fixed by pixels, so wins shrink as chars/token rises." +
    "\nLOSSY on exact strings — see skills/honey-px/SKILL.md guards before using."
);
