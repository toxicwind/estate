# DSML 02 — tokenizer ground truth (the on-box proof)

> Modular doc 2. The estate holds the REAL vocabulary locally; scanner
> regressions are pinned against these bytes, not doc quotes.

## Files (downloaded 2026-11-02, `~60s` TTL refresh recommended)

- `/tmp/deepseek-tok/tokenizer.json` — 6.3 MB, BPE, vocab 128000 + 1283 added
- Source: `deepseek-ai/DeepSeek-V4-Flash-0731` (the exact model family the
  estate's freeinference lane serves)

## The DSML token

| Field | Value |
| --- | --- |
| id | **128825** |
| content | `｜DSML｜` |
| utf-8 | `ef bd 9c 44 53 4d 4c ef bd 9c` |
| utf-16 | `ff5c 0044 0053 004d 004c ff5c` |
| special | **false** (a regular added token) |
| b64 | `772cRFNNTO+9nA==` |

## The other family (the legacy control tokens)

| id | token |
| --- | --- |
| 128806 | `<｜tool▁calls▁begin｜>` |
| 128807 | `<｜tool▁calls▁end｜>` |
| 128808 | `<｜tool▁call▁begin｜>` |
| 128809 | `<｜tool▁call▁end｜>` |
| 128814 | `<｜tool▁sep｜>` |
| 128840 | `<dsml:` |
| 128841 | `</dsml:` |

Note ids 128840/128841 — `<dsml:` / `</dsml:` — a SECOND markup family
(lowercase, colon-suffixed) the estate scanner does not yet consume. The
serving stack can plausibly degrade DSML into THAT family; the scanner should
treat `dsml:`-prefixed tags with the same shape tolerance.

## Tokenizer mechanics (why degradation happens)

- The BPE vocab holds `｜DSML｜` as ONE token, but the ENVELOPE tags
  (`<｜DSML｜tool_calls>` = `<` + token + `tool_calls` + `>`) are ordinary
  character sequences — a serving stack that re-chunks the byte stream can
  split/duplicate the `｜` bytes mid-tag without breaking the model's own
  tokenizer, but breaking every downstream exact-string matcher.
- Tokenizer config: `model.type = "BPE"`. The estate mirror of the tokenizer
  lets us pin the scanner against id 128825's bytes in tests — no doc quotes.

## Refresh

```sh
curl -sL https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731/resolve/main/tokenizer.json \
  -o /tmp/deepseek-tok/tokenizer.json
```
