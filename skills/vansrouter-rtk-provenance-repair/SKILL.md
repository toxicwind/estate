---
name: vansrouter-rtk-provenance-repair
description: Diagnose and durably repair VansRouter RTK tool-result interleaving without losing legitimate token savings.
---

# VansRouter RTK provenance repair

## Diagnose
1. Prove raw command/file bytes are correct by persisting output and reading it independently.
2. Check whether model-bound tool results contain RTK-only phrases such as `Staged:`, `Modified:`, or `files in … dirs`.
3. Map the phrase to `open-sse/rtk/autodetect.js` and its filters.
4. Trace `open-sse/rtk/index.js::compressMessages()` from `open-sse/handlers/chatCore.js`.

## Root-cause invariant
RTK is intended to save context tokens, but content-only autodetection must never rewrite results from file-reading or other non-shell tools. Tool-result provenance must be recovered from the preceding tool call before selecting compression.

## Repair contract
- Preserve RTK for genuine shell/exec results.
- Match filters against the invoked command/tool, not arbitrary result appearance.
- Never compress `read` or other structured/file-content results.
- Add regressions proving both non-corruption and retained compression savings.
- Run focused RTK tests, then verify through the live VansRouter request path before declaring success.
- Commit and push the source fix; do not runtime-patch the installed package.
