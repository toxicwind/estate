# DSML 03 — the scanner shape contract

> Modular doc 3. The estate's implementation: `packages/ai/src/dialect/deepseek.ts`
> (tau). Tests: `packages/ai/test/dsml-bar-mutation.test.ts` (6 mutations) —
> all 103 dialect-suite tests green at commit `973f84c54c`.

## The contract

1. **Shape beats spelling.** The recognizer is
   `<[/]?[｜|]+(DSML|頭)?[｜|]+\s*word?attrs?>` — bar-runs (≥1, either
   charset), optional body, optional drifted word, arbitrary attrs. The
   next serving-stack mutation cannot break it by changing spelling.
2. **Envelope semantics** (per vLLM #48931 + DeepSeek encoding_dsv4.py):
   - `<…tool_calls>` open → `dsmlSection` state.
   - `<…invoke name="…">` open → `dsmlInvoke` state — **even with no
     envelope open** (START-token omission): a bare NAMED invoke IS a tool
     call, not drift.
   - `<…parameter name="…" string="…">` → `dsmlParam`; value streams as
     `toolArgDelta`; coerced by the `string` attr.
   - Every OTHER family tag (closes without envelope, drifted words like
     `</… calls>`, nameless opens) is an **orphan** — stripped, never
     visible text (issue #10556 mimicry-starvation).
3. **Partial-tag hold.** Any unterminated `<…` tail that could still become
   a DSML tag is held in the buffer — never char-swallowed — so SSE chunk
   splits reassemble (`<｜｜DS` + `ML｜｜invoke>` works).

## The proof matrix (all green)

| Mutation | Result |
| --- | --- |
| canonical single-bar envelope | parsed, args exact |
| double-fullwidth-bar envelope | parsed, zero text leak |
| ascii double-bar (`<\|\|DSML\|\|…>`) | parsed |
| mixed charset bar-runs (`<|｜DSML｜|…>`) | parsed |
| drifted closer `</… calls>` | stripped as orphan |
| orphan open with attrs (`<… invoke name="…">`, no envelope) | omit-START: parsed as tool call |
| envelope split across 7 SSE chunks | reassembled, args exact |
| chunk ends mid-bar-run (`text<｜｜`) | held, no leak |

## Where the bytes come from (test-side pinning)

`tokenizer.json` (doc 02) gives id 128825's exact bytes; the suite mutates
from those bytes, so a serving-stack change that alters the token spelling is
caught by updating ONE fixture — the SHAPE logic is untouched.

## What is deliberately NOT fixed here

- The serving stack itself (freeinference upstream vLLM build) — the leak is
  a runtime regression class there (NVIDIA thread: rollback fixed it). The
  estate scanner is the DEFENSE layer; upstream pinning is an ops decision.
- The `dsml:` lowercase family (vocab ids 128840/128841) — same shape
  tolerance likely needed; not yet observed leaking live.
