# DSML serving-stack degradation — the bar-run anomaly

> Modular doc 1 of the DSML series. Sources at the bottom; every claim is
> byte-verified or cited. Companion: `dsml-02-tokenizer-ground-truth.md`,
> `dsml-03-scanner-shape-contract.md`.

## What leaked (the observable)

A live DeepSeek-family stream on the estate's freeinference lane emitted
tool-call markup with MUTATED delimiters straight into the assistant's
visible text:

```
<｜｜DSML｜｜ calls>
<｜｜DSML｜｜ invoke name="eval">
<｜｜DSML｜｜ parameter name="language" string="true">js</｜｜DSML｜｜ parameter>
...
</｜｜DSML｜｜ invoke>
</｜｜DSML｜｜ calls>
```

The two tool calls inside (a bun-transpiler eval + a kappa-code grep) were
NEVER executed — the estate received them as prose. The work was orphaned
inside the markup.

## Byte ground truth (vocab id 128825, real tokenizer.json)

```
token bytes: efbd9c 44534d4c efbd9c
             └──U+FF5C──┘ DSML └──U+FF5C──┘
```

- The DSML special token = **U+FF5C (FULLWIDTH VERTICAL LINE) + "DSML" +
  U+FF5C**. It is NOT a CJK ideograph — the `頭`-looking glyph is U+FF5C
  rendered in a CJK font. Verified from
  `deepseek-ai/DeepSeek-V4-Flash-0731/tokenizer.json` (added_tokens id 128825,
  `special: false`).
- The full tags (`<｜DSML｜tool_calls>` etc.) are NOT special tokens — they are
  ordinary characters around the one special token (MoonBit tokenizer
  analysis).

## The anomaly (what everyone else normalizes)

| Form | Bars | Body | Seen |
| --- | --- | --- | --- |
| `<｜DSML｜tool_calls>` | ×1 fullwidth | DSML | canonical (docs + vocab) |
| `<\|\|DSML\|\|tool_calls>` | ×2 ascii | DSML | HF #209 (V4-Pro, vLLM) |
| `<｜｜DSML｜｜tool_calls>` | ×2 fullwidth | DSML | estate leak (this doc) |
| `<｜｜DSML｜｜ invoke ...>` | ×2 + space | DSML | estate leak |
| `</｜｜DSML｜｜ calls>` | ×2 | **calls** (drifted word) | estate leak |
| `<|｜DSML｜|invoke>` | mixed | DSML | estate leak |

## Why it matters (the orphaned-work effect)

Every mutation the parser misses (a) leaks protocol text into user-visible
content and (b) **orphanes the tool call inside it** — real work the model
meant to execute never runs. Worse: per issue #10556 mechanics, each stored
leak teaches the model to mimic and further mutate the markup.

## Community evidence (we are not alone)

- **HF deepseek-ai/DeepSeek-V4-Pro discussion #209** (Jul 8): degraded
  `<||DSML||tool_calls>`; reporter ships a normalize-regex
  (`(?:\|\s*\||｜\s*｜)` → canonical).
- **vLLM issue #48931**: parser leaks raw DSML when the model OMITS the
  `<｜DSML｜tool_calls>` START token (long contexts); fix = enter tool mode on
  a full invoke_start match with bounded hold-back.
- **NVIDIA forums (spark-vllm-b12x)**: closers leak after a runtime bump;
  rollback to the prior vLLM image stopped the leak — a serving-stack
  regression, not a finetune defect.

## The deeper read (beyond their fixes)

The community normalizes bar-runs toward the ASCII spelling. Two blind spots:

1. **Enumeration never converges** — the next serving-stack build mutates
   differently. The invariant is the SHAPE (`<[/]?bars[body]bars word?
   attrs?>`), not any spelling. bge-m3 clustering of the whole family:
   mutations at 0.86-0.99 cosine to canonical; ordinary text at 0.43-0.54 —
   one semantic cluster, provably separable from prose.
2. **The estate holds the tokenizer truth locally** — `tokenizer.json`
   downloaded + parsed on-box; the vocab id 128825 bytes are checkable at
   test time, so scanner regressions can be pinned against the REAL
   vocabulary, not doc quotes.
