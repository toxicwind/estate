# DSML 04 — the borrow universe (six implementations, one unified contract)

> Modular doc 4. Recon via GHAS/blackbird (2026-11-02). Six independent
> implementations found publicly; tau's scanner now unifies them.

## The fragmented universe (what exists publicly)

| Impl | Language | Approach | Borrowed insight |
| --- | --- | --- | --- |
| `SoreHait/dsml-heal-proxy` | JS | ingress PROXY rewriting raw markup → `delta.tool_calls` | grammar table; V3.2 `function_calls` variant; EOS sentinel leak |
| `Bino5150/lumina` | Python eval | `_GARBLED_PATTERNS` strippers | **pipes are OPTIONAL** (`<\|?\s*DSML\s*\|?[^>]*>`) — bare `<DSML …>` is family |
| `MiaAI-Lab/…DSpark` | vLLM patch | `DSPARK_ENABLE_DSML_RECOVERY` | **provisional tool call**: buffer, validate name against LIVE request tools, commit only on close; verbatim rollback on any doubt |
| `skyjjgw/tianshu-…` | TS plugin | `dsml-recovery.ts` four gates | **close-before-commit** (truncated turns = text, never guessed); **name-must-be-declared**; **no-tools-no-recovery**; **any-doubt-rolls-back-verbatim** |
| `shyringo/…in-c` | C | `dsv4_dsml.c` | **SHORT forms are first-class grammar**: `<inv…` / `</inv>` / `<par…` / `</parameter>` — degradation has canonical short spellings |
| `otheru-ai/ember` | C embedded | `dsml_decode.c` B6 tracker | decode-STATE tracker with per-syntax field names; literal/partial match primitives |

## The 頭 anomaly — RESOLVED

The doc-table glyph that looked like a CJK ideograph (`頭`, U+982D) is
**U+FF5C rendered in a CJK font** — the real vocab bytes are
`ef bd 9c 44 53 4d 4c ef bd 9c` = `｜DSML｜` (id 128825, `special:false`).
GitHub code-search for the glyph body returns **zero** — the community
"DSML" normalization was correct after all; the anomaly was a font illusion
that cost a byte-level detour to prove.

## What tau's scanner now holds (the unified contract)

- SHAPE recognition: optional pipes, optional body, optional space,
  known-or-drifted words, SHORT degradation forms (`<inv`, `<par`, `</inv`)
- omit-START semantics (vLLM #48931): bare named invoke = tool call
- orphan strip for everything else (never visible text)
- partial-tag hold so SSE chunk splits reassemble
- (private-operator gates — name-declared, no-tools-no-recovery,
  verbatim-rollback — live in the TaaS operator layer, arroyo, not the
  dialect scanner; scanner stays content-neutral.)

## Sources

- HF: `deepseek-ai/DeepSeek-V4-Pro/discussions/209` + `encoding/README.md` +
  `encoding/encoding_dsv4.py` (dsml_token = the bar glyph pair)
- vLLM: issue #48931 (START omission), #52645 (provisional recovery upstream),
  #51914 (`toolcalls` variant)
- NVIDIA forums: `spark-vllm-b12x` closer-leak thread (rollback fix)
- Borrowed impls: the six repos above (fetched via GHAS/blackbird + raw
 .githubusercontent, token from keyring SSOT)
