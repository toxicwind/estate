# vansrouter-rtk-provenance-repair

[![for-the-badge](https://img.shields.io/badge/RTK-Provenance-FF6F61?style=for-the-badge)](https://open-sse.github.io/rtk) [![for-the-badge](https://img.shields.io/badge/Tool-Result-Probe-FFD700?style=for-the-badge)](https://github.com/tool-result) [![for-the-badge](https://img.shields.io/badge/ChatCore-JS-7FDBFF?style=for-the-badge)](https://github.com/open-sse/handlers)

## vansrouter-rtk-provenance-repair

Diagnose and durably repair VansRouter RTK tool-result interleaving without losing legitimate token savings.

### Diagnose

1. **Prove raw command/file bytes are correct** by persisting output and reading it independently
2. **Check whether model-bound tool results contain RTK-only phrases** such as `Staged:`, `Modified:`, or `files in … dirs`
3. **Map the phrase to `open-sse/rtk/autodetect.js`** and its filters
4. **Trace `open-sse/rtk/index.js::compressMessages()`** from `open-sse/handlers/chatCore.js`

### Root-cause invariant

RTK is intended to save context tokens, but content-only autodetection must never rewrite results from file-reading or other non-shell tools. Tool-result provenance must be recovered from the preceding tool call before selecting compression.

### Repair contract

- **Preserve RTK for genuine shell/exec results.**
- **Match filters against the invoked command/tool**, not arbitrary result appearance.
- **Never compress `read` or other structured/file-content results.**
- **Add regressions proving both non-corruption and retained compression savings.**
- **Run focused RTK tests**, then verify through the live VansRouter request path before declaring success.
- **Commit and push the source fix**; do not runtime-patch the installed package.

### Quick start (3 commands max)

```bash
# Diagnose RTK provenance interleaving
# 1. Persist output from a tool call
# 2. Check for RTK-only phrases: Staged:, Modified:, files in ... dirs
# 3. Map to open-sse/rtk/autodetect.js filters
# 4. Trace compressMessages() from chatCore.js

# Run the diagnostic script
python3 diagnose_rtk.py --result /path/to/tool_result.txt

# Verify repair contract
# 1. Confirm RTK preserved for shell results
# 2. Confirm no compression on read/structured results
# 3. Run: focused RTK tests
# 4. Verify through live VansRouter request path
```

### Architecture

The VansRouter RTK provenance repair addresses the interleaving of tool results with RTK (Reduce Token Kit) compression metadata. The root cause is that content-only autodetection can mistakenly rewrite RTK metadata when results appear to match RTK-only phrases, even when those results originated from file-reading or other non-shell tools.

The repair ensures:
- RTK is preserved for genuine shell/exec results
- Filters match against the invoked command/tool, not arbitrary result appearance
- `read` and other structured/file-content results are never compressed
- Regressions prove both non-corruption and retained compression savings

### Config / optional services

- `open-sse/rtk/autodetect.js` — filter patterns for RTK phrase matching
- `open-sse/handlers/chatCore.js` — contains `compressMessages()` function
- Tool result provenance from preceding tool call (must be recovered before compression)
- RTK test suite for regression verification

### Dev / contributing

- Add regressions proving both non-corruption and retained compression savings
- Test through the live VansRouter request path before declaring success
- Commit and push the source fix — do not runtime-patch the installed package
- Match filters against the invoked command/tool, not arbitrary result appearance
- Never compress `read` or other structured/file-content results

### License

Open Claw — see `skill.toml` for details.

### Security

- Never compress `read` or other structured/file-content results
- Match filters against the invoked command/tool, not arbitrary result appearance
- Preserve RTK for genuine shell/exec results only
- Commit and push the source fix; do not runtime-patch the installed package