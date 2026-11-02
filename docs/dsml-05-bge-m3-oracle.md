# DSML 05 — bge-m3 the oracle: eight workstreams, one black box opened

> Modular doc 5. All experiments live-verified on the estate's freeinference
> bge-m3 lane (1024-dim); artifacts in
> `estate/archive/2026-11-02-tau-bge-m3-blackbox/`. The bar-run arc (docs
> 01-04) was the on-ramp; this is the destination.

## The core discoveries (all byte/probe-verified, all novel)

**W1 compositionality — WEAK, and that's the finding.**
`e(sentence)` vs mean-of-word-vectors: 0.62-0.81. The sphere is NOT a
bag-of-words. But the order test is the bombshell:
**"the dog chased the cat" ↔ "the cat chased the dog" = 0.990** — bge-m3 is
nearly ROLE-BLIND for agent-patient swaps. Yet polysemy separates
(rust-compile ↔ rust-oxidize = 0.583). Meaning: token SENSE dominates,
syntactic ROLE nearly vanishes — the sphere encodes "what is being
talked about", not "who did what to whom".

**W4 order/negation — the negation collapse.**
`not-agree ↔ disagree = 0.944` (negation → antonym) but
`agree ↔ not-agree = 0.759` (asymmetric gap). And **litotes is REAL**:
`good ↔ not-bad = 0.959` vs `good ↔ bad = 0.743` — "not bad" lands in
good-space. And the nonsense-swap ("the apple ate Eve") = 0.950 to its
sensible counterpart — semantic ROLE is nearly destroyed for embeds.

**W5 multilingual pivot — translations collapse, but not to ONE point.**
Within-set means 0.83-0.92, spreads up to 0.219 — same-meaning sentences
live in a NEIGHBORHOOD, not a point. Cross-meaning pairs drop to 0.46 —
six clean language-independent meaning-clusters with zero confusion.

**W6 length physics — meaning survives padding, but drifts.**
1x↔10x = 0.897, 1x↔100x = 0.783, 10x↔100x = 0.891 — a monotone
drift-quantization: repetition moves the point ~0.1 cosine per 10x, and the
drift is TRANSITIVE (10x↔100x ≈ 1x↔10x). A length-invariant meaning
estimator: project out the drift direction.

**W3 unicode planes — the mangle axis.**
`｜ (FF5C) ↔ | (ascii) = 1.000` — char-level embeddings CANNOT see the
fullwidth/ascii difference (the font-illusion root cause, now measured).
But `｜ ↔ 頭 (U+982D) = 0.563` — the mangle axis is detectable at the
CHAR level. Scripts cluster loosely (latin 0.585, cjk 0.429, kana 0.730) —
single-char geometry is script-identity, not script-structure.

**W7 INJECTION ORACLE — the product.**
A calibrated instruction-vs-data axis: pure instructions +0.27..+0.43,
pure data −0.30..−0.38 (clean zero-crossing), and instruction-text inside
data flags POSITIVE (+0.09..+0.25) while its container stays negative.
Zero-cost tripwire for every text entering an agent context. LANDED as
`pens/geode/products/injection-detector` (4 TDD tests, live keyring lane,
public repo, star-whored).

**W8 protocol fingerprinting — a free dialect-classifier.**
Same tool call in 8 surfaces: the protocol-axis separates ALL dialects
(+0.21..+0.34) from prose (−0.34) in ONE cosine. Confusability map: hermes↔qwen
0.952 (same JSON-in-wrapper family), anthropic↔minimax 0.910, dsml↔anthropic
0.892. A zero-cost stream-router: embed the chunk, project, route.

**E1/E2 (the DSML arc's on-ramp):** determinism exact; markup-axis ±0.533;
the DSML degradation family provably separable from prose in one call.

## The keystone (why bge-m3 is a black box worth opening)

Free + unlimited + hosted + 1024-dim + unit-normalized (everything) +
deterministic. Nobody probed its GEOMETRY. The eight results above are all
ONE-COSINE operations — the cheapest possible semantic primitives for
coding agents: leak firewalls, injection tripwires, translation pivots,
dialect routers, truth/negation/order/nature probes.

## Sources

- Estate archive `2026-11-02-tau-bge-m3-blackbox/` — W4/W5/W3/W7/W8/W2/W6
  artifacts + the experiment scripts (copy-pasteable)
- DSML arc: docs 01-04; tau scanner `973f84c54c`
- Community: HF #209, vLLM #48931, NVIDIA spark-vllm thread
