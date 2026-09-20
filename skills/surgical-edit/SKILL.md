---
name: "surgical_edit"
description: "Assertive surgical file editing: exact-text replacements with pre/post occurrence counts, every check before any write, abort on any mismatch. For config surgery (herd.yaml, model_constraints.yaml, etc.) where a wrong edit is worse than no edit. Born from the 2026-09-20 moonshot peer restore — the pattern that survived two scoping bugs because the asserts caught them."
---

# surgical-edit

Config surgery where a wrong edit is worse than no edit.

## The doctrine

1. **All checks before any write.** Count every `old` block's occurrences first. If any
   count mismatches its expectation, abort with zero bytes written.
2. **Exact text, never fuzzy.** Replacements are literal string operations — no regex,
   no "close enough". If the file drifted, the assert fails and you look, not the tool.
3. **Atomic writes.** Write to temp + rename. No half-written configs, ever.
4. **Byte-exact transit.** When the target file lives on yote and you are on the cell,
   transfer the patch spec (not the script) via base64 chunks — see TOOLS.md
   "Bridge exec: no large heredocs". The script itself lives in the repo; only the
   small JSON spec crosses the bridge.

## Components

- `bin/surgical-edit` — the editor. Takes a JSON patch spec:
  ```json
  {
    "file": "/home/toxic/sovereign/config/herd.yaml",
    "edits": [
      {"old": "  # --- moonshot: Moonshot AI direct (PARKED 2026-09-20) ---",
       "new": "  # --- moonshot: Moonshot AI direct (RESTORED 2026-09-20) ---",
       "expected": 1}
    ]
  }
  ```
  `surgical-edit patch.json` — apply. `surgical-edit --check patch.json` — verify only.
  Exit 0 on success; `ABORT: ...` on stderr + exit 1 with nothing written on mismatch.
- `bin/herd-probe` — exact-token probe through the herd router:
  `herd-probe moonshot/kimi-k2.6 "ABSTRACT-7X3Q"` — posts to
  `127.0.0.1:25100/v1/chat/completions` and checks the reply is verbatim.
  Prints `VERBATIM_EXACT` / `NONEXACT` / `HTTP <status>` + error body.
  A 429/402/404 body is evidence, not a verdict — read what it says.

## When to use

- Any edit to `config/herd.yaml`, `config/model_constraints.yaml`, or other
  hand-maintained router config: write the spec, `--check` it, then apply.
- Verifying a model route actually serves: `herd-probe` with the canary token.
- Do NOT use for bulk refactors or generated code — this is a scalpel, not a bulldozer.
  For AST-scale rewrites see `ast-migrate.ts`.

## Deep links

- Master README: `/home/toxic/sovereign/README.md`
- Herd config docs: `/home/toxic/sovereign/config/` (herd.yaml, model_constraints.yaml)
- Bridge transfer pattern: `~/TOOLS.md` ("Bridge exec: no large heredocs")
- Provenance: moonshot peer restore, 2026-09-20 (`projects/audits/moonshot-parked-audit-2026-09-20.md` §8)
